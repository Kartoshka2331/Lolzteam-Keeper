import asyncio
import signal

from config import settings
from scheduler import TaskScheduler
from services import ContestService, ThreadService
from utils.logger import logger


async def run() -> None:
    logger.info("Starting application for thread bumping and contest creation")

    thread_service = ThreadService(settings)
    contest_service = ContestService(settings)
    task_scheduler = TaskScheduler(settings, thread_service, contest_service)

    shutdown_event = asyncio.Event()
    event_loop = asyncio.get_running_loop()

    for signal_number in (signal.SIGINT, signal.SIGTERM):
        try:
            event_loop.add_signal_handler(signal_number, shutdown_event.set)
        except NotImplementedError:
            signal.signal(signal_number, lambda handled_signal, frame: event_loop.call_soon_threadsafe(shutdown_event.set))

    task_scheduler.start()

    try:
        await shutdown_event.wait()
    finally:
        logger.info("Stopping application")
        task_scheduler.shutdown()


def main() -> None:
    try:
        asyncio.run(run())
    except Exception as error:
        logger.critical(f"Critical application error: {error}")
        raise


if __name__ == "__main__":
    main()
