# from langchain.agents import create_agent
# from langchain_openai import ChatOpenAI
# from app.service.fundamentals_service import get_fundamental_analysis
# import os
# from dotenv import load_dotenv
# from app.core.logger_config import get_logger
# from fastapi.encoders import jsonable_encoder  

# logger = get_logger(__name__)
# load_dotenv()

# model = ChatOpenAI(model="gpt-4",api_key = os.getenv("OPENAI_API_KEY"))

# SYSTEM_PROMPT = """"""

# agent = create_agent(
#     model = model,
#     system_prompt = SYSTEM_PROMPT
#     # tools = [get_fundamental_analysis]
# )

# def build_agent_context(symbol: str):
#     fundamental_analysis = get_fundamental_analysis(symbol)
#     return fundamental_analysis

# def run_agent(symbol: str):
#     ctx = build_agent_context(symbol)
#     user_content = f"""
# [FUNDAMENTAL_ANALYSIS]
# {jsonable_encoder(ctx)}

# YOU ARE A QUANT TRADING SPECIALIST. YOUR JOB IS TO DO FUNDAMENTAL ANALYSIS OF STOCKS.
# DECIDE buy | avoid. Give a short rationale and suggest a buy range if buy. 
#     """
#     response = agent.invoke({
#         "messages": [
#             {
#                 "role": "user",
#                 "content": f"{user_content}"
#             }
#         ]
#     })
#     return response


# if __name__ == "__main__":
#     print()