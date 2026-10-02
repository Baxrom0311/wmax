from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PatientMembership


class PatientMembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_care_owner(self, patient_id: uuid.UUID) -> PatientMembership | None:
        res = await self.session.execute(
            select(PatientMembership).where(
                PatientMembership.patient_id == patient_id,
                PatientMembership.kind == "care",
                PatientMembership.revoked_at.is_(None),
            )
        )
        return res.scalar_one_or_none()

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[PatientMembership]:
        res = await self.session.execute(
            select(PatientMembership).where(
                PatientMembership.tenant_id == tenant_id,
                PatientMembership.revoked_at.is_(None),
            )
        )
        return list(res.scalars().all())

