from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician, require_doctor
from app.core.db import get_session
from app.schemas.common import AlertLevel
from app.schemas.patient import PatientDetail, PatientSummary
from app.schemas.task import Task as TaskSchema
from app.services.patient_service import PatientService

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


@router.get(
    "",
    response_model=list[PatientSummary],
    summary="Worklist sorted by acuity: red > no_data > amber > green.",
)
async def list_patients(
    district: str | None = Query(None, description="Filter by district"),
    level: AlertLevel | None = Query(None, description="Filter by alert level"),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[PatientSummary]:
    service = PatientService(session)
    return await service.get_worklist(district=district, level=level)


@router.get(
    "/{id}",
    response_model=PatientDetail,
    summary="Patient detail with multi-param series, baselines, trend, and prognosis.",
)
async def get_patient_detail(
    id: uuid.UUID,
    days: int = Query(7, ge=1, le=30, description="History window in days"),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> PatientDetail:
    service = PatientService(session)
    return await service.get_patient_detail(id, days=days)


@router.post(
    "/{id}/discharge",
    response_model=TaskSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Discharge patient and create 24h active-call follow-up task.",
)
async def discharge_patient(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_doctor),
) -> TaskSchema:
    service = PatientService(session)
    return await service.discharge_patient(id, doctor_id=current_user.id)


@router.post(
    "/{id}/approve-baseline",
    summary="Doctor approves personal baseline — transitions patient from learning to full phase.",
)
async def approve_baseline(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_doctor),
) -> dict[str, str]:
    service = PatientService(session)
    await service.approve_baseline(id, approved_by=current_user.id)
    return {"detail": "Shaxsiy baza muvaffaqiyatli tasdiqlandi"}


@router.post(
    "/{id}/relatives/{relative_id}/rotate-token",
    summary="Doctor rotates caregiver access token (R13).",
)
async def rotate_relative_token(
    id: uuid.UUID,
    relative_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_doctor),
) -> dict[str, str]:
    service = PatientService(session)
    return await service.rotate_relative_token(id, relative_id)

