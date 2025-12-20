from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.agents.structured_output import ToolStrategy
from app.agents.agent_response_model import QuantAgentResponseList as DecisionAgentResponseModel
from app.core.logger_config import get_logger
from app.agents.fundamental_analysis_agent import run_agent as run_fundamental_analysis_agent
from app.agents.quant_agent import run_agent as run_quant_agent
import os
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)



SYSTEM_PROMPT = f"""You will receive two lists of recommendations for the same GTTs: 
1. Based on fundamentals analysis of stocks.
2. Based on Quantitative analysis of stocks.
Take both the data into consideration. Analyse the two sets of data. Resolve into a final decision.
If conflicts, explain why and choose one. Output must be a list with fields: 
symbol
current_gtt
recommended_action
buy_price 
rationale 
confidence
If one of the fundamental analysis data or Quantitative analysis data is not available, then explicitly mention.
Your reasoning must be comprehensive and include all relevant factors. Verbosity is preferred."""

model = ChatOpenAI(
    model = "gpt-4o",
    api_key = os.getenv("OPENAI_API_KEY") , 
    )

agent = create_agent(
    model = model,
    system_prompt = SYSTEM_PROMPT,
    response_format = ToolStrategy(
        schema = DecisionAgentResponseModel,
        tool_message_content = "Final Stock Decision Response"
    )
)

def run_agent(fund_out, quant_out):
    user_content = f"""
Intelligently Analyze current GTTs using two sets of data - 
- fundamental analysis of the stock
{fund_out}
- quantitative analysis of the stock
{quant_out}
Return an items array where each item contains:
- symbol
- current_gtt
- recommended_action (KEEP | MODIFY | CANCEL | NEW)
- buy_price (only if MODIFY/NEW, else null)
- rationale (mention specific fundamental metrics) - be verbose.
- confidence (0-100)
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

def run_pipeline():
    fund_out = run_fundamental_analysis_agent()
    quant_out = run_quant_agent()
    return run_agent(fund_out, quant_out)