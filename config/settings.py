from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_token: str = Field()
    api_base_url: str = Field(default="https://prod-api.zelenka.guru")
    api_request_timeout_seconds: float = Field(default=30.0)

    secret_answer: str = Field()

    thread_to_bump_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)
    thread_bump_delay_seconds: float = Field(default=3.0)
    thread_bump_cron_hour: str = Field(default="8,20")
    thread_bump_cron_minute: str = Field(default="0")

    contests_config_path: str = Field(default="contests.json")
    contest_creation_cron_day: str = Field(default="*/2")
    contest_creation_cron_hour: str = Field(default="17")
    contest_creation_cron_minute: str = Field(default="0")

    retry_max_attempts: int = Field(default=3)
    retry_wait_min_seconds: float = Field(default=4.0)
    retry_wait_max_seconds: float = Field(default=10.0)
    retry_wait_multiplier: float = Field(default=1.0)

    scheduler_timezone: str = Field(default="Europe/Moscow")

    log_level: str = Field(default="INFO")

    @field_validator("thread_to_bump_ids", mode="before")
    @classmethod
    def parse_thread_ids(cls, raw_value: object) -> list[int]:
        if isinstance(raw_value, str):
            return [int(item.strip()) for item in raw_value.split(",") if item.strip()]
        if isinstance(raw_value, list):
            return [int(item) for item in raw_value]
        return []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
