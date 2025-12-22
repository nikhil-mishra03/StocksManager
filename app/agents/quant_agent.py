from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
# from app.service.holding_service import get_holding_snapshot
# from app.service.gtt_service import get_active_gtts_with_metrics, get_gtts_grouped_by_instrument
# from app.service.market_data import get_enriched_market_data, get_price_levels
from app.tools.quant_tools import (
    get_holding_snapshot_tool,
    get_active_gtts_with_metrics_tool,
    get_gtts_grouped_by_instrument_tool,
    get_enriched_market_data_tool,
    get_price_levels_tool,
    get_all_instruments_tool,
    get_instrument_indicators_tool
)
from fastapi.encoders import jsonable_encoder
from app.core.logger_config import get_logger
from app.agents.agent_response_model import QuantAgentResponseList as QuantAgentResponseModel
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import SummarizationMiddleware
import json

import os
from dotenv import load_dotenv
load_dotenv()

logger = get_logger(__name__)

model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are StockGTT, a professional quantitative trading assistant focused on managing
stock GTT (Good Till Triggered) orders for a long-term investor.

## AVAILABLE TOOLS

1. **get_active_gtts_with_metrics_tool** - All active GTT orders with metrics
2. **get_price_levels_tool(instrument_token)** - Support/resistance levels
3. **get_instrument_indicators_tool(instrument_token)** - Technical indicators (CRITICAL)

## REQUIRED WORKFLOW

For EVERY GTT analysis, you MUST:
1. Call get_active_gtts_with_metrics_tool to get all GTTs
2. For EACH instrument_token in the GTTs:
   a. Call get_instrument_indicators_tool(instrument_token) - THIS IS REQUIRED
   b. Call get_price_levels_tool(instrument_token)
3. Analyze indicators and make recommendations

## TECHNICAL INDICATORS (MUST USE ALL)

get_instrument_indicators_tool returns these - USE ALL OF THEM:

### EMAs (ema_9, ema_20, ema_50, ema_200)
- Bullish: Price > EMA9 > EMA20 > EMA50 > EMA200
- Bearish: Price < EMA9 < EMA20 < EMA50 < EMA200
- MUST STATE: "Price (X) vs EMA20 (Y), EMA50 (Z) indicates uptrend/downtrend/sideways"

### RSI (rsi_14)
- Overbought: RSI > 70 | Oversold: RSI < 30 | Neutral: 30-70
- MUST STATE: "RSI at X indicates overbought/oversold/neutral"

### MACD (macd_line, macd_signal, macd_histogram)
- Bullish: MACD > Signal, histogram positive
- Bearish: MACD < Signal, histogram negative
- MUST STATE: "MACD (X) vs signal (Y), histogram (Z) shows bullish/bearish momentum"

### Bollinger Bands (bb_upper, bb_middle, bb_lower)
- Upper band: Resistance | Lower band: Support
- MUST STATE: "Price near upper/middle/lower Bollinger Band"

### ATR (atr_14) - CRITICAL FOR GTT DISTANCE
- distance_atr = abs(current_price - trigger) / atr_14
- < 1 ATR: TIGHT (whipsaw risk) | 1-3 ATR: REASONABLE | > 3 ATR: FAR
- MUST STATE: "ATR X (Y%), trigger is Z ATR away - tight/reasonable/far"

## OUTPUT REQUIREMENTS

### trend_state (REQUIRED)
- "uptrend" if price > ema_20 > ema_50
- "downtrend" if price < ema_20 < ema_50
- "sideways" otherwise

### distance_to_trigger_atr (REQUIRED)
= abs(current_price - trigger) / atr_14
(If ATR null, use 2% of price as estimate)

### risk_reward (REQUIRED)
Format: "1:X.X" or "unfavorable"

### rationale (REQUIRED - 4-6 sentences with SPECIFIC numbers)
1. EMA alignment with values
2. MACD line/signal/histogram with values
3. RSI value and interpretation
4. Bollinger Band position
5. ATR and trigger distance in ATR multiples
6. Final recommendation reasoning

## DECISION LOGIC

- **KEEP**: 1-3 ATR distance, trend supports, technicals neutral/favorable
- **MODIFY**: < 1 ATR (too tight) OR technicals suggest better level
- **CANCEL**: > 5 ATR OR fundamentals/technicals clearly bearish
- **NEW**: No GTT but setup warrants one
"""

tools = [
    get_active_gtts_with_metrics_tool,
    get_price_levels_tool,
    get_instrument_indicators_tool,
]

agent = create_agent(
    model = model,
    tools = tools,
    system_prompt = SYSTEM_PROMPT,
    response_format = ToolStrategy(
        schema = QuantAgentResponseModel ,
        tool_message_content = "Stock Quant Analysis Response"
    ) ,
    # middleware=[
    # SummarizationMiddleware(
    #     model="gpt-4o",
        # trigger=("tokens", 1500),
        # keep=("messages", 20),
    # ) ,
# ],

)

# def build_agent_context():
#     holdings = get_holding_snapshot()
    
#     gtts = get_gtts_grouped_by_instrument()
#     instruments_token = [
#         gtt.instrument_token for gtt in gtts
#     ]
#     logger.info(instruments_token)
#     gtts = jsonable_encoder(gtts)
#     price_levels = [
#         get_price_levels(instrument_token) for instrument_token in instruments_token
#     ]
#     price_levels = jsonable_encoder(price_levels)
#     logger.info(price_levels)
    
#     return {
#         "holdings": holdings,
#         "gtts": gtts,
#         "price_levels": price_levels
#     }

def run_agent():
    # ctx = build_agent_context()
    user_content = """
Follow the workflow in the system prompt and return structured items.
For each GTT:
- include current_price and distance_to_trigger (both % and ATR multiples)
- assess if trigger distance is too tight / reasonable / too far
- include trend_state and time_horizon
- provide 4–6 sentences in rationale with concrete numbers
If you cannot compute a field, set it to "unknown" (string) or 0.0 for numeric fields.
"""
    # response  =agent.invoke(
    #     {
    #     "messages": [
    #         {"role": "user",
    #          "content": user_content
    #          }
    #     ]
    # }
    # )
    # logger.info(response)
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_content
                }
            ]
        }
    )
    return response


if __name__ == "__main__":
    run_agent()
