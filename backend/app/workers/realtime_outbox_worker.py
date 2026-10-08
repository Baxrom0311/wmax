from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.db import get_db_context
from app.core.realtime import realtime_hub
from app.models import RealtimeEventOutbox

logger = logging.getLogger("wmax.workers.realtime_outbox")


async def dispatch_pending_events(limit: int = 100) -> int:
    """Publish only committed outbox rows; failures leave them retryable."""
    async with get_db_context() as session:
        result = await session.execute(
            select(RealtimeEventOutbox)
            .where(RealtimeEventOutbox.published_at.is_(None))
            .order_by(RealtimeEventOutbox.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        events = result.scalars().all()
        for event in events:
            await realtime_hub.publish(event.topic, event.payload, event_id=event.id)
            event.published_at = datetime.now(timezone.utc)
        return len(events)


async def run_realtime_outbox_worker(interval_seconds: int = 1) -> None:
    logger.info("Realtime outbox dispatcher started")
    while True:
        try:
            dispatched = await dispatch_pending_events()
            if not dispatched:
                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Realtime outbox dispatch failed; events remain pending")
            await asyncio.sleep(max(interval_seconds, 2))
