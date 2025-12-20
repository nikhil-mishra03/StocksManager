import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI

from app.agents.agent_response_model import QuantAgentResponseList as FundamentalActionList
from app.core.logger_config import get_logger
from app.tools.fundamentals_tools import get_fundamental_analysis_tool
from app.tools.quant_tools import get_active_gtts_with_metrics_tool

logger = get_logger(__name__)
load_dotenv()

model = ChatOpenAI(model="gpt-4o",api_key = os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are the Fundamental GTT Analyst.
You must use fundamental data to judge whether each GTT is sensible and what action to take.

Workflow:
1) Call get_active_gtts_with_metrics_tool to fetch current GTTs.
2) For each symbol, call get_fundamental_analysis_tool to fetch fundamentals.
3) Decide KEEP | MODIFY | CANCEL | NEW for each GTT using fundamentals.

Factors to consider:
- Profitability: profit margin, ROE, EPS trend.
- Valuation: P/E, P/B (expensive vs reasonable).
- Balance sheet strength: debt-to-equity, current ratio, net cash.
- Growth: whether the company is growing in profit, revenue, and net worth.

Output strictly follows the response schema."""

agent = create_agent(
    model = model,
    system_prompt = SYSTEM_PROMPT,
    tools = [get_active_gtts_with_metrics_tool, get_fundamental_analysis_tool],
    response_format = ToolStrategy(
        schema = FundamentalActionList,
        tool_message_content = "Stock Fundamental Analysis Response"
    )
)

# def build_agent_context(symbol: str):
#     fundamental_analysis = get_fundamental_analysis(symbol)
#     return fundamental_analysis

def run_agent():
    user_content = """
Use the tools to analyze current GTTs using fundamentals.
Return an items array where each item contains:
- symbol
- current_gtt
- recommended_action (KEEP | MODIFY | CANCEL | NEW)
- buy_price (only if MODIFY/NEW, else null)
- rationale (mention specific fundamental metrics)
- confidence (0-100)
    """
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"{user_content}"
            }
        ]
    })
    return response


if __name__ == "__main__":
    print()
