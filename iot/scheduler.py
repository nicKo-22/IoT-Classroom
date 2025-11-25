"""APScheduler wrapper with sane defaults for IoT loops."""
from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

LOGGER = logging.getLogger(__name__)


class IoTScheduler:
    """Convenience helper around APScheduler."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()

    def add_interval_job(self, name: str, seconds: int, func: Callable[[], None]) -> None:
        trigger = IntervalTrigger(seconds=seconds)
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=name,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        LOGGER.info("Scheduled job %s every %ss", name, seconds)

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            LOGGER.info("Scheduler started")

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            LOGGER.info("Scheduler stopped")
