"""
News fetching service using Google News RSS.
Free, no API key required - suitable for learning/personal projects.
"""

import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import requests

from app.core.logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class NewsArticle:
    """Represents a single news article."""
    title: str
    source: str
    published_date: str
    link: str
    snippet: Optional[str] = None


def fetch_stock_news(
    symbol: str,
    company_name: Optional[str] = None,
    max_articles: int = 4
) -> List[NewsArticle]:
    """
    Fetch recent news articles for a stock using Google News RSS.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        company_name: Optional company name for better search results
        max_articles: Maximum number of articles to return (default: 4)
    
    Returns:
        List of NewsArticle objects with title, source, date, and link
    """
    # Build search query - include both symbol and company name if available
    # Adding "stock" and "NSE" helps get relevant financial news for Indian stocks
    if company_name:
        query = f"{company_name} {symbol} stock NSE"
    else:
        query = f"{symbol} stock NSE India"
    
    encoded_query = urllib.parse.quote(query)
    
    # Google News RSS feed URL
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    articles: List[NewsArticle] = []
    
    try:
        logger.info(f"Fetching news for {symbol} from Google News RSS")
        
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
        
        # Parse RSS XML
        root = ET.fromstring(response.content)
        
        # Find all item elements (news articles)
        items = root.findall(".//item")
        
        for item in items[:max_articles]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            source_elem = item.find("source")
            
            if title_elem is not None and title_elem.text:
                article = NewsArticle(
                    title=title_elem.text.strip(),
                    source=source_elem.text.strip() if source_elem is not None and source_elem.text else "Unknown",
                    published_date=pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else "",
                    link=link_elem.text.strip() if link_elem is not None and link_elem.text else "",
                    snippet=None  # Google News RSS doesn't provide snippets in basic feed
                )
                articles.append(article)
        
        logger.info(f"Found {len(articles)} news articles for {symbol}")
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch news for {symbol}: {e}")
    except ET.ParseError as e:
        logger.error(f"Failed to parse RSS feed for {symbol}: {e}")
    
    return articles


def format_news_for_analysis(articles: List[NewsArticle]) -> str:
    """
    Format news articles into a string suitable for LLM analysis.
    
    Args:
        articles: List of NewsArticle objects
    
    Returns:
        Formatted string with numbered articles
    """
    if not articles:
        return "No recent news articles found for this stock."
    
    formatted_parts = []
    for i, article in enumerate(articles, 1):
        formatted_parts.append(
            f"{i}. [{article.source}] {article.title}\n"
            f"   Published: {article.published_date}"
        )
    
    return "\n\n".join(formatted_parts)


def get_news_for_symbol(symbol: str, company_name: Optional[str] = None) -> dict:
    """
    Main entry point: fetch and format news for a stock symbol.
    
    Args:
        symbol: Stock symbol
        company_name: Optional company name
    
    Returns:
        Dict with symbol, article_count, and formatted_news
    """
    articles = fetch_stock_news(symbol, company_name)
    formatted_news = format_news_for_analysis(articles)
    
    return {
        "symbol": symbol,
        "article_count": len(articles),
        "articles": [
            {
                "title": a.title,
                "source": a.source,
                "published_date": a.published_date,
                "link": a.link
            }
            for a in articles
        ],
        "formatted_for_analysis": formatted_news
    }

