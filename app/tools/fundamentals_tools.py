from langchain.tools import tool
from app.service.fundamentals_service import get_fundamental_analysis
from fastapi.encoders import jsonable_encoder

@tool
def get_fundamental_analysis_tool(symbol: str):
    """Get fundamental analysis for a symbol"""
    try:
        analysis = get_fundamental_analysis(symbol)
        return jsonable_encoder(analysis)
    except Exception as e:
        raise e