import sys

from loguru import logger

from config import get_settings


def configure_logger() -> None:
    settings = get_settings()

    logger.remove()
    logger.add(sys.stdout, level=settings.log_level, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", enqueue=True)


configure_logger()


__all__ = [
    "configure_logger",
    "logger",
]
