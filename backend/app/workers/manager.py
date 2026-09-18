from __future__ import annotations

import asyncio
import logging

from app.workers.escalation_worker import run_escalation_worker
from app.workers.notification_worker import run_notification_worker

logger = logging.getLogger("nazorat.workers.manager")


class WorkerManager:
    """Manages asynchronous background tasks for the FastAPI application lifecycle."""

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []

    def start_workers(self) -> None:
        """Starts all background worker loops."""
        logger.info("Starting background worker services...")
        self._tasks.append(asyncio.create_task(run_escalation_worker(interval_seconds=60)))
        self._tasks.append(asyncio.create_task(run_notification_worker(interval_seconds=60)))
        logger.info("All background workers started successfully.")

    async def stop_workers(self) -> None:
        """Gracefully cancels and stops all background workers."""
        logger.info("Cancelling background worker services...")
        for task in self._tasks:
            task.cancel()

        results = await asyncio.gather(*self._tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
                logger.error("Worker raised exception during shutdown: %s", r)

        self._tasks.clear()
        logger.info("All background workers stopped.")


# Global instance
worker_manager = WorkerManager()
