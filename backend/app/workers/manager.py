from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.core.config import settings
from app.core.db import get_engine
from app.workers.escalation_worker import run_escalation_worker

logger = logging.getLogger("wmax.workers.manager")

LOCK_RETRY_SECONDS = 30


class WorkerManager:
    """Runs the background loops on exactly one API replica.

    The worker advances clinical state: it stamps active-call reminders,
    escalates overdue tasks, and raises `no_data` alerts for silent watches.
    Delivering those changes over Telegram is the notifier service's job.
    Running the worker on several replicas would double-escalate, so a Postgres
    session-level advisory lock elects a single leader;
    replicas that lose the election keep retrying and take over if the leader
    dies (the lock is released with its connection).
    """

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []
        self._leader_connection = None

    async def _acquire_leadership(self) -> bool:
        """Tries to take the advisory lock. Returns False if another replica holds it."""
        engine = get_engine()
        if engine.dialect.name != "postgresql":
            # SQLite (tests/local fallback) has no advisory locks and no second
            # replica to race against.
            return True

        try:
            connection = await engine.connect()
            result = await connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": settings.WORKER_LOCK_ID},
            )
            acquired = bool(result.scalar())
            if acquired:
                # Hold the connection: releasing it releases the lock.
                self._leader_connection = connection
            else:
                await connection.close()
            return acquired
        except Exception as err:
            logger.warning("Could not evaluate worker leadership: %s", err)
            return False

    async def _run_when_leader(self) -> None:
        """Waits for leadership, then supervises the worker loops."""
        while True:
            if await self._acquire_leadership():
                logger.info("Acquired worker leadership — starting background loops.")
                break
            logger.info(
                "Another replica owns the workers; retrying in %ds.", LOCK_RETRY_SECONDS
            )
            await asyncio.sleep(LOCK_RETRY_SECONDS)

        await run_escalation_worker(interval_seconds=60)

    def start_workers(self) -> None:
        """Starts the leader-election task unless workers are disabled."""
        if not settings.ENABLE_WORKERS:
            logger.info("Background workers disabled via ENABLE_WORKERS.")
            return

        logger.info("Starting background worker services...")
        self._tasks.append(asyncio.create_task(self._run_when_leader()))

    async def stop_workers(self) -> None:
        """Gracefully cancels the workers and releases the leadership lock."""
        if not self._tasks:
            return

        logger.info("Cancelling background worker services...")
        for task in self._tasks:
            task.cancel()

        results = await asyncio.gather(*self._tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
                logger.error("Worker raised exception during shutdown: %s", r)

        self._tasks.clear()

        if self._leader_connection is not None:
            try:
                await self._leader_connection.close()
            except Exception as err:  # pragma: no cover - shutdown best effort
                logger.warning("Failed to release worker advisory lock: %s", err)
            self._leader_connection = None

        logger.info("All background workers stopped.")


# Global instance
worker_manager = WorkerManager()
