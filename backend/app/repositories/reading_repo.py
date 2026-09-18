from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reading import Reading


class ReadingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_batch_idempotent(
        self, records: list[dict[str, Any]]
    ) -> tuple[int, int]:
        if not records:
            return 0, 0

        stmt = (
            insert(Reading)
            .values(records)
            .on_conflict_do_nothing(index_elements=["patient_id", "ts"])
        )
        res = await self.session.execute(stmt)
        await self.session.flush()

        accepted = res.rowcount if res.rowcount >= 0 else len(records)
        duplicates = max(0, len(records) - accepted)
        return accepted, duplicates

    async def get_readings_since(
        self, patient_id: uuid.UUID, since_ts: datetime
    ) -> Sequence[Reading]:
        stmt = (
            select(Reading)
            .where(Reading.patient_id == patient_id, Reading.ts >= since_ts)
            .order_by(Reading.ts.asc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_latest_reading(self, patient_id: uuid.UUID) -> Reading | None:
        stmt = (
            select(Reading)
            .where(Reading.patient_id == patient_id)
            .order_by(Reading.ts.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
