from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from algo_interface import BaselineEntry
from app.models.baseline import Baseline


class BaselineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_patient(self, patient_id: uuid.UUID) -> Sequence[Baseline]:
        stmt = select(Baseline).where(Baseline.patient_id == patient_id)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def upsert_baselines(
        self, patient_id: uuid.UUID, entries: list[BaselineEntry]
    ) -> None:
        if not entries:
            return

        now = datetime.now(timezone.utc)
        for b in entries:
            stmt = (
                insert(Baseline)
                .values(
                    patient_id=patient_id,
                    param=b.param,
                    time_window=b.time_window,
                    median=b.median,
                    mad=b.mad,
                    n_samples=b.n_samples,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    index_elements=["patient_id", "param", "time_window"],
                    set_={
                        "median": b.median,
                        "mad": b.mad,
                        "n_samples": b.n_samples,
                        "updated_at": now,
                    },
                )
            )
            await self.session.execute(stmt)
        await self.session.flush()
