"""
Sentiment analysis tools for LangChain agents.
"""

from langchain.tools import tool
from fastapi.encoders import jsonable_encoder

from app.service.news_service import get_news_for_symbol
from app.service.gtt_service import get_active_gtts_with_metrics


@tool
def get_stock_news_tool(symbol: str) -> dict:
    """
    Fetch recent news articles for a stock symbol.
    
    Use this tool to get the latest news headlines for sentiment analysis.
    Returns up to 4 recent news articles with titles, sources, and dates.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
    
    Returns:
        Dict containing:
        - symbol: The stock symbol
        - article_count: Number of articles found
        - articles: List of article objects with title, source, published_date, link
        - formatted_for_analysis: Pre-formatted string for easy analysis
    """
    try:
        news_data = get_news_for_symbol(symbol)
        return jsonable_encoder(news_data)
    except Exception as e:
        return {
            "symbol": symbol,
            "article_count": 0,
            "articles": [],
            "formatted_for_analysis": f"Error fetching news: {str(e)}",
            "error": str(e)
        }


@tool
def get_symbols_from_gtts_tool() -> list:
    """
    Get list of unique stock symbols from active GTT orders.
    
    Use this tool first to get the list of symbols that need sentiment analysis.
    
    Returns:
        List of unique stock symbols from active GTTs
    """
    try:
        gtts = get_active_gtts_with_metrics()
        symbols = list(set(gtt.get("tradingsymbol", "") for gtt in gtts if gtt.get("tradingsymbol")))
        return symbols
    except Exception as e:
        return {"error": str(e), "symbols": []}

