import json
import random

from pydantic import ValidationError

from config import Settings
from models import ContestConfig
from services.api_client import LolzteamApiClient
from utils.logger import logger


class ContestService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _load_contest_configs(self) -> list[ContestConfig]:
        try:
            with open(self._settings.contests_config_path, encoding="utf-8") as contests_file:
                raw_contests = json.load(contests_file)
        except FileNotFoundError as file_not_found_error:
            logger.error(f"Contests config file not found at {self._settings.contests_config_path}: {file_not_found_error}")
            return []
        except json.JSONDecodeError as json_decode_error:
            logger.error(f"Failed to parse contests config at {self._settings.contests_config_path}: {json_decode_error}")
            return []

        try:
            return [ContestConfig.model_validate(raw_contest) for raw_contest in raw_contests]
        except ValidationError as validation_error:
            logger.error(f"Invalid contests config structure at {self._settings.contests_config_path}: {validation_error}")
            return []

    async def create_random_contest(self) -> None:
        contest_configs = self._load_contest_configs()
        if not contest_configs:
            logger.info("No valid contests configured for creation")
            return

        selected_contest = random.choice(contest_configs)
        async with LolzteamApiClient(self._settings) as api_client:
            try:
                await api_client.create_contest(selected_contest)
            except Exception as error:
                logger.error(f"Error while creating contest '{selected_contest.title}': {error}")
