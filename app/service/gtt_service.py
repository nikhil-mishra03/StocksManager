"""
GTT Order Service Module.

Provides functions to query and analyze GTT orders from the database.
Broker-agnostic: only depends on the database.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.store.models import GTTOrder, Instrument, HistoricalData
from app.store.db import SessionLocal
from app.core.logger_config import get_logger
from langchain.tools import tool

logger = get_logger(__name__)


@dataclass
class GTTWithMetrics:
    """GTT order with computed metrics."""

    gtt: GTTOrder
    symbol: str
    exchange: str
    current_price: float | None
    distance_percent: float | None
    days_to_expiry: int | None


@dataclass
class GTTGroupSummary:
    """Summary of GTT orders grouped by instrument."""

    instrument_token: int
    symbol: str
    exchange: str
    buy_orders: list[GTTOrder]
    sell_orders: list[GTTOrder]
    total_buy_quantity: int
    total_sell_quantity: int
    nearest_buy_trigger: float | None
    nearest_sell_trigger: float | None


def get_active_gtts() -> list[GTTOrder]:
    """
    Get all active GTT orders.

    Returns:
        List of active GTTOrder records.
    """
    with SessionLocal() as session:
        gtts = session.query(GTTOrder).filter_by(status="active").all()
        return gtts


def get_gtt_by_id(gtt_id: int) -> GTTOrder | None:
    """
    Get a GTT order by its internal ID.

    Args:
        gtt_id: The internal database ID.

    Returns:
        GTTOrder if found, None otherwise.
    """
    with SessionLocal() as session:
        gtt = session.query(GTTOrder).filter_by(id=gtt_id).first()
        return gtt


def get_gtt_by_zerodha_id(zerodha_id: int) -> GTTOrder | None:
    """
    Get a GTT order by its Zerodha ID.

    Args:
        zerodha_id: The Zerodha GTT trigger ID.

    Returns:
        GTTOrder if found, None otherwise.
    """
    with SessionLocal() as session:
        gtt = session.query(GTTOrder).filter_by(zerodha_id=zerodha_id).first()
        return gtt


def get_gtts_by_instrument(instrument_token: int) -> list[GTTOrder]:
    """
    Get all GTT orders for a specific instrument.

    Args:
        instrument_token: The instrument token.

    Returns:
        List of GTTOrder records for the instrument.
    """
    with SessionLocal() as session:
        gtts = (
            session.query(GTTOrder)
            .filter_by(instrument_token=instrument_token)
            .all()
        )
        return gtts


def get_gtts_by_status(status: str) -> list[GTTOrder]:
    """
    Get all GTT orders with a specific status.

    Args:
        status: One of 'active', 'triggered', 'cancelled', 'expired', 'error'.

    Returns:
        List of GTTOrder records with the given status.
    """
    with SessionLocal() as session:
        gtts = session.query(GTTOrder).filter_by(status=status).all()
        return gtts


def get_expiring_gtts(days: int = 7) -> list[GTTOrder]:
    """
    Get active GTT orders expiring within the specified number of days.

    Args:
        days: Number of days to look ahead (default: 7).

    Returns:
        List of GTTOrder records expiring soon.
    """
    with SessionLocal() as session:
        cutoff = datetime.now() + timedelta(days=days)
        gtts = (
            session.query(GTTOrder)
            .filter(GTTOrder.status == "active")
            .filter(GTTOrder.expires_at <= cutoff)
            .order_by(GTTOrder.expires_at)
            .all()
        )
        return gtts


# @tool
def get_active_gtts_with_metrics() -> list[GTTWithMetrics]:
    """
    Get all active GTT orders with computed metrics.

    Metrics include:
    - Current price (latest close from historical data)
    - Distance percent (how far current price is from trigger)
    - Days to expiry

    Returns:
        List of GTTWithMetrics objects.
    """
    with SessionLocal() as session:
        gtts_with_instruments = (
            session.query(GTTOrder, Instrument)
            .join(Instrument, GTTOrder.instrument_token == Instrument.token)
            .filter(GTTOrder.status == "active")
            .all()
        )

        results: list[GTTWithMetrics] = []

        for gtt, instrument in gtts_with_instruments:
            latest_candle = (
                session.query(HistoricalData)
                .filter_by(instrument_token=gtt.instrument_token)
                .order_by(HistoricalData.timestamp.desc())
                .first()
            )

            current_price = latest_candle.close if latest_candle else None

            distance_percent = None
            if current_price and gtt.trigger_price:
                distance_percent = (
                    (gtt.trigger_price - current_price) / current_price
                ) * 100

            days_to_expiry = None
            if gtt.expires_at:
                delta = gtt.expires_at - datetime.now()
                days_to_expiry = max(0, delta.days)

            results.append(
                GTTWithMetrics(
                    gtt=gtt,
                    symbol=instrument.symbol,
                    exchange=instrument.exchange,
                    current_price=current_price,
                    distance_percent=distance_percent,
                    days_to_expiry=days_to_expiry,
                )
            )

        return results

# @tool
def get_gtts_grouped_by_instrument() -> list[GTTGroupSummary]:
    """
    Get active GTT orders grouped by instrument with summary metrics.

    Returns:
        List of GTTGroupSummary objects, one per instrument.
    """
    with SessionLocal() as session:
        gtts_with_instruments = (
            session.query(GTTOrder, Instrument)
            .join(Instrument, GTTOrder.instrument_token == Instrument.token)
            .filter(GTTOrder.status == "active")
            .all()
        )

        groups: dict[int, dict] = {}

        for gtt, instrument in gtts_with_instruments:
            token = instrument.token

            if token not in groups:
                groups[token] = {
                    "instrument_token": token,
                    "symbol": instrument.symbol,
                    "exchange": instrument.exchange,
                    "buy_orders": [],
                    "sell_orders": [],
                }

            if gtt.transaction_type == "buy":
                groups[token]["buy_orders"].append(gtt)
            else:
                groups[token]["sell_orders"].append(gtt)

        results: list[GTTGroupSummary] = []

        for token, group in groups.items():
            buy_orders = group["buy_orders"]
            sell_orders = group["sell_orders"]

            results.append(
                GTTGroupSummary(
                    instrument_token=token,
                    symbol=group["symbol"],
                    exchange=group["exchange"],
                    buy_orders=buy_orders,
                    sell_orders=sell_orders,
                    total_buy_quantity=sum(o.quantity for o in buy_orders),
                    total_sell_quantity=sum(o.quantity for o in sell_orders),
                    nearest_buy_trigger=(
                        max(o.trigger_price for o in buy_orders) if buy_orders else None
                    ),
                    nearest_sell_trigger=(
                        min(o.trigger_price for o in sell_orders) if sell_orders else None
                    ),
                )
            )

        return results
