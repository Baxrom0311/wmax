from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, Patient, PatientAccess


class PatientAccessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, access_id: uuid.UUID) -> PatientAccess | None:
        res = await self.session.execute(select(PatientAccess).where(PatientAccess.id == access_id))
        return res.scalar_one_or_none()

    async def get_by_account_and_patient(
        self, account_id: uuid.UUID, patient_id: uuid.UUID
    ) -> PatientAccess | None:
        res = await self.session.execute(
            select(PatientAccess).where(
                PatientAccess.account_id == account_id,
                PatientAccess.patient_id == patient_id,
                PatientAccess.revoked_at.is_(None),
            )
        )
        return res.scalar_one_or_none()

    async def get_assigned_patients_by_phone(
        self, phone: str
    ) -> list[tuple[PatientAccess, Patient, Account]]:
        stmt = (
            select(PatientAccess, Patient, Account)
            .join(Account, PatientAccess.account_id == Account.id)
            .join(Patient, PatientAccess.patient_id == Patient.id)
            .where(Account.phone == phone, PatientAccess.revoked_at.is_(None))
        )
        res = await self.session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in res.all()]

