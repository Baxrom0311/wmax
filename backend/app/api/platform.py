from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_admin
from app.core.db import get_session
from app.models.audit import ProfileAudit
from app.models.patient import Patient

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


@router.get("/research/cohort", summary="Anonymized research cohort")
async def research_cohort(
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_admin),
) -> list[dict[str, Any]]:
    rows = (await session.execute(select(Patient).limit(limit))).scalars().all()
    return [
        {
            "patient_id": str(row.id),
            "birth_year": row.birth_date.year if row.birth_date else None,
            "sex": row.sex,
            "preferred_lang": row.preferred_lang,
            "deceased": row.deceased_at is not None,
        }
        for row in rows
    ]


@router.get("/support/patients/{id}", summary="Support access to full patient with mandatory reason")
async def support_patient(
    id: uuid.UUID,
    reason: str = Query(..., min_length=3),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    patient = await session.get(Patient, id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bemor topilmadi")
    audit = ProfileAudit(
        patient_id=id,
        actor_kind="platform_support",
        actor_id=current_user.id,
        entity="patient",
        entity_id=str(id),
        action="support_read",
        changes={"reason": reason},
    )
    session.add(audit)
    await session.flush()
    await session.commit()
    return {
        "id": str(patient.id),
        "full_name": patient.full_name,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "sex": patient.sex,
        "phone": patient.phone,
        "preferred_lang": patient.preferred_lang,
        "reason": reason,
    }


@router.get("/access-log", summary="Platform access audit log")
async def platform_access_log(
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_admin),
) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(ProfileAudit).where(ProfileAudit.actor_kind == "platform_support").order_by(ProfileAudit.at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": row.id,
            "patient_id": str(row.patient_id),
            "actor_id": str(row.actor_id) if row.actor_id else None,
            "action": row.action,
            "changes": row.changes,
            "at": row.at.isoformat(),
        }
        for row in rows
    ]
