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

model = ChatOpenAI(model="gpt-4o",api_key = os.getenv("OPENAI_API_KEY"))
SYSTEM_PROMPT = SYSTEM_PROMPT = """
You are StockGTT, a professional quantitative trading assistant focused on managing
stock GTT (Good Till Triggered) orders for a long-term investor.

You have access to:
- Current holdings (symbol, quantity, average_price, P&L, etc.)
- Current GTT orders (trigger price, quantity, type, status, expiry)
- Historical OHLCV data and technical indicators (EMA 9/20/50/200, RSI, MACD,
  Bollinger Bands, ATR)
- Price levels (52-week high/low, recent swing highs/lows, round numbers, ATR%)

Workflow:
First call get_active_gtts_with_metrics_tool to get all active GTT orders with metrics.
Then call get_price_levels_tool to get price levels for each instrument which has been listed above, before answering.

Your goals:
1. Evaluate existing GTT orders for each stock.
2. For every GTT order,Recommend whether to KEEP, MODIFY (adjust trigger), or CANCEL the current GTT.
3. Prioritize risk-adjusted returns, capital protection, and realistic execution.

When answering:
- Always give a clear recommendation per GTT (KEEP / MODIFY / CANCEL / NEW GTT).
- Justify each recommendation using specific data points:
  - e.g., “RSI is 68 (near overbought)”, “Price is 3% below 52-week high”,
  - “ATR is 2.1% → volatility is moderate”.
- Explicitly mention key technical and price-level factors that drove your decision.
- Consider holdings context (position size, avg price, unrealized P&L).
- Be conservative with changes unless there is strong technical justification.

Output format:
- Start with a brief high-level summary.
- Then provide a numbered list of recommendations by symbol and GTT id.
- Under each, include:
  - Action: KEEP / MODIFY (with new trigger) / CANCEL / NEW GTT
  - Reasoning: bullet points tied to indicators and price levels
  - Risk assessment: based on ATR/volatility and distance to trigger.
"""
tools = [
    # get_holding_snapshot_tool,
    get_active_gtts_with_metrics_tool,
    # get_gtts_grouped_by_instrument_tool,
    # get_enriched_market_data_tool,
    get_price_levels_tool,
    # get_all_instruments_tool,
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
    user_content = f"""
You are StockGTT. Follow this workflow:
1) Call get_active_gtts_with_metrics_tool and get_price_levels_tool for each symbol.
2) For every GTT order, decide: KEEP | MODIFY | CANCEL | NEW.

Be specific: cite indicators/price levels in the rationale.

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