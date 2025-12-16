from app.store.db import SessionLocal
from app.store.models import FundamentalAnalysis as FundamentalAnalysisModel
from app.core.logger_config import get_logger

logger = get_logger(__name__)
session = SessionLocal()


def get_fundamental_analysis(symbol: str) -> FundamentalAnalysisModel:
    """
    Get fundamental analysis for a symbol.

    Args:
        symbol: The trading symbol (e.g., "RELIANCE", "INFY").

    Returns:
        FundamentalAnalysis if found, None otherwise.
    """
    try:
        with SessionLocal() as session:
            analysis = session.query(FundamentalAnalysisModel).filter_by(symbol=symbol).first()
            return analysis
    except Exception as e:
        logger.error(f"Error fetching fundamental analysis: {e}")
        raise e
