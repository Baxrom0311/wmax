from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, patient_id: uuid.UUID) -> Patient | None:
        stmt = select(Patient).where(Patient.id == patient_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Patient | None:
        stmt = select(Patient).where(Patient.phone == phone)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_all(
        self, district: str | None = None
    ) -> Sequence[Patient]:
        stmt = select(Patient)
        if district:
            stmt = stmt.where(Patient.district == district)
        stmt = stmt.order_by(Patient.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def set_discharge_date(
        self, patient_id: uuid.UUID, discharge_date: date
    ) -> Patient | None:
        patient = await self.get_by_id(patient_id)
        if patient:
            patient.discharge_date = discharge_date
            await self.session.flush()
        return patient

    async def approve_baseline(
        self, patient_id: uuid.UUID, doctor_id: uuid.UUID, approved_at: datetime
    ) -> Patient | None:
        patient = await self.get_by_id(patient_id)
        if patient:
            patient.phase = "full"
            patient.baseline_approved_by = doctor_id
            patient.baseline_approved_at = approved_at
            await self.session.flush()
        return patient
