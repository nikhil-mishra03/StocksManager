from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logger_config import get_logger
from app.fundamentals.fundamental_analysis import get_all_fundamentals

logger = get_logger(__name__)

_scheduler = AsyncIOScheduler()


def _run_fundamentals_job() -> None:
    logger.info("Starting fundamentals refresh job.")
    try:
        get_all_fundamentals()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fundamentals refresh failed.", exc_info=exc)


def start_fundamentals_scheduler(interval_hours: int = 24) -> None:
    if _scheduler.get_job("fundamentals_refresh"):
        return
    _scheduler.add_job(
        _run_fundamentals_job,
        trigger=IntervalTrigger(hours=interval_hours),
        id="fundamentals_refresh",
        max_instances=1,
        replace_existing=True,
    )
    _scheduler.start()
    _run_fundamentals_job()
    logger.info("Fundamentals scheduler started (every %s hours).", interval_hours)


def stop_fundamentals_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Fundamentals scheduler stopped.")
