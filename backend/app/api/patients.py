from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician, require_doctor
from app.auth.scope import assert_patient_access
from app.core.db import get_session
from app.core.exceptions import ForbiddenException, ValidationException
from app.models import PatientConsent, PatientMembership
from app.models.baseline import Baseline
from app.models.patient import Patient
from app.models.reading import Reading
from app.schemas.common import AlertLevel
from app.schemas.patient import PatientDetail, PatientSummary
from app.schemas.task import Task as TaskSchema
from app.services.patient_relationship_service import PatientRelationshipService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


class PatientCreateRequest(BaseModel):
    full_name: str
    tenant_id: uuid.UUID | None = None
    birth_date: date | None = None
    sex: str | None = Field(None, pattern="^[mf]$")
    phone: str | None = None
    jshshir: str | None = None
    preferred_lang: str = "uz"


class PatientPatchRequest(BaseModel):
    full_name: str | None = None
    birth_date: date | None = None
    sex: str | None = Field(None, pattern="^[mf]$")
    phone: str | None = None
    jshshir: str | None = None
    preferred_lang: str | None = None


class MembershipCreateRequest(BaseModel):
    tenant_id: uuid.UUID
    kind: Literal["care"] = "care"


class BaselineDecisionRequest(BaseModel):
    decision: str


class AccessInviteRequest(BaseModel):
    phone: str
    full_name: str
    relation: str | None = None
    role: Literal["payer", "caregiver"] = "caregiver"


class AccessAcceptRequest(BaseModel):
    access_id: uuid.UUID


class ConsentCreateRequest(BaseModel):
    scope: Literal["family_access", "clinical_monitoring"]
    granted: bool = True
    method: Literal["sms", "in_app", "verbal_by_clinician"] = "verbal_by_clinician"
    target_account_id: uuid.UUID | None = None
    target_tenant_id: uuid.UUID | None = None


def _patient_dict(patient: Patient) -> dict[str, Any]:
    return {
        "id": str(patient.id),
        "full_name": patient.full_name,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "sex": patient.sex,
        "phone": patient.phone,
        "jshshir": patient.jshshir,
        "preferred_lang": patient.preferred_lang,
        "deceased_at": patient.deceased_at.isoformat() if patient.deceased_at else None,
    }


def _assert_tenant_scope(current_user: CurrentUser, tenant_id: uuid.UUID) -> None:
    if current_user.role == "admin":
        return
    if tenant_id not in current_user.tenant_ids:
        raise ForbiddenException("Bu klinika bo'yicha amal bajarish huquqi yo'q")


def _resolve_create_tenant(current_user: CurrentUser, tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is not None:
        _assert_tenant_scope(current_user, tenant_id)
        return tenant_id
    if len(current_user.tenant_ids) == 1:
        return current_user.tenant_ids[0]
    raise ValidationException("Bemor yaratish uchun tenant_id talab qilinadi")


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
    tenant_ids = None if current_user.role == "admin" else current_user.tenant_ids
    return await service.get_worklist(district=district, level=level, clinician_tenant_ids=tenant_ids)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new patient")
async def create_patient(
    req: PatientCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    tenant_id = _resolve_create_tenant(current_user, req.tenant_id)
    patient_data = req.model_dump(exclude={"tenant_id"}, exclude_none=True)
    patient = Patient(**patient_data)
    session.add(patient)
    await session.flush()
    await PatientRelationshipService(session).create_membership(
        patient_id=patient.id,
        tenant_id=tenant_id,
        kind="care",
        granted_by=current_user.id,
    )
    return _patient_dict(patient)


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
    await assert_patient_access(session, current_user, id)
    service = PatientService(session)
    return await service.get_patient_detail(id, days=days)


@router.patch("/{id}", summary="Patch patient profile")
async def patch_patient(
    id: uuid.UUID,
    req: PatientPatchRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    await assert_patient_access(session, current_user, id)
    patient = await session.get(Patient, id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bemor topilmadi")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    await session.flush()
    await session.commit()
    return _patient_dict(patient)


@router.get("/{id}/timeline", summary="Patient event timeline")
async def patient_timeline(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    await assert_patient_access(session, current_user, id)
    alerts = (await session.execute(select(Reading).where(Reading.patient_id == id).order_by(Reading.window_start.desc()).limit(20))).scalars().all()
    return [
        {
            "kind": "reading",
            "ts": item.window_start.isoformat(),
            "payload": {"hr_mean": item.hr_mean, "worn": item.worn, "battery": item.battery},
        }
        for item in alerts
    ]


@router.get("/{id}/readings", summary="Patient readings")
async def patient_readings(
    id: uuid.UUID,
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    await assert_patient_access(session, current_user, id)
    rows = (
        await session.execute(
            select(Reading).where(Reading.patient_id == id).order_by(Reading.window_start.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "window_start": row.window_start.isoformat(),
            "window_end": row.window_end.isoformat(),
            "hr_mean": row.hr_mean,
            "hr_min": row.hr_min,
            "hr_max": row.hr_max,
            "rmssd": row.rmssd,
            "worn": row.worn,
            "worn_pct": row.worn_pct,
            "samples_n": row.samples_n,
            "battery": row.battery,
        }
        for row in rows
    ]


@router.get("/{id}/baseline", summary="Current patient baseline")
async def patient_baseline(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    await assert_patient_access(session, current_user, id)
    rows = (
        await session.execute(select(Baseline).where(Baseline.patient_id == id).order_by(Baseline.param, Baseline.time_window))
    ).scalars().all()
    return [
        {
            "param": row.param,
            "time_window": row.time_window,
            "median": row.median,
            "mad": row.mad,
            "n_samples": row.n_samples,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
        }
        for row in rows
    ]


@router.post("/{id}/baseline/approve", summary="Doctor approves personal baseline")
async def approve_baseline_contract(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_doctor),
) -> dict[str, str]:
    return await approve_baseline(id, session, current_user)


@router.post("/{id}/deceased", summary="Mark patient deceased")
async def mark_deceased(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_doctor),
) -> dict[str, Any]:
    await assert_patient_access(session, current_user, id)
    patient = await session.get(Patient, id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bemor topilmadi")
    patient.deceased_at = datetime.now(timezone.utc)
    patient.deceased_marked_by = current_user.id
    await session.flush()
    await session.commit()
    return _patient_dict(patient)


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
    await assert_patient_access(session, current_user, id)
    service = PatientService(session)
    return await service.discharge_patient(
        id,
        doctor_id=current_user.id,
        clinician_tenant_ids=current_user.tenant_ids,
    )


@router.post(
    "/{id}/approve-baseline",
    summary="Doctor approves personal baseline — transitions patient from learning to full phase.",
)
async def approve_baseline(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_doctor),
) -> dict[str, str]:
    await assert_patient_access(session, current_user, id)
    service = PatientService(session)
    await service.approve_baseline(id, approved_by=current_user.id)
    return {"detail": "Shaxsiy baza muvaffaqiyatli tasdiqlandi"}


@router.post("/{id}/memberships", status_code=status.HTTP_201_CREATED, summary="Admit patient to a clinic")
async def create_membership(
    id: uuid.UUID,
    req: MembershipCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    _assert_tenant_scope(current_user, req.tenant_id)
    return await PatientRelationshipService(session).create_membership(
        patient_id=id,
        tenant_id=req.tenant_id,
        kind=req.kind,
        granted_by=current_user.id,
    )


@router.delete("/{id}/memberships/{mid}", summary="Revoke patient clinic membership")
async def revoke_membership(
    id: uuid.UUID,
    mid: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    membership = await session.get(PatientMembership, mid)
    if not membership or membership.patient_id != id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="A'zolik topilmadi")
    _assert_tenant_scope(current_user, membership.tenant_id)
    return await PatientRelationshipService(session).revoke_membership(
        patient_id=id,
        membership_id=mid,
    )


@router.post("/{id}/memberships/{mid}/baseline-decision", summary="Record baseline ownership decision")
async def membership_baseline_decision(
    id: uuid.UUID,
    mid: uuid.UUID,
    req: BaselineDecisionRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    membership = await session.get(PatientMembership, mid)
    if not membership or membership.patient_id != id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="A'zolik topilmadi")
    _assert_tenant_scope(current_user, membership.tenant_id)
    membership.baseline_decision = req.decision
    await session.flush()
    await session.commit()
    return {"id": str(mid), "baseline_decision": membership.baseline_decision}


@router.post("/{id}/access/invite", status_code=status.HTTP_201_CREATED, summary="Invite caregiver access")
async def invite_access(
    id: uuid.UUID,
    req: AccessInviteRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    await assert_patient_access(session, current_user, id)
    return await PatientRelationshipService(session).invite_access(
        patient_id=id,
        phone=req.phone,
        full_name=req.full_name,
        role=req.role,
        relation=req.relation,
        invited_by=current_user.id,
    )


@router.delete("/{id}/access/{aid}", summary="Revoke caregiver access")
async def revoke_access(
    id: uuid.UUID,
    aid: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    await assert_patient_access(session, current_user, id)
    return await PatientRelationshipService(session).revoke_access(
        patient_id=id,
        access_id=aid,
    )


@router.get("/{id}/consents", summary="List patient consents")
async def list_consents(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    await assert_patient_access(session, current_user, id)
    rows = (await session.execute(select(PatientConsent).where(PatientConsent.patient_id == id))).scalars().all()
    return [
        {
            "id": str(row.id),
            "scope": row.scope,
            "granted": row.granted,
            "method": row.method,
            "recorded_at": row.recorded_at.isoformat(),
            "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
        }
        for row in rows
    ]


@router.post("/{id}/consents", status_code=status.HTTP_201_CREATED, summary="Record patient consent")
async def create_consent(
    id: uuid.UUID,
    req: ConsentCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    await assert_patient_access(session, current_user, id)
    if req.target_tenant_id is not None:
        _assert_tenant_scope(current_user, req.target_tenant_id)
    return await PatientRelationshipService(session).create_consent(
        patient_id=id,
        scope=req.scope,
        granted=req.granted,
        method=req.method,
        witnessed_by=current_user.id,
        target_account_id=req.target_account_id,
        target_tenant_id=req.target_tenant_id,
    )


@router.post("/{id}/consents/{cid}/revoke", summary="Revoke patient consent")
async def revoke_consent(
    id: uuid.UUID,
    cid: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    await assert_patient_access(session, current_user, id)
    return await PatientRelationshipService(session).revoke_consent(
        patient_id=id,
        consent_id=cid,
    )


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
    await assert_patient_access(session, current_user, id)
    service = PatientService(session)
    return await service.rotate_relative_token(id, relative_id)
