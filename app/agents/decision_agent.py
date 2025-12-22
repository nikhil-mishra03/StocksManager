from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.agents.structured_output import ToolStrategy
from app.agents.agent_response_model import DecisionAgentResponseList
from app.core.logger_config import get_logger
from app.agents.fundamental_analysis_agent import run_agent as run_fundamental_analysis_agent
from app.agents.quant_agent import run_agent as run_quant_agent
import os
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


SYSTEM_PROMPT = """You are the Final Decision Agent for GTT (Good Till Triggered) order management.

You receive two analyses for each GTT:
1. **Fundamental Analysis** - business quality, valuation, balance sheet health
2. **Quantitative/Technical Analysis** - price action, indicators, support/resistance levels

Your job is to synthesize both into a comprehensive, actionable recommendation.

## OUTPUT REQUIREMENTS (STRICTLY ENFORCED)

For EVERY field in the schema, you MUST provide a meaningful value.
The only field that can be null is `buy_price` when action is KEEP or CANCEL.

### rationale.fundamental_analysis (REQUIRED - 4-6 sentences):
You MUST include ALL of the following with specific numbers:
- Revenue/profit growth: "Revenue grew from ₹X in FY2021 to ₹Y in FY2024, representing Z% CAGR"
- Profitability trends: "Profit margin improved/declined from X% to Y% over 3 years"
- ROE assessment: "ROE of X% is above/below the typical threshold of 15%"
- Valuation: "P/E of X is high/reasonable compared to historical average / growth rate"
- Balance sheet: "Debt-to-equity of X and current ratio of Y indicate strong/weak financial health"
If fundamental data is not available, state: "Fundamental data not available. Recommendation based on technical analysis only."

### rationale.technical_analysis (REQUIRED - 4-6 sentences):
You MUST include ALL of the following indicators with SPECIFIC values:

**Moving Averages (EMAs) - CRITICAL for trend assessment:**
- State: "Price (₹X) vs EMA9 (₹A), EMA20 (₹B), EMA50 (₹C), EMA200 (₹D)"
- Interpret: Bullish if Price > EMA9 > EMA20 > EMA50; Bearish if reversed; Sideways if mixed

**MACD - CRITICAL for momentum:**
- State: "MACD line (X) vs signal line (Y), histogram (Z)"
- Interpret: Bullish if MACD > signal and histogram positive/rising

**RSI - CRITICAL for overbought/oversold:**
- State: "RSI at X"
- Interpret: >70 = overbought (caution), <30 = oversold (opportunity), 30-70 = neutral

**Bollinger Bands - CRITICAL for volatility and extremes:**
- State: "Price near upper/middle/lower band (₹X / ₹Y / ₹Z)"
- Interpret: Near upper = resistance/overbought; Near lower = support/oversold

**ATR - CRITICAL for trigger distance assessment:**
- State: "ATR ₹X (Y% of price), trigger is Z ATR multiples away"
- Interpret: <1 ATR = TIGHT (whipsaw risk); 1-3 ATR = REASONABLE; >3 ATR = FAR

If technical data is not available, state: "Technical data not available. Recommendation based on fundamental analysis only."

### rationale.combined_assessment (REQUIRED - 3-4 sentences):
- Agreement/conflict: "Fundamentals and technicals agree/conflict because..."
- Key deciding factor: "The primary reason for this recommendation is..."
- Risk factor: "This recommendation would be invalidated if..."

### confidence_breakdown (REQUIRED):
- fundamental_confidence: 0-100 (0 if no fundamental data available)
- technical_confidence: 0-100 (0 if no technical data available)
- data_quality: 0-100 (based on completeness and recency of data)

### distance_to_trigger_atr (REQUIRED):
Calculate as: abs(current_price - trigger_price) / ATR
If ATR is not provided, estimate using: ATR ≈ 2% of current price (typical equity volatility)
Example: If current_price=1175, trigger=1100, estimated ATR=23.5, then distance = 75/23.5 = 3.19 ATR

### risk_reward (REQUIRED):
Estimate based on distance to trigger vs potential upside/downside.
Format: "1:X.X" (e.g., "1:2.5") or "unfavorable" if risk exceeds reward.
If insufficient data, state: "1:1 (neutral - insufficient data for precise calculation)"

### time_horizon (REQUIRED):
Based on trigger distance and volatility:
- "short" = trigger likely hit in days to 2 weeks
- "medium" = trigger likely hit in 2 weeks to 2 months
- "long" = trigger likely hit in 2+ months or uncertain

### trend_state (REQUIRED):
Must be one of: "uptrend", "downtrend", or "sideways"
Determine based on EMA alignment and price structure from technical data.

## QUALITY STANDARDS
- Be SPECIFIC: "RSI is 62" not "RSI is neutral"
- Be QUANTITATIVE: "3.2% below 52W high" not "near highs"
- Be COMPARATIVE: "P/E of 67 vs sector avg of 22" not "P/E is high"
- ACKNOWLEDGE gaps: If data is missing, say so explicitly rather than making up values

## CONFLICT RESOLUTION
When fundamental and technical signals conflict:
1. State the conflict clearly in combined_assessment
2. Weight long-term fundamental strength higher for LONG time horizons
3. Weight technical momentum higher for SHORT time horizons
4. For MEDIUM horizons, prefer the analysis with higher data quality
5. Reduce overall confidence when signals conflict
"""

model = ChatOpenAI(
    model="gpt-5",
    api_key=os.getenv("OPENAI_API_KEY"),
)

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(
        schema=DecisionAgentResponseList,
        tool_message_content="Final Stock Decision Response"
    )
)


def run_agent(fund_out, quant_out):
    """
    Run the decision agent with outputs from fundamental and quant agents.

    Args:
        fund_out: Output from fundamental analysis agent
        quant_out: Output from quantitative analysis agent

    Returns:
        DecisionAgentResponseList with comprehensive recommendations
    """
    user_content = f"""
Analyze the following GTT recommendations from two different analyses and produce a final decision for each.

## FUNDAMENTAL ANALYSIS RECOMMENDATIONS:
{fund_out}

## QUANTITATIVE/TECHNICAL ANALYSIS RECOMMENDATIONS:
{quant_out}

## YOUR TASK:
For each GTT, synthesize both analyses into a final recommendation.

IMPORTANT REQUIREMENTS:
1. Every field in the response schema MUST be filled with meaningful data
2. The rationale MUST have three sections: fundamental_analysis, technical_analysis, combined_assessment
3. Each section MUST contain 4-6 sentences with SPECIFIC numbers and metrics
4. Include confidence_breakdown with scores for fundamental, technical, and data_quality
5. Calculate distance_to_trigger_atr (use 2% of price as ATR estimate if not provided)
6. Provide risk_reward ratio and time_horizon for each recommendation

If one analysis source is missing data, acknowledge it in the rationale but still provide
the best possible recommendation based on available data.
"""
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": user_content
            }
        ]
    })
    return response


def _get_items_count(output) -> str:
    """Safely get item count from agent output."""
    try:
        # If it's a Pydantic model with items attribute
        if hasattr(output, 'items') and isinstance(output.items, list):
            return str(len(output.items))
        # If it's a dict with 'items' key
        if isinstance(output, dict) and 'items' in output:
            return str(len(output['items']))
        return 'N/A'
    except Exception:
        return 'N/A'


def run_pipeline():
    """Run the full decision pipeline: fundamental agent → quant agent → decision agent."""
    logger.info("Starting decision pipeline...")

    logger.info("Running fundamental analysis agent...")
    fund_out = run_fundamental_analysis_agent()
    logger.info(f"Fundamental agent complete: {_get_items_count(fund_out)} items")

    logger.info("Running quantitative analysis agent...")
    quant_out = run_quant_agent()
    logger.info(f"Quant agent complete: {_get_items_count(quant_out)} items")

    logger.info("Running decision agent to synthesize recommendations...")
    result = run_agent(fund_out, quant_out)
    logger.info("Decision pipeline complete.")

    return result