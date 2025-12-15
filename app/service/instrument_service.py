"""
Instrument Service Module.

Provides functions to query instruments from the database.
Broker-agnostic: only depends on the database.
"""

from app.store.models import Instrument
from app.store.db import SessionLocal
from app.core.logger_config import get_logger
from langchain.tools import tool

logger = get_logger(__name__)


def get_all_instruments() -> list[Instrument]:
    """
    Get all instruments from the database.

    Returns:
        List of all Instrument records.
    """
    with SessionLocal() as session:
        instruments = session.query(Instrument).all()
        return instruments


def get_instrument_by_token(token: int) -> Instrument | None:
    """
    Get an instrument by its token.

    Args:
        token: The instrument token.

    Returns:
        Instrument if found, None otherwise.
    """
    with SessionLocal() as session:
        instrument = session.query(Instrument).filter_by(token=token).first()
        return instrument


def get_instrument_by_symbol(symbol: str) -> Instrument | None:
    """
    Get an instrument by its symbol.

    Args:
        symbol: The trading symbol (e.g., "RELIANCE", "INFY").

    Returns:
        Instrument if found, None otherwise.
    """
    with SessionLocal() as session:
        instrument = session.query(Instrument).filter_by(symbol=symbol).first()
        return instrument


def get_instruments_by_exchange(exchange: str) -> list[Instrument]:
    """
    Get all instruments for a specific exchange.

    Args:
        exchange: The exchange name (e.g., "NSE", "BSE").

    Returns:
        List of Instrument records for the exchange.
    """
    with SessionLocal() as session:
        instruments = session.query(Instrument).filter_by(exchange=exchange).all()
        return instruments
