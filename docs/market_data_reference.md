# Market Data Service Reference

This document explains all data returned by `market_data.py` and how the quant agent uses it for GTT management decisions.

---

## Table of Contents

1. [Basic Price Data (OHLCV)](#1-basic-price-data-ohlcv)
2. [Trend Indicators](#2-trend-indicators)
   - [EMAs](#emas-exponential-moving-averages)
   - [RSI](#rsi-relative-strength-index)
   - [MACD](#macd-moving-average-convergence-divergence)
   - [Bollinger Bands](#bollinger-bands)
   - [ATR](#atr-average-true-range)
3. [Price Levels](#3-price-levels)
   - [52-Week Context](#52-week-context)
   - [20-Day Context](#20-day-context)
   - [Swing Highs/Lows](#swing-highslows)
   - [Round Number Levels](#round-number-levels)
   - [ATR Percent](#atr-percent)
4. [Data Structure Overview](#4-data-structure-overview)
5. [Agent Decision Examples](#5-agent-decision-examples)

---

## 1. Basic Price Data (OHLCV)

Each candle contains:

```python
@dataclass
class OHLCV:
    timestamp: datetime  # When this candle occurred
    open: float          # First trade price in the period
    high: float          # Highest price in the period
    low: float           # Lowest price in the period
    close: float         # Last trade price in the period
    volume: int          # Number of shares traded
```

### Field Meanings

| Field | What It Tells You |
|-------|-------------------|
| `open` | Where price started — gap up/down from previous close shows overnight sentiment |
| `high` | Maximum buying pressure — where bulls ran out of steam |
| `low` | Maximum selling pressure — where bears ran out of steam |
| `close` | Where the "battle" ended — most important price (used for most indicators) |
| `volume` | Conviction — high volume = strong move, low volume = weak/unreliable move |

---

## 2. Trend Indicators

### EMAs (Exponential Moving Averages)

```python
ema_9: float   # Fast — reacts quickly (short-term trend)
ema_20: float  # Medium — standard swing trading reference
ema_50: float  # Slow — intermediate trend
ema_200: float # Very slow — long-term trend (institutional reference)
```

| Indicator | What It Tells The Agent |
|-----------|-------------------------|
| `ema_9` | Very short-term momentum. Day traders use this. |
| `ema_20` | **Key level** — many algorithms use this. Price below = short-term bearish. |
| `ema_50` | Intermediate trend. Hedge funds often use this. |
| `ema_200` | **The big one** — price above 200 EMA = bullish, below = bearish. |

#### Agent Usage

| Scenario | Interpretation | GTT Action |
|----------|----------------|------------|
| Price > all EMAs | Strong uptrend | Raise sell GTT triggers |
| Price < all EMAs | Strong downtrend | Lower buy GTT triggers |
| EMAs converging | Consolidation, expect breakout | Widen GTT range |
| Price crosses above EMA 200 | Major trend change to bullish | Review all bearish GTTs |

---

### RSI (Relative Strength Index)

```python
rsi_14: float  # 0-100 scale
```

| RSI Value | What It Means |
|-----------|---------------|
| > 70 | **Overbought** — stock may be stretched, pullback likely |
| 50-70 | Bullish momentum |
| 30-50 | Bearish momentum |
| < 30 | **Oversold** — stock may be beaten down, bounce likely |

#### Agent Usage

| Scenario | Interpretation | GTT Action |
|----------|----------------|------------|
| RSI > 80 | Extremely overbought | Sell GTT targets may be unrealistic |
| RSI < 25 | Extremely oversold | Good accumulation zone for buy GTT |
| RSI divergence | Warning sign | Tighten stops |

---

### MACD (Moving Average Convergence Divergence)

```python
macd_line: float       # Fast EMA - Slow EMA (momentum)
macd_signal: float     # EMA of MACD line (trigger)
macd_histogram: float  # MACD - Signal (momentum of momentum)
```

| Signal | What It Means |
|--------|---------------|
| `macd_line > 0` | Bullish momentum (fast EMA above slow) |
| `macd_line < 0` | Bearish momentum |
| `histogram > 0 and growing` | Momentum accelerating up |
| `histogram < 0 and shrinking` | Momentum accelerating down |
| MACD crosses above signal | **BUY signal** |
| MACD crosses below signal | **SELL signal** |

#### Agent Usage

| Scenario | Interpretation | GTT Action |
|----------|----------------|------------|
| Histogram shrinking from positive | Momentum fading | Tighten sell GTT |
| MACD crossing up from below zero | New uptrend starting | Raise buy GTT triggers |
| MACD negative and falling | Strong downtrend | Lower stop-loss GTTs |

---

### Bollinger Bands

```python
bb_upper: float   # Upper band (2 std dev above middle)
bb_middle: float  # 20-period SMA
bb_lower: float   # Lower band (2 std dev below middle)
```

| Situation | What It Means |
|-----------|---------------|
| Price touches `bb_upper` | Stock at upper extreme — may reverse down |
| Price touches `bb_lower` | Stock at lower extreme — may reverse up |
| Bands **squeezing** (narrow) | Low volatility — big move coming |
| Bands **expanding** (wide) | High volatility — trend in progress |

#### Agent Usage

| Scenario | Interpretation | GTT Action |
|----------|----------------|------------|
| Price at `bb_lower` | Support zone | Good level for buy GTT |
| Price at `bb_upper` | Resistance zone | Reasonable sell target |
| Bands very narrow | Expect breakout | Don't set tight GTTs |

---

### ATR (Average True Range)

```python
atr_14: float  # Average daily price range over 14 days
```

**This is THE KEY indicator for GTT placement.**

| ATR | What It Means |
|-----|---------------|
| High ATR | Stock moves a lot daily — volatile |
| Low ATR | Stock moves little daily — calm |

#### Agent Usage (Critical for Stop Placement)

| Stop Distance | Interpretation |
|---------------|----------------|
| < 1x ATR | **Too tight** — will get stopped by normal noise |
| 1.5-2x ATR | Reasonable for active trading |
| 2-3x ATR | Standard swing trade stop |
| > 3x ATR | Very wide — safe but gives up profit |

**Example**: ATR = ₹15 means stock moves ₹15/day on average.
- Stop-loss 1x ATR (₹15) away = 50% chance of hitting daily
- Stop-loss 2x ATR (₹30) away = Much safer

---

## 3. Price Levels

### 52-Week Context

```python
high_52w: float           # Highest price in 52 weeks
low_52w: float            # Lowest price in 52 weeks
pct_from_52w_high: float  # e.g., -15% means 15% below yearly high
pct_from_52w_low: float   # e.g., +40% means 40% above yearly low
```

| Data | What It Tells The Agent |
|------|-------------------------|
| `pct_from_52w_high = -5%` | Near highs — strong stock, breakout potential |
| `pct_from_52w_high = -40%` | Deep correction — either value or falling knife |
| `pct_from_52w_low = +10%` | Near lows — weak or bottoming |
| `pct_from_52w_low = +100%` | Doubled from lows — very strong momentum |

#### Agent Usage

| Scenario | GTT Action |
|----------|------------|
| Sell GTT trigger above 52w high | Flag as "Unrealistic target" |
| Buy GTT trigger below 52w low | Flag as "Very aggressive, might miss opportunity" |
| Price within 5% of 52w high | Strong stock, consider trailing stops |

---

### 20-Day Context

```python
high_20d: float  # Highest price in last 20 days
low_20d: float   # Lowest price in last 20 days
```

| Data | What It Tells The Agent |
|------|-------------------------|
| Price = `high_20d` | Short-term breakout, momentum is strong |
| Price = `low_20d` | Short-term breakdown, weakness |

#### Agent Usage

| Scenario | GTT Action |
|----------|------------|
| Current price = 20d high | Stock is strong, don't lower sell GTT |
| Current price = 20d low | Stock is weak, consider lowering buy GTT |

---

### Swing Highs/Lows

```python
recent_swing_high: float        # Last resistance level
recent_swing_high_date: datetime
recent_swing_low: float         # Last support level
recent_swing_low_date: datetime
```

**These are the REAL support/resistance levels** — where price actually reversed.

A **swing high** is detected when price drops at least 3% from a peak.
A **swing low** is detected when price rises at least 3% from a trough.

| Data | What It Tells The Agent |
|------|-------------------------|
| `recent_swing_high` | Resistance — price struggled here before |
| `recent_swing_low` | Support — buyers stepped in here before |

#### Agent Usage

| Scenario | GTT Action |
|----------|------------|
| Sell GTT at/below swing high | Reasonable profit target |
| Stop-loss GTT below swing low | Logical stop placement |
| Buy GTT near swing low | Good accumulation zone |
| Price breaks above swing high | Bullish breakout, raise targets |

---

### Round Number Levels

```python
nearest_round_above: float  # e.g., ₹1000 when price is ₹985
nearest_round_below: float  # e.g., ₹950 when price is ₹985
```

**Psychological levels** — traders cluster orders at round numbers.

Rounding logic adapts to price:
- Price < ₹100: round to nearest 10
- Price ₹100-1000: round to nearest 50
- Price ₹1000-10000: round to nearest 100
- Price > ₹10000: round to nearest 500

#### Agent Usage

| Scenario | GTT Action |
|----------|------------|
| GTT trigger at ₹999 | Suggest adjusting to ₹1000 (more liquidity) |
| Stop at exactly ₹500 | Common level, might get "stop hunted", consider ₹495 or ₹505 |
| Price just below round number | Expect resistance (profit-taking) |

---

### ATR Percent

```python
atr_percent: float  # ATR as % of current price
```

**Normalized volatility** — makes ATR comparable across different price stocks.

| ATR % | Volatility Level | Example |
|-------|------------------|---------|
| < 1% | Very calm | Blue-chip, large-cap |
| 1-2% | Low to moderate | Most stocks |
| 2-3% | Moderate | Growth stocks |
| 3-5% | High | Small-caps, momentum stocks |
| > 5% | Very high | Speculative, penny stocks |

#### Agent Usage

| Stop Distance vs ATR% | Interpretation |
|-----------------------|----------------|
| Stop 2% away, ATR% = 4% | Stop is 0.5x ATR — **TOO TIGHT!** |
| Stop 6% away, ATR% = 2% | Stop is 3x ATR — reasonable |
| Stop 10% away, ATR% = 2% | Stop is 5x ATR — very safe but gives up profit |

---

## 4. Data Structure Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EnrichedMarketData                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  IDENTITY                                                           │
│  ├── instrument_token: 12345                                        │
│  ├── symbol: "RELIANCE"                                             │
│  └── exchange: "NSE"                                                │
│                                                                     │
│  CURRENT STATE                                                      │
│  └── latest_price: ₹2,450                                           │
│                                                                     │
│  TREND (IndicatorValues)                                            │
│  ├── EMA 9:   ₹2,445  ─┐                                            │
│  ├── EMA 20:  ₹2,430   │  All below price = BULLISH                 │
│  ├── EMA 50:  ₹2,380   │                                            │
│  └── EMA 200: ₹2,200  ─┘                                            │
│                                                                     │
│  MOMENTUM                                                           │
│  ├── RSI: 65 (bullish, not overbought)                              │
│  ├── MACD: +12 (bullish)                                            │
│  └── MACD Histogram: +3 (accelerating)                              │
│                                                                     │
│  VOLATILITY                                                         │
│  ├── ATR: ₹45                                                       │
│  ├── ATR %: 1.8% (moderate)                                         │
│  ├── BB Upper: ₹2,520                                               │
│  └── BB Lower: ₹2,340                                               │
│                                                                     │
│  KEY LEVELS (PriceLevels)                                           │
│  ├── 52w High: ₹2,600 (-5.8% away)                                  │
│  ├── 52w Low:  ₹1,900 (+29% above)                                  │
│  ├── Swing High: ₹2,500 (resistance)                                │
│  ├── Swing Low:  ₹2,300 (support)                                   │
│  ├── Round Above: ₹2,500                                            │
│  └── Round Below: ₹2,400                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Agent Decision Examples

### Example 1: Evaluating a Sell GTT

**Situation**: Sell GTT at ₹2,600, current price ₹2,450

| Check | Data Used | Result |
|-------|-----------|--------|
| Is target realistic? | `high_52w = ₹2,600` | At 52w high, hard to break |
| Is stock trending up? | All EMAs below price | ✅ Yes, bullish |
| Is momentum strong? | RSI 65, MACD positive | ✅ Yes |
| How far is target? | (2600-2450)/2450 = 6.1% | 6.1% away |
| Is 6.1% reasonable? | ATR% = 1.8%, so 3.4x ATR | Reasonable |
| Any resistance before? | `swing_high = ₹2,500` | ⚠️ Resistance at ₹2,500 |

**Agent Conclusion**: "Target at ₹2,600 is at 52-week high with resistance at ₹2,500. Consider partial profit at ₹2,500 or wait for breakout."

---

### Example 2: Evaluating a Stop-Loss GTT

**Situation**: Stop-loss at ₹2,400, current price ₹2,450

| Check | Data Used | Result |
|-------|-----------|--------|
| How far is stop? | (2450-2400)/2450 = 2% | 2% away |
| Is this enough room? | ATR% = 1.8% | Stop is 1.1x ATR — **tight!** |
| Is there support? | `swing_low = ₹2,300` | Support at ₹2,300 |
| Round number? | `nearest_round_below = ₹2,400` | ⚠️ Stop at round number |

**Agent Conclusion**: "Stop at ₹2,400 is only 1.1x ATR (too tight) and at a round number (stop-hunt risk). Suggest ₹2,350 (2x ATR) or ₹2,295 (just below swing low)."

---

### Example 3: Evaluating a Buy GTT

**Situation**: Buy GTT at ₹2,200, current price ₹2,450

| Check | Data Used | Result |
|-------|-----------|--------|
| How far is trigger? | (2450-2200)/2450 = 10.2% | 10.2% below current |
| Is there support? | `swing_low = ₹2,300` | ⚠️ Support at ₹2,300 |
| Is stock weak? | RSI 65, above all EMAs | ❌ No, stock is strong |
| 52w context? | `low_52w = ₹1,900` | Buy trigger well above 52w low |

**Agent Conclusion**: "Buy GTT at ₹2,200 may never trigger — stock is strong (RSI 65, above all EMAs) with support at ₹2,300. Consider raising trigger to ₹2,280-₹2,300 range."

---

## Quick Reference Card

### Trend Assessment
```
BULLISH:  Price > EMA9 > EMA20 > EMA50 > EMA200
BEARISH:  Price < EMA9 < EMA20 < EMA50 < EMA200
NEUTRAL:  EMAs intertwined / no clear order
```

### Momentum Assessment
```
STRONG UP:    RSI > 60, MACD > 0, Histogram growing
STRONG DOWN:  RSI < 40, MACD < 0, Histogram shrinking
OVERBOUGHT:   RSI > 70 (caution for longs)
OVERSOLD:     RSI < 30 (opportunity for longs)
```

### Stop-Loss Guidelines (based on ATR)
```
Day trade:    1-1.5x ATR
Swing trade:  2-3x ATR
Position:     3-4x ATR
```

### Target Guidelines
```
Conservative: 2x ATR (Risk:Reward = 1:1 with 2x ATR stop)
Moderate:     3-4x ATR (Risk:Reward = 1:1.5 to 1:2)
Aggressive:   Next swing high / 52w high
```

