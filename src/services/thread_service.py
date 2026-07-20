import asyncio

from config import Settings
from services.api_client import LolzteamApiClient
from utils.logger import logger


class ThreadService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def bump_all_threads(self) -> None:
        if not self._settings.thread_to_bump_ids:
            logger.info("No threads configured for bumping")
            return

        async with LolzteamApiClient(self._settings) as api_client:
            for thread_id in self._settings.thread_to_bump_ids:
                try:
                    await api_client.bump_thread(thread_id)
                except Exception as error:
                    logger.error(f"Error while bumping thread {thread_id}: {error}")

                await asyncio.sleep(self._settings.thread_bump_delay_seconds)
