from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logger_config import get_logger
from app.brokers.zerodha.gtt import GTTOrderService
from app.brokers.zerodha.historical_data import HistoricalDataService
from app.brokers.zerodha.holdings import get_holding_snaphost


logger = get_logger(__name__)

_scheduler = AsyncIOScheduler()

def run_portfolio_job():
    logger.info("Starting portfolio refresh job.")
    try:
        get_holding_snaphost()
        gtt_service = GTTOrderService()
        gtt_service.get_gtts()
        historical_data_service = HistoricalDataService()
        historical_data_service.get_historical_data("day")
    except Exception as e:
        logger.error(f"Error refreshing portfolio: {e}")


def start_portfolio_scheduler(interval_hours: int = 1) -> None:
    if _scheduler.get_job("portfolio_refresh"):
        return
    _scheduler.add_job(
        run_portfolio_job,
        trigger = IntervalTrigger(hours = interval_hours),
        id = "portfolio_refresh",
        max_instances = 1,
        replace_existing = True,
    )
    _scheduler.start()
    run_portfolio_job()
    logger.info("Portfolio scheduler started (every %s hours).", interval_hours)

def stop_portfolio_scheudler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait = False)
        logger.info("Portfolio scheduler stopped")
    