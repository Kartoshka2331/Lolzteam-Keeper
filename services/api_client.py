import asyncio
from types import TracebackType
from typing import Any, Self

import aiohttp
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from config import Settings
from models import ContestConfig
from utils.logger import logger


class LolzteamApiError(Exception):
    pass


class BumpLimitReachedError(LolzteamApiError):
    pass


def _is_retryable_error(raised_error: BaseException) -> bool:
    if isinstance(raised_error, aiohttp.ClientResponseError):
        return raised_error.status == 429 or raised_error.status >= 500
    return isinstance(raised_error, (aiohttp.ClientError, asyncio.TimeoutError))


class LolzteamApiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        timeout = aiohttp.ClientTimeout(total=self._settings.api_request_timeout_seconds)
        headers = {"accept": "application/json", "Authorization": f"Bearer {self._settings.api_token}"}
        self._session = aiohttp.ClientSession(base_url=self._settings.api_base_url, headers=headers, timeout=timeout)
        return self

    async def __aexit__(self, exception_type: type[BaseException] | None, exception_value: BaseException | None, traceback: TracebackType | None) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    @property
    def _active_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("LolzteamApiClient must be used as an async context manager")
        return self._session

    def _build_retry_decorator(self) -> Any:
        return retry(
            stop=stop_after_attempt(self._settings.retry_max_attempts),
            wait=wait_exponential(multiplier=self._settings.retry_wait_multiplier, min=self._settings.retry_wait_min_seconds, max=self._settings.retry_wait_max_seconds),
            retry=retry_if_exception(_is_retryable_error),
            before_sleep=lambda retry_state: logger.warning(f"Retry attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"),
            reraise=True,
        )

    async def bump_thread(self, thread_id: int) -> None:
        async def perform_request() -> None:
            async with self._active_session.post(f"/threads/{thread_id}/bump") as response:
                response.raise_for_status()
                response_payload: dict[str, Any] = await response.json()

            if response_payload.get("status") == "ok":
                logger.info(f"Thread {thread_id} successfully bumped")
                return

            errors = response_payload.get("errors") or [""]
            if isinstance(errors, list) and errors and str(errors[0]).startswith("Согласно вашим правам"):
                logger.warning(f"Bump limit reached for thread {thread_id}")
                raise BumpLimitReachedError(f"Bump limit reached for thread {thread_id}")

            logger.error(f"Unknown error while bumping thread {thread_id}. Response: {response_payload}")
            raise LolzteamApiError(f"Unknown error while bumping thread {thread_id}: {response_payload}")

        await self._build_retry_decorator()(perform_request)()

    async def create_contest(self, contest_config: ContestConfig) -> None:
        async def perform_request() -> None:
            payload = {"post_body": contest_config.body}
            query_params: dict[str, Any] = {
                "title": contest_config.title,
                "contest_type": contest_config.parameters.contest_type,
                "length_value": contest_config.parameters.length_value,
                "length_option": contest_config.parameters.length_option,
                "prize_type": contest_config.parameters.prize_type,
                "count_winners": contest_config.parameters.count_winners,
                "prize_data_money": contest_config.parameters.prize_data_money,
                "require_like_count": contest_config.parameters.require_like_count,
                "require_total_like_count": contest_config.parameters.require_total_like_count,
                "secret_answer": self._settings.secret_answer,
                "tags": contest_config.parameters.tags,
            }

            async with self._active_session.post("/contests", json=payload, params=query_params) as response:
                response.raise_for_status()
                response_payload: dict[str, Any] = await response.json()

            if response_payload.get("thread", {}).get("thread_id"):
                logger.info(f"Contest '{contest_config.title}' successfully created")
                return

            logger.error(f"Unknown error while creating contest '{contest_config.title}'. Response: {response_payload}")
            raise LolzteamApiError(f"Unknown error while creating contest '{contest_config.title}': {response_payload}")

        await self._build_retry_decorator()(perform_request)()
