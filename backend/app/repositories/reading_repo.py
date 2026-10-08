from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_assignment import DeviceAssignment
from app.models.reading import OrphanReading, Reading


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
            .on_conflict_do_nothing(constraint="uq_reading_key")
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
            .where(Reading.patient_id == patient_id, Reading.window_start >= since_ts)
            .order_by(Reading.window_start.asc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_latest_reading(self, patient_id: uuid.UUID) -> Reading | None:
        stmt = (
            select(Reading)
            .where(Reading.patient_id == patient_id)
            .order_by(Reading.window_start.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_assignment_at(
        self, device_id: uuid.UUID, window_start: datetime
    ) -> DeviceAssignment | None:
        stmt = (
            select(DeviceAssignment)
            .where(
                DeviceAssignment.device_id == device_id,
                DeviceAssignment.assigned_at <= window_start,
                (
                    (DeviceAssignment.released_at.is_(None))
                    | (DeviceAssignment.released_at > window_start)
                ),
            )
            .order_by(DeviceAssignment.assigned_at.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_assignment_covering(
        self, device_id: uuid.UUID, start: datetime, end: datetime
    ) -> DeviceAssignment | None:
        """Return an assignment only when it owns the entire half-open interval."""
        release_bound = (
            DeviceAssignment.released_at >= end
            if end > start
            else DeviceAssignment.released_at > start
        )
        stmt = (
            select(DeviceAssignment)
            .where(
                DeviceAssignment.device_id == device_id,
                DeviceAssignment.assigned_at <= start,
                (DeviceAssignment.released_at.is_(None))
                | release_bound,
            )
            .order_by(DeviceAssignment.assigned_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_assignments_for_device_range(
        self,
        device_id: uuid.UUID,
        start: datetime,
        end: datetime,
    ) -> Sequence[DeviceAssignment]:
        stmt = (
            select(DeviceAssignment)
            .where(
                DeviceAssignment.device_id == device_id,
                DeviceAssignment.assigned_at <= end,
                or_(
                    DeviceAssignment.released_at.is_(None),
                    DeviceAssignment.released_at > start,
                ),
            )
            .order_by(DeviceAssignment.assigned_at.asc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def insert_orphan_idempotent(self, record: dict[str, Any]) -> bool:
        stmt = (
            insert(OrphanReading)
            .values(record)
            .on_conflict_do_nothing(constraint="uq_orphan_key")
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0
