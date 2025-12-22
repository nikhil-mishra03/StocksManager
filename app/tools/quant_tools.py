from langchain.tools import tool
from app.service.instrument_service import get_all_instruments
from app.service.market_data import get_enriched_market_data, get_price_levels
from app.service.holding_service import get_holding_snapshot
from app.service.gtt_service import get_active_gtts_with_metrics, get_gtts_grouped_by_instrument
from fastapi.encoders import jsonable_encoder

@tool
def get_all_instruments_tool():
    """Get all instruments from the database"""
    try:
        instruments = get_all_instruments()
        return jsonable_encoder(instruments)
    except Exception as e:
        raise e
    

@tool
def get_gtts_grouped_by_instrument_tool():
    """Get all active GTT orders grouped by instrument"""
    try:
        gtts = get_gtts_grouped_by_instrument()
        return jsonable_encoder(gtts)
    except Exception as e:
        raise e
    
@tool
def get_active_gtts_with_metrics_tool():
    """Get all active GTT orders with computed metrics"""
    try:
        gtts = get_active_gtts_with_metrics()
        return jsonable_encoder(gtts)
    except Exception as e:
        raise e


@tool
def get_enriched_market_data_tool(instrument_token: int):
    """Get OHLCV data with computed technical indicators"""
    try:
        data = get_enriched_market_data(instrument_token)
        return jsonable_encoder(data)
    except Exception as e:
        raise e
    

@tool
def get_price_levels_tool(instrument_token: int):
    """Get key price levels for an instrument"""
    try:
        levels = get_price_levels(instrument_token)
        return jsonable_encoder(levels)
    except Exception as e:
        raise e

@tool
def get_holding_snapshot_tool():
    """Get current Holding Snapshot from the Broker"""
    try:
        data = get_holding_snapshot()
        return jsonable_encoder(data)
    except Exception as e:
        raise e
    

@tool
def get_instrument_indicators_tool(instrument_token: int):
    """
    Get technical indicators for an instrument.

    Returns a dict with:
    - latest_price: Current price
    - indicators: Object containing:
        - ema_9, ema_20, ema_50, ema_200: Exponential Moving Averages
        - rsi_14: Relative Strength Index (14-period)
        - macd_line, macd_signal, macd_histogram: MACD components
        - bb_upper, bb_middle, bb_lower: Bollinger Bands (20, 2σ)
        - atr_14: Average True Range (14-period)
    - price_levels: Support/resistance levels

    Use these indicators to assess:
    - Trend: EMA alignment (bullish if price > EMA9 > EMA20 > EMA50)
    - Momentum: MACD crossovers and histogram direction
    - Overbought/Oversold: RSI > 70 (overbought), RSI < 30 (oversold)
    - Volatility: ATR as % of price, Bollinger Band width
    - Entry zones: Price near lower BB or key EMA support
    """
    try:
        raw_data = get_enriched_market_data(instrument_token)
        market_data = {
            "latest_price": raw_data.latest_price,
            "indicators": jsonable_encoder(raw_data.indicators),
            "price_levels": jsonable_encoder(raw_data.price_levels)
        }
        return market_data
    except Exception as e:
        raise e
