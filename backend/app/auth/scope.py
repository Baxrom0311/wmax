from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models import PatientMembership
from app.models.patient import Patient
from app.schemas.auth import CurrentUser


async def assert_patient_access(
    session: AsyncSession,
    principal: CurrentUser,
    patient_id: uuid.UUID,
) -> None:
    if principal.role == "admin":
        return
    if principal.role == "patient":
        if principal.id != patient_id:
            raise ForbiddenException("Bemor faqat o'z profiliga kirish huquqiga ega")
        return
    if principal.role == "relative":
        if patient_id not in principal.patient_ids:
            raise ForbiddenException("Bu bemor profiliga ruxsat yo'q")
        return

    patient = await session.get(Patient, patient_id)
    if not patient:
        raise NotFoundException("Bemor topilmadi")
    if not principal.tenant_ids:
        raise ForbiddenException("Bu bemor bo'yicha amal bajarish huquqi yo'q")

    membership_id = (
        await session.execute(
            select(PatientMembership.id).where(
                PatientMembership.patient_id == patient_id,
                PatientMembership.tenant_id.in_(principal.tenant_ids),
                PatientMembership.revoked_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if membership_id is None:
        raise ForbiddenException("Bu bemor bo'yicha amal bajarish huquqi yo'q")
