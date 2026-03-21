import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.collector import collect_once
from app.config import get_settings
from app.db import SessionLocal

logger = logging.getLogger(__name__)


def run_collection_job() -> None:
    with SessionLocal() as db:
        try:
            collect_once(db)
        except Exception:  # noqa: BLE001
            logger.exception("scheduled collection failed")


def create_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_collection_job,
        trigger="interval",
        seconds=settings.collect_interval_seconds,
        id="collect-sushiro-hk",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    return scheduler
