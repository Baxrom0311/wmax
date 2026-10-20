from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clinical_scope import clinician_patient_ids
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models import PatientAccess, PatientConsent
from app.models.patient import Patient
from app.services.monitoring_policy import family_history_visible
from app.schemas.auth import CurrentUser


async def assert_patient_access(
    session: AsyncSession,
    principal: CurrentUser,
    patient_id: uuid.UUID,
) -> None:
    if principal.role == "patient":
        if principal.id != patient_id:
            raise ForbiddenException("Bemor faqat o'z profiliga kirish huquqiga ega")
        return
    if principal.role == "relative":
        allowed = (
            await session.execute(
                select(PatientAccess.id)
                .join(PatientConsent, PatientConsent.patient_id == PatientAccess.patient_id)
                .join(Patient, Patient.id == PatientAccess.patient_id)
                .where(
                    family_history_visible(),
                    PatientAccess.patient_id == patient_id,
                    PatientAccess.account_id == principal.id,
                    PatientAccess.accepted_at.is_not(None),
                    PatientAccess.revoked_at.is_(None),
                    PatientConsent.scope == "family_access",
                    PatientConsent.granted.is_(True),
                    PatientConsent.revoked_at.is_(None),
                    PatientConsent.target_account_id == principal.id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if allowed is None:
            raise ForbiddenException("Bu bemor profiliga ruxsat yo'q")
        return

    patient = await session.get(Patient, patient_id)
    if not patient:
        raise NotFoundException("Bemor topilmadi")
    if not principal.tenant_ids:
        raise ForbiddenException("Bu bemor bo'yicha amal bajarish huquqi yo'q")

    allowed = (await session.execute(
        select(Patient.id).where(
            Patient.id == patient_id,
            Patient.id.in_(clinician_patient_ids(principal.id, principal.tenant_ids)),
        )
    )).scalar_one_or_none()
    if allowed is None:
        raise ForbiddenException("Bu bemor bo'yicha amal bajarish huquqi yo'q")
