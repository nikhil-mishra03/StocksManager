"""
Market Data Service Module.

Provides functions to query historical OHLCV data and compute technical indicators.
Broker-agnostic: only depends on the database.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math

from app.store.models import HistoricalData, Instrument
from app.store.db import SessionLocal
from app.core.logger_config import get_logger
from app.analyser.indicators import ema, rsi, macd, bollinger_bands, atr
from langchain.tools import tool

logger = get_logger(__name__)


@dataclass
class OHLCV:
    """Single OHLCV candle."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class IndicatorValues:
    """Computed indicator values at current point."""

    ema_9: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    rsi_14: float | None = None
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    atr_14: float | None = None


@dataclass
class PriceLevels:
    """
    Key price levels for support/resistance context.

    Used by the agent to assess GTT trigger price validity.
    """

    # 52-week context
    high_52w: float | None = None
    low_52w: float | None = None
    pct_from_52w_high: float | None = None  # Negative = below high
    pct_from_52w_low: float | None = None   # Positive = above low

    # 20-day context (short-term)
    high_20d: float | None = None
    low_20d: float | None = None

    # Recent swing points (percentage-based detection)
    recent_swing_high: float | None = None
    recent_swing_high_date: datetime | None = None
    recent_swing_low: float | None = None
    recent_swing_low_date: datetime | None = None

    # Psychological levels (round numbers)
    nearest_round_above: float | None = None
    nearest_round_below: float | None = None

    # Normalized volatility
    atr_percent: float | None = None  # ATR as % of current price


@dataclass
class EnrichedMarketData:
    """OHLCV data enriched with technical indicators and price levels."""

    instrument_token: int
    symbol: str | None
    exchange: str | None
    candles: list[OHLCV]
    latest_price: float | None
    indicators: IndicatorValues
    price_levels: PriceLevels
    # Full indicator series (for charting or detailed analysis)
    indicator_series: dict[str, list[float]] = field(default_factory=dict)


def get_historical_data(
    instrument_token: int,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int | None = None,
) -> list[HistoricalData]:
    """
    Get raw historical OHLCV data for an instrument.

    Args:
        instrument_token: The instrument token.
        from_time: Start time filter (optional).
        to_time: End time filter (optional).
        limit: Maximum number of records to return (optional).

    Returns:
        List of HistoricalData records ordered by timestamp ascending.
    """
    with SessionLocal() as session:
        query = (
            session.query(HistoricalData)
            .filter(HistoricalData.instrument_token == instrument_token)
        )

        if from_time:
            query = query.filter(HistoricalData.timestamp >= from_time)
        if to_time:
            query = query.filter(HistoricalData.timestamp <= to_time)

        query = query.order_by(HistoricalData.timestamp.asc())

        if limit:
            query = query.limit(limit)

        return query.all()


def get_latest_price(instrument_token: int) -> float | None:
    """
    Get the latest close price for an instrument.

    Args:
        instrument_token: The instrument token.

    Returns:
        Latest close price, or None if no data available.
    """
    with SessionLocal() as session:
        latest = (
            session.query(HistoricalData)
            .filter_by(instrument_token=instrument_token)
            .order_by(HistoricalData.timestamp.desc())
            .first()
        )
        return latest.close if latest else None

# @tool
def get_enriched_market_data(
    instrument_token: int,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    include_series: bool = False,
) -> EnrichedMarketData:
    """
    Get OHLCV data with computed technical indicators.

    Computes:
    - EMA (9, 20, 50, 200)
    - RSI (14)
    - MACD (12, 26, 9)
    - Bollinger Bands (20, 2)
    - ATR (14)

    Args:
        instrument_token: The instrument token.
        from_time: Start time filter (optional).
        to_time: End time filter (optional).
        include_series: If True, include full indicator series in response.

    Returns:
        EnrichedMarketData with candles and indicator values.
    """
    with SessionLocal() as session:
        # Get instrument info
        instrument = (
            session.query(Instrument).filter_by(token=instrument_token).first()
        )
        symbol = instrument.symbol if instrument else None
        exchange = instrument.exchange if instrument else None

        # Get historical data
        query = (
            session.query(HistoricalData)
            .filter(HistoricalData.instrument_token == instrument_token)
        )

        if from_time:
            query = query.filter(HistoricalData.timestamp >= from_time)
        if to_time:
            query = query.filter(HistoricalData.timestamp <= to_time)

        records = query.order_by(HistoricalData.timestamp.asc()).all()

        # Convert to OHLCV objects
        candles = [
            OHLCV(
                timestamp=r.timestamp,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume,
            )
            for r in records
        ]

        # Extract price arrays for indicator calculation
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        # Compute indicators
        indicators = IndicatorValues()
        indicator_series: dict[str, list[float]] = {}

        if closes:
            # EMAs
            ema_9_series = ema(closes, 9)
            ema_20_series = ema(closes, 20)
            ema_50_series = ema(closes, 50)
            ema_200_series = ema(closes, 200)

            indicators.ema_9 = _last_valid(ema_9_series)
            indicators.ema_20 = _last_valid(ema_20_series)
            indicators.ema_50 = _last_valid(ema_50_series)
            indicators.ema_200 = _last_valid(ema_200_series)

            # RSI
            rsi_14_series = rsi(closes, 14)
            indicators.rsi_14 = _last_valid(rsi_14_series)

            # MACD
            macd_result = macd(closes, 12, 26, 9)
            indicators.macd_line = _last_valid(macd_result["macd"])
            indicators.macd_signal = _last_valid(macd_result["signal"])
            indicators.macd_histogram = _last_valid(macd_result["histogram"])

            # Bollinger Bands
            bb_result = bollinger_bands(closes, 20, 2.0)
            indicators.bb_upper = _last_valid(bb_result["upper"])
            indicators.bb_middle = _last_valid(bb_result["middle"])
            indicators.bb_lower = _last_valid(bb_result["lower"])

            # ATR
            atr_14_series = atr(highs, lows, closes, 14)
            indicators.atr_14 = _last_valid(atr_14_series)

            if include_series:
                indicator_series = {
                    "ema_9": ema_9_series,
                    "ema_20": ema_20_series,
                    "ema_50": ema_50_series,
                    "ema_200": ema_200_series,
                    "rsi_14": rsi_14_series,
                    "macd": macd_result["macd"],
                    "macd_signal": macd_result["signal"],
                    "macd_histogram": macd_result["histogram"],
                    "bb_upper": bb_result["upper"],
                    "bb_middle": bb_result["middle"],
                    "bb_lower": bb_result["lower"],
                    "atr_14": atr_14_series,
                }

        # Compute price levels
        price_levels = _compute_price_levels_from_candles(
            candles=candles,
            current_price=closes[-1] if closes else None,
            atr_value=indicators.atr_14,
        )

        return EnrichedMarketData(
            instrument_token=instrument_token,
            symbol=symbol,
            exchange=exchange,
            candles=candles,
            latest_price=closes[-1] if closes else None,
            indicators=indicators,
            price_levels=price_levels,
            indicator_series=indicator_series,
        )


def _last_valid(values: list[float]) -> float | None:
    """Get the last non-NaN value from a list."""
    for v in reversed(values):
        if not math.isnan(v):
            return v
    return None


def _compute_price_levels_from_candles(
    candles: list[OHLCV],
    current_price: float | None,
    atr_value: float | None,
    swing_threshold_pct: float = 0.03,
) -> PriceLevels:
    """
    Compute price levels from a list of candles.

    Internal helper used by get_enriched_market_data.
    """
    if not candles or current_price is None:
        return PriceLevels()

    # Determine how much data we have
    num_candles = len(candles)

    # 52-week high/low (use all available data, ideally 252 trading days)
    high_52w = max(c.high for c in candles)
    low_52w = min(c.low for c in candles)
    pct_from_52w_high = ((current_price - high_52w) / high_52w) * 100
    pct_from_52w_low = ((current_price - low_52w) / low_52w) * 100

    # 20-day high/low
    candles_20d = candles[-20:] if num_candles >= 20 else candles
    high_20d = max(c.high for c in candles_20d)
    low_20d = min(c.low for c in candles_20d)

    # Swing highs/lows
    swing_highs = _find_swing_highs(candles, swing_threshold_pct)
    swing_lows = _find_swing_lows(candles, swing_threshold_pct)

    recent_swing_high = swing_highs[0][1] if swing_highs else None
    recent_swing_high_date = swing_highs[0][0] if swing_highs else None
    recent_swing_low = swing_lows[0][1] if swing_lows else None
    recent_swing_low_date = swing_lows[0][0] if swing_lows else None

    # Round number levels
    nearest_round_above, nearest_round_below = _get_round_number_levels(current_price)

    # ATR as % of price
    atr_percent = (atr_value / current_price) * 100 if atr_value else None

    return PriceLevels(
        high_52w=high_52w,
        low_52w=low_52w,
        pct_from_52w_high=pct_from_52w_high,
        pct_from_52w_low=pct_from_52w_low,
        high_20d=high_20d,
        low_20d=low_20d,
        recent_swing_high=recent_swing_high,
        recent_swing_high_date=recent_swing_high_date,
        recent_swing_low=recent_swing_low,
        recent_swing_low_date=recent_swing_low_date,
        nearest_round_above=nearest_round_above,
        nearest_round_below=nearest_round_below,
        atr_percent=atr_percent,
    )


def _find_swing_highs(
    candles: list[OHLCV], threshold_pct: float = 0.03
) -> list[tuple[datetime, float]]:
    """
    Find swing highs using percentage-based detection.

    A swing high is a point from which price dropped at least threshold_pct.

    Args:
        candles: List of OHLCV candles (oldest first).
        threshold_pct: Minimum drop from high to qualify as swing (default 3%).

    Returns:
        List of (timestamp, price) tuples for swing highs, most recent first.
    """
    if len(candles) < 2:
        return []

    swing_highs: list[tuple[datetime, float]] = []

    # Track the highest point and whether we've seen a significant drop
    current_high = candles[0].high
    current_high_date = candles[0].timestamp

    for candle in candles[1:]:
        # Check if we've dropped enough from the current high
        drop_pct = (current_high - candle.low) / current_high

        if drop_pct >= threshold_pct:
            # This is a valid swing high
            swing_highs.append((current_high_date, current_high))
            # Reset: start tracking from this candle
            current_high = candle.high
            current_high_date = candle.timestamp
        elif candle.high > current_high:
            # New high, update tracking
            current_high = candle.high
            current_high_date = candle.timestamp

    # Return most recent first
    return list(reversed(swing_highs))


def _find_swing_lows(
    candles: list[OHLCV], threshold_pct: float = 0.03
) -> list[tuple[datetime, float]]:
    """
    Find swing lows using percentage-based detection.

    A swing low is a point from which price rose at least threshold_pct.

    Args:
        candles: List of OHLCV candles (oldest first).
        threshold_pct: Minimum rise from low to qualify as swing (default 3%).

    Returns:
        List of (timestamp, price) tuples for swing lows, most recent first.
    """
    if len(candles) < 2:
        return []

    swing_lows: list[tuple[datetime, float]] = []

    # Track the lowest point and whether we've seen a significant rise
    current_low = candles[0].low
    current_low_date = candles[0].timestamp

    for candle in candles[1:]:
        # Check if we've risen enough from the current low
        rise_pct = (candle.high - current_low) / current_low

        if rise_pct >= threshold_pct:
            # This is a valid swing low
            swing_lows.append((current_low_date, current_low))
            # Reset: start tracking from this candle
            current_low = candle.low
            current_low_date = candle.timestamp
        elif candle.low < current_low:
            # New low, update tracking
            current_low = candle.low
            current_low_date = candle.timestamp

    # Return most recent first
    return list(reversed(swing_lows))


def _get_round_number_levels(price: float) -> tuple[float | None, float | None]:
    """
    Get the nearest psychological (round number) levels above and below price.

    Uses adaptive rounding based on price magnitude:
    - Price < 100: round to nearest 10
    - Price 100-1000: round to nearest 50
    - Price 1000-10000: round to nearest 100
    - Price > 10000: round to nearest 500

    Args:
        price: Current price.

    Returns:
        Tuple of (nearest_round_above, nearest_round_below).
    """
    if price <= 0:
        return None, None

    # Determine rounding magnitude based on price
    if price < 100:
        step = 10
    elif price < 1000:
        step = 50
    elif price < 10000:
        step = 100
    else:
        step = 500

    round_below = (price // step) * step
    round_above = round_below + step

    # If price is exactly on a round number, adjust
    if price == round_below:
        round_above = price
        round_below = price - step

    return round_above, round_below

# @tool
def get_price_levels(
    instrument_token: int,
    swing_threshold_pct: float = 0.03,
) -> PriceLevels:
    """
    Compute key price levels for an instrument.

    Includes:
    - 52-week high/low with % distance
    - 20-day high/low
    - Recent swing high/low (percentage-based detection)
    - Nearest round number levels
    - ATR as % of price

    Args:
        instrument_token: The instrument token.
        swing_threshold_pct: Threshold for swing detection (default 3%).

    Returns:
        PriceLevels dataclass with all computed levels.
    """
    with SessionLocal() as session:
        now = datetime.now()

        # Get 52-week data
        one_year_ago = now - timedelta(days=365)
        records_52w = (
            session.query(HistoricalData)
            .filter(HistoricalData.instrument_token == instrument_token)
            .filter(HistoricalData.timestamp >= one_year_ago)
            .order_by(HistoricalData.timestamp.asc())
            .all()
        )

        if not records_52w:
            return PriceLevels()

        # Convert to OHLCV
        candles_52w = [
            OHLCV(
                timestamp=r.timestamp,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume,
            )
            for r in records_52w
        ]

        # Current price (latest close)
        current_price = candles_52w[-1].close

        # 52-week high/low
        high_52w = max(c.high for c in candles_52w)
        low_52w = min(c.low for c in candles_52w)
        pct_from_52w_high = ((current_price - high_52w) / high_52w) * 100
        pct_from_52w_low = ((current_price - low_52w) / low_52w) * 100

        # 20-day high/low
        candles_20d = candles_52w[-20:] if len(candles_52w) >= 20 else candles_52w
        high_20d = max(c.high for c in candles_20d)
        low_20d = min(c.low for c in candles_20d)

        # Swing highs/lows
        swing_highs = _find_swing_highs(candles_52w, swing_threshold_pct)
        swing_lows = _find_swing_lows(candles_52w, swing_threshold_pct)

        recent_swing_high = swing_highs[0][1] if swing_highs else None
        recent_swing_high_date = swing_highs[0][0] if swing_highs else None
        recent_swing_low = swing_lows[0][1] if swing_lows else None
        recent_swing_low_date = swing_lows[0][0] if swing_lows else None

        # Round number levels
        nearest_round_above, nearest_round_below = _get_round_number_levels(current_price)

        # ATR as % of price
        highs = [c.high for c in candles_52w]
        lows = [c.low for c in candles_52w]
        closes = [c.close for c in candles_52w]
        atr_series = atr(highs, lows, closes, 14)
        atr_value = _last_valid(atr_series)
        atr_percent = (atr_value / current_price) * 100 if atr_value else None

        return PriceLevels(
            high_52w=high_52w,
            low_52w=low_52w,
            pct_from_52w_high=pct_from_52w_high,
            pct_from_52w_low=pct_from_52w_low,
            high_20d=high_20d,
            low_20d=low_20d,
            recent_swing_high=recent_swing_high,
            recent_swing_high_date=recent_swing_high_date,
            recent_swing_low=recent_swing_low,
            recent_swing_low_date=recent_swing_low_date,
            nearest_round_above=nearest_round_above,
            nearest_round_below=nearest_round_below,
            atr_percent=atr_percent,
        )
