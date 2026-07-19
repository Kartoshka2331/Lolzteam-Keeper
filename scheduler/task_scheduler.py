from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Settings
from services import ContestService, ThreadService
from utils.logger import logger


class TaskScheduler:
    def __init__(self, settings: Settings, thread_service: ThreadService, contest_service: ContestService) -> None:
        self._settings = settings
        self._thread_service = thread_service
        self._contest_service = contest_service
        self._scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    def start(self) -> None:
        if self._settings.thread_to_bump_ids:
            self._scheduler.add_job(
                self._thread_service.bump_all_threads,
                CronTrigger(hour=self._settings.thread_bump_cron_hour, minute=self._settings.thread_bump_cron_minute),
                id="thread_bump_job",
                name="Thread bumping",
            )
            logger.info("Thread bumping job scheduled")

        self._scheduler.add_job(
            self._contest_service.create_random_contest,
            CronTrigger(day=self._settings.contest_creation_cron_day, hour=self._settings.contest_creation_cron_hour, minute=self._settings.contest_creation_cron_minute),
            id="contest_creation_job",
            name="Contest creation",
        )
        logger.info("Contest creation job scheduled")

        self._scheduler.start()
        logger.info("Scheduler started")

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
