from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.models.relative import Relative


class RelativeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_token(self, token: str) -> Relative | None:
        stmt = select(Relative).where(Relative.access_token == token)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Sequence[Relative]:
        stmt = select(Relative).where(Relative.phone == phone)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_assigned_patients(
        self, phone: str
    ) -> list[tuple[Relative, Patient]]:
        stmt = (
            select(Relative, Patient)
            .join(Patient, Relative.patient_id == Patient.id)
            .where(Relative.phone == phone)
        )
        res = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in res.all()]

    async def get_by_id_and_patient(
        self, relative_id: uuid.UUID, patient_id: uuid.UUID
    ) -> Relative | None:
        stmt = select(Relative).where(
            Relative.id == relative_id,
            Relative.patient_id == patient_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_access_token(
        self, relative: Relative, new_token: str
    ) -> Relative:
        from datetime import datetime, timezone
        relative.access_token = new_token
        relative.created_at = datetime.now(timezone.utc)
        self.session.add(relative)
        await self.session.flush()
        return relative

