from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from algo_interface import AlertResult
from app.models.alert import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest(self, patient_id: uuid.UUID) -> Alert | None:
        stmt = (
            select(Alert)
            .where(Alert.patient_id == patient_id)
            .order_by(Alert.ts.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_recent(
        self, patient_id: uuid.UUID, limit: int = 20
    ) -> Sequence[Alert]:
        stmt = (
            select(Alert)
            .where(Alert.patient_id == patient_id)
            .order_by(Alert.ts.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def insert_idempotent(
        self, patient_id: uuid.UUID, ts: datetime, result: AlertResult
    ) -> Alert | None:
        stmt = (
            insert(Alert)
            .values(
                patient_id=patient_id,
                ts=ts,
                level=result.level,
                composite_score=result.composite_score,
                triggered_params=result.triggered_params,
                anomaly_score=result.anomaly_score,
                reason=result.reason,
            )
            .on_conflict_do_nothing(index_elements=["patient_id", "ts"])
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_latest(patient_id)
