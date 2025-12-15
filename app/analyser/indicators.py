"""
Technical Indicators Module.

Provides pure functions for computing common technical indicators
from OHLCV data. All functions are broker-agnostic and operate
on simple lists of price data.

Design principles:
- Pure functions: no side effects, no DB access
- Return NaN for insufficient data points (not exceptions)
- All functions return lists matching input length
"""

import math


def sma(prices: list[float], period: int) -> list[float]:
    """
    Compute Simple Moving Average (SMA).

    Args:
        prices: List of prices (typically close prices).
        period: Number of periods for the moving average.

    Returns:
        List of SMA values. First (period-1) values will be NaN.
    """
    if period < 1 or len(prices) < period:
        return [float("nan")] * len(prices)

    result: list[float] = [float("nan")] * (period - 1)
    window_sum = sum(prices[:period])
    result.append(window_sum / period)

    for i in range(period, len(prices)):
        window_sum += prices[i] - prices[i - period]
        result.append(window_sum / period)

    return result


def ema(prices: list[float], period: int) -> list[float]:
    """
    Compute Exponential Moving Average (EMA).

    Uses multiplier = 2 / (period + 1). First EMA is seeded with SMA.

    Args:
        prices: List of prices (typically close prices).
        period: Number of periods for the EMA.

    Returns:
        List of EMA values. First (period-1) values will be NaN.
    """
    if period < 1 or len(prices) < period:
        return [float("nan")] * len(prices)

    result: list[float] = [float("nan")] * (period - 1)
    multiplier = 2 / (period + 1)

    # Seed with SMA of first `period` prices
    sma_seed = sum(prices[:period]) / period
    result.append(sma_seed)

    # Calculate EMA for remaining prices
    for i in range(period, len(prices)):
        ema_val = (prices[i] - result[-1]) * multiplier + result[-1]
        result.append(ema_val)

    return result


def rsi(prices: list[float], period: int = 14) -> list[float]:
    """
    Compute Relative Strength Index (RSI).

    Uses Wilder's smoothing method.

    Args:
        prices: List of prices (typically close prices).
        period: Number of periods for RSI (default: 14).

    Returns:
        List of RSI values (0-100 scale). First `period` values will be NaN.
    """
    if period < 1 or len(prices) < period + 1:
        return [float("nan")] * len(prices)

    result: list[float] = [float("nan")] * period

    # Calculate price changes
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        gains.append(delta if delta > 0 else 0)
        losses.append(-delta if delta < 0 else 0)

    # First average gain/loss (SMA)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Calculate first RSI
    if avg_loss == 0:
        result.append(100.0)
    else:
        rs = avg_gain / avg_loss
        result.append(100 - (100 / (1 + rs)))

    # Calculate remaining RSI values using Wilder's smoothing
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))

    return result


def macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> dict[str, list[float]]:
    """
    Compute Moving Average Convergence Divergence (MACD).

    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal_period)
    Histogram = MACD Line - Signal Line

    Args:
        prices: List of prices (typically close prices).
        fast_period: Fast EMA period (default: 12).
        slow_period: Slow EMA period (default: 26).
        signal_period: Signal line EMA period (default: 9).

    Returns:
        Dict with 'macd', 'signal', and 'histogram' lists.
    """
    n = len(prices)
    nan_result = {
        "macd": [float("nan")] * n,
        "signal": [float("nan")] * n,
        "histogram": [float("nan")] * n,
    }

    if fast_period >= slow_period or n < slow_period:
        return nan_result

    ema_fast = ema(prices, fast_period)
    ema_slow = ema(prices, slow_period)

    # MACD line
    macd_line: list[float] = []
    for f, s in zip(ema_fast, ema_slow):
        if math.isnan(f) or math.isnan(s):
            macd_line.append(float("nan"))
        else:
            macd_line.append(f - s)

    # Signal line: EMA of valid MACD values
    valid_macd = [m for m in macd_line if not math.isnan(m)]
    if len(valid_macd) < signal_period:
        return {
            "macd": macd_line,
            "signal": [float("nan")] * n,
            "histogram": [float("nan")] * n,
        }

    signal_values = ema(valid_macd, signal_period)
    nan_count = n - len(valid_macd)
    signal_line = [float("nan")] * nan_count + signal_values

    # Histogram
    histogram: list[float] = []
    for m, s in zip(macd_line, signal_line):
        if math.isnan(m) or math.isnan(s):
            histogram.append(float("nan"))
        else:
            histogram.append(m - s)

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}



def bollinger_bands(
    prices: list[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> dict[str, list[float]]:
    """
    Compute Bollinger Bands.

    Middle Band = SMA(period)
    Upper Band = Middle + (std_dev * standard deviation)
    Lower Band = Middle - (std_dev * standard deviation)

    Args:
        prices: List of prices (typically close prices).
        period: Number of periods for SMA and std dev (default: 20).
        std_dev: Number of standard deviations (default: 2.0).

    Returns:
        Dict with 'upper', 'middle', 'lower' band lists.
    """
    n = len(prices)
    nan_result = {
        "upper": [float("nan")] * n,
        "middle": [float("nan")] * n,
        "lower": [float("nan")] * n,
    }

    if period < 1 or n < period:
        return nan_result

    middle: list[float] = [float("nan")] * (period - 1)
    upper: list[float] = [float("nan")] * (period - 1)
    lower: list[float] = [float("nan")] * (period - 1)

    for i in range(period - 1, n):
        window = prices[i - period + 1 : i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)

        middle.append(mean)
        upper.append(mean + std_dev * std)
        lower.append(mean - std_dev * std)

    return {"upper": upper, "middle": middle, "lower": lower}


def atr(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float]:
    """
    Compute Average True Range (ATR).

    True Range = max(high - low, |high - prev_close|, |low - prev_close|)
    ATR = Smoothed average of True Range (Wilder's method)

    Args:
        highs: List of high prices.
        lows: List of low prices.
        closes: List of close prices.
        period: Number of periods for ATR (default: 14).

    Returns:
        List of ATR values. First `period` values will be NaN.
    """
    n = len(highs)
    if not (n == len(lows) == len(closes)):
        return [float("nan")] * n
    if n < period + 1:
        return [float("nan")] * n

    # Calculate True Range
    tr: list[float] = [highs[0] - lows[0]]  # First TR is just high - low
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr.append(max(hl, hc, lc))

    # First ATR is SMA of first `period` TR values
    result: list[float] = [float("nan")] * period
    first_atr = sum(tr[1 : period + 1]) / period
    result.append(first_atr)

    # Subsequent ATR values use Wilder's smoothing
    for i in range(period + 1, n):
        atr_val = (result[-1] * (period - 1) + tr[i]) / period
        result.append(atr_val)

    return result

