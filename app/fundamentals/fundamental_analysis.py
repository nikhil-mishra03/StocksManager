from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.logger_config import get_logger
from app.fundamentals.balance_sheet import get_balance_sheet
from app.fundamentals.company_overview import get_company_overview
from app.fundamentals.profit_loss import get_profit_loss
from app.store.models import FundamentalAnalysis
from app.store.db import SessionLocal

logger = get_logger(__name__)
session = SessionLocal()


def get_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Collect fundamentals for a symbol from the existing helpers.

    Returns a dict with:
      - overview: company overview dict
      - income: list of income statement snapshots
      - balance: list of balance sheet snapshots
    """
    logger.info("Fetching fundamentals for %s", symbol)

    overview: Dict[str, Any] = {}
    income: List[Dict[str, Any]] = []
    balance: List[Dict[str, Any]] = []

    try:
        overview = get_company_overview(symbol)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch company overview for %s", symbol, exc_info=exc)

    try:
        income = get_profit_loss(symbol)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch income statement for %s", symbol, exc_info=exc)

    try:
        balance = get_balance_sheet(symbol)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch balance sheet for %s", symbol, exc_info=exc)
    
    return {
        "symbol": symbol,
        "overview": overview,
        "income": income,
        "balance": balance,
    }


def store_fundamentals(symbol: str) -> FundamentalAnalysis:
    """
    Fetch fundamentals and persist them into the FundamentalAnalysis table.
    If a row already exists for the symbol, update it; otherwise insert a new row.
    """
    data = get_fundamentals(symbol)

    record = session.query(FundamentalAnalysis).filter_by(symbol=symbol).one_or_none()
    if record:
        record.company_overview = data["overview"]
        record.profit_loss = data["income"]
        record.balance_sheet = data["balance"]
        record.ingested_at = datetime.utcnow()
    else:
        record = FundamentalAnalysis(
            symbol=symbol,
            company_overview=data["overview"],
            profit_loss=data["income"],
            balance_sheet=data["balance"],
            ingested_at=datetime.utcnow(),
        )
        session.add(record)

    session.commit()
    return record


if __name__ == "__main__":
    # Simple smoke test; adjust ticker suffix as needed (e.g., .NS for NSE)
    import pprint

    pprint.pp(store_fundamentals("INFY"))
