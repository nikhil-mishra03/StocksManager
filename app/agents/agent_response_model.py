from pydantic import BaseModel, Field
from typing import List


# ============================================================
# Shared sub-models for detailed breakdowns
# ============================================================

class RationaleBreakdown(BaseModel):
    """Structured rationale with separate sections for fundamental, technical, and combined analysis."""

    fundamental_analysis: str = Field(
        ...,
        description="""Detailed fundamental breakdown (4-6 sentences) including:
        - Multi-year revenue/profit growth trends with specific numbers (e.g., 'Revenue grew from ₹X to ₹Y, Z% CAGR')
        - Year-over-year changes in profit margin, ROE, ROA with direction
        - P/E, P/B interpretation vs industry/historical averages
        - Debt-to-equity and balance sheet health assessment
        If fundamental data unavailable, state 'Fundamental data not available for this analysis.'"""
    )
    technical_analysis: str = Field(
        ...,
        description="""Detailed technical breakdown (4-6 sentences) including:
        - EMA positions: price vs 9/20/50/200 EMAs with specific values
        - MACD: line value, signal value, histogram, and interpretation
        - RSI: current value and overbought/oversold/neutral assessment
        - Bollinger Band position (upper/middle/lower)
        - ATR value, volatility assessment, and distance to trigger in ATR multiples
        If technical data unavailable, state 'Technical data not available for this analysis.'"""
    )
    combined_assessment: str = Field(
        ...,
        description="""Synthesis of fundamental + technical (3-4 sentences) including:
        - Areas of agreement or conflict between the two analyses
        - The key deciding factor for the recommendation
        - Risk factors that could invalidate the recommendation"""
    )


class ConfidenceBreakdown(BaseModel):
    """Breakdown of confidence score by analysis type."""

    fundamental_confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence from fundamental analysis (0-100). 0 if no fundamental data."
    )
    technical_confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence from technical analysis (0-100). 0 if no technical data."
    )
    data_quality: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence in data completeness and quality (0-100)."
    )


# ============================================================
# Quant Agent Response (for technical/quantitative analysis)
# ============================================================

class QuantAgentResponse(BaseModel):
    """Response from the quantitative/technical analysis agent."""

    symbol: str = Field(..., description="Symbol of the instrument")
    current_gtt: float = Field(..., description="Current GTT trigger price for the instrument")
    recommended_action: str = Field(
        ...,
        description="Recommended action for the GTT order. One of: KEEP, MODIFY, CANCEL, NEW"
    )
    buy_price: float | None = Field(
        None,
        description="New trigger price if MODIFY/NEW, else null for KEEP/CANCEL."
    )
    rationale: str = Field(
        ...,
        description="Detailed rationale (4-6 sentences) with specific indicator values and levels."
    )
    confidence: int = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    current_price: float = Field(..., description="Latest price used for analysis.")
    distance_to_trigger_pct: float = Field(..., description="Percent gap between current price and trigger.")
    distance_to_trigger_atr: float = Field(
        ...,
        description="Gap in ATR multiples. If ATR unavailable, estimate using 2% of price as typical ATR."
    )
    trend_state: str = Field(
        ...,
        description="Trend state: 'uptrend', 'downtrend', or 'sideways'"
    )
    risk_reward: str = Field(
        ...,
        description="Risk:reward ratio (e.g., '1:2.5') or 'unfavorable' if no clear levels."
    )
    time_horizon: str = Field(
        ...,
        description="Expected time horizon: 'short' (days), 'medium' (weeks), 'long' (months)"
    )


# ============================================================
# Fundamental Analysis Agent Response
# ============================================================

class FundamentalAnalysisAgentResponse(BaseModel):
    """Response from the fundamental analysis agent."""

    symbol: str = Field(..., description="Symbol of the instrument")
    current_gtt: float = Field(..., description="Current GTT trigger price for the instrument")
    recommended_action: str = Field(
        ...,
        description="Recommended action: KEEP, MODIFY, CANCEL, or NEW"
    )
    buy_price: float | None = Field(
        None,
        description="New trigger price if MODIFY/NEW, else null."
    )
    rationale: str = Field(
        ...,
        description="""Detailed rationale (4-6 sentences) including:
        - Valuation metrics (P/E, P/B) with interpretation
        - Profitability (ROE, profit margin) trends
        - Balance sheet health (debt-to-equity, current ratio)
        - Growth trajectory and sustainability"""
    )
    confidence: int = Field(..., ge=0, le=100, description="Confidence score (0-100)")


# ============================================================
# Decision Agent Response (combines fundamental + technical)
# ============================================================

class DecisionAgentResponse(BaseModel):
    """Final decision response combining fundamental and technical analysis."""

    symbol: str = Field(..., description="Symbol of the instrument")
    current_gtt: float = Field(..., description="Current GTT trigger price")
    recommended_action: str = Field(
        ...,
        description="Final recommended action: KEEP, MODIFY, CANCEL, or NEW"
    )
    buy_price: float | None = Field(
        None,
        description="New trigger price if MODIFY/NEW, else null for KEEP/CANCEL."
    )

    # Structured rationale (required)
    rationale: RationaleBreakdown = Field(
        ...,
        description="Detailed breakdown of reasoning by analysis type."
    )

    # Confidence with breakdown (required)
    confidence: int = Field(..., ge=0, le=100, description="Overall confidence score (0-100)")
    confidence_breakdown: ConfidenceBreakdown = Field(
        ...,
        description="Breakdown of confidence by analysis type."
    )

    # Technical metrics (all required)
    current_price: float = Field(..., description="Latest price used for analysis.")
    distance_to_trigger_pct: float = Field(
        ...,
        description="Percent gap between current price and trigger."
    )
    distance_to_trigger_atr: float = Field(
        ...,
        description="Gap in ATR multiples. If ATR unavailable, estimate using 2% of price."
    )
    trend_state: str = Field(
        ...,
        description="Trend state: 'uptrend', 'downtrend', or 'sideways'"
    )

    # Risk/reward assessment (required)
    risk_reward: str = Field(
        ...,
        description="Risk:reward ratio (e.g., '1:2.5') or 'unfavorable' with explanation."
    )
    time_horizon: str = Field(
        ...,
        description="Expected time horizon: 'short' (days), 'medium' (weeks), 'long' (months)"
    )


# ============================================================
# List wrappers for agent responses
# ============================================================

class QuantAgentResponseList(BaseModel):
    """List of quant agent responses."""
    items: List[QuantAgentResponse]


class FundamentalAnalysisAgentResponseList(BaseModel):
    """List of fundamental analysis agent responses."""
    items: List[FundamentalAnalysisAgentResponse]


class DecisionAgentResponseList(BaseModel):
    """List of final decision agent responses."""
    items: List[DecisionAgentResponse]
