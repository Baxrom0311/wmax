from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import (
    CurrentUser,
    get_current_principal,
    require_clinician,
    require_doctor,
)
from app.auth.field_policy import assert_can_edit_entity
from app.core.db import get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.security import hash_password
from app.models.patient import Patient
from app.repositories.profile_repo import ProfileRepository
from app.schemas.profile import (
    AddressCreate,
    AddressItem,
    AddressUpdate,
    AdmissionCreate,
    AdmissionItem,
    AllergyCreate,
    AllergyItem,
    ConditionCreate,
    ConditionItem,
    ConditionUpdate,
    MeasurementCreate,
    MeasurementItem,
    MedicationCreate,
    MedicationItem,
    MedicationUpdate,
    PatientFullProfile,
    PatientProfilePatch,
    ProfileAuditItem,
    RiskFactorsItem,
    RiskFactorsUpdate,
)
from app.services.patient_context import PatientContext, PatientContextBuilder

router = APIRouter(prefix="/api/v1/patients/{id}", tags=["profile"])


def _verify_patient_access(patient_id: uuid.UUID, principal: CurrentUser) -> None:
    """Verifies that non-clinicians (patients, caregivers) only access authorized patient records."""
    if principal.role == "patient" and principal.id != patient_id:
        raise ForbiddenException("Bemor faqat o'z profiliga kirish huquqiga ega")


@router.get(
    "/profile",
    response_model=PatientFullProfile,
    summary="Get comprehensive patient clinical profile",
)
async def get_patient_profile(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    patient = await db.get(Patient, id)
    if not patient:
        raise NotFoundException("Bemor topilmadi")

    addresses = await repo.list_addresses(id)
    primary_addr = next((a for a in addresses if a.is_primary), None) or (addresses[0] if addresses else None)
    conditions = await repo.list_conditions(id)
    medications = await repo.list_medications(id)
    allergies = await repo.list_allergies(id)
    measurements = await repo.list_measurements(id)
    risk_factors = await repo.get_risk_factors(id)
    admissions = await repo.list_admissions(id)

    return PatientFullProfile(
        id=patient.id,
        full_name=patient.full_name,
        age=patient.age,
        birth_date=patient.birth_date,
        sex=patient.sex,  # type: ignore[arg-type]
        diagnosis=patient.diagnosis,
        district=patient.district,
        phone=patient.phone,
        primary_icd10=patient.primary_icd10,
        blood_group=patient.blood_group,
        rh=patient.rh,
        preferred_lang=patient.preferred_lang,
        profile_completed_at=patient.profile_completed_at,
        primary_address=AddressItem.model_validate(primary_addr, from_attributes=True) if primary_addr else None,
        addresses=[AddressItem.model_validate(a, from_attributes=True) for a in addresses],
        conditions=[ConditionItem.model_validate(c, from_attributes=True) for c in conditions],
        medications=[MedicationItem.model_validate(m, from_attributes=True) for m in medications],
        allergies=[AllergyItem.model_validate(a, from_attributes=True) for a in allergies],
        measurements=[MeasurementItem.model_validate(m, from_attributes=True) for m in measurements],
        risk_factors=RiskFactorsItem.model_validate(risk_factors, from_attributes=True) if risk_factors else None,
        admissions=[AdmissionItem.model_validate(a, from_attributes=True) for a in admissions],
    )


@router.patch(
    "/profile",
    response_model=PatientFullProfile,
    summary="Update basic patient profile fields with field-level RBAC",
)
async def patch_patient_profile(
    id: uuid.UUID,
    req: PatientProfilePatch,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    assert_can_edit_entity("contact", principal)

    repo = ProfileRepository(db)
    patient = await db.get(Patient, id)
    if not patient:
        raise NotFoundException("Bemor topilmadi")

    changes = req.model_dump(exclude_unset=True)
    if changes:
        await repo.update_with_audit(patient, changes, principal, id)
        await db.commit()
        await db.refresh(patient)

    return await get_patient_profile(id, principal, db)


# Addresses
@router.get("/addresses", response_model=list[AddressItem])
async def list_addresses(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    return await repo.list_addresses(id)


@router.post("/addresses", response_model=AddressItem, status_code=status.HTTP_201_CREATED)
async def create_address(
    id: uuid.UUID,
    req: AddressCreate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    assert_can_edit_entity("address", principal)
    repo = ProfileRepository(db)
    addr = await repo.create_address(id, req.model_dump(), principal)
    await db.commit()
    await db.refresh(addr)
    return addr


@router.patch("/addresses/{aid}", response_model=AddressItem)
async def update_address(
    id: uuid.UUID,
    aid: uuid.UUID,
    req: AddressUpdate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    assert_can_edit_entity("address", principal)
    repo = ProfileRepository(db)
    addr = await repo.get_address(aid, id)
    if not addr:
        raise NotFoundException("Manzil topilmadi")

    changes = req.model_dump(exclude_unset=True)
    if changes:
        await repo.update_with_audit(addr, changes, principal, id)
        await db.commit()
        await db.refresh(addr)
    return addr


# response_model=None is required: `from __future__ import annotations`
# turns the `-> None` return annotation into the string "None", which
# FastAPI otherwise treats as a response model and rejects on a 204.
@router.delete(
    "/addresses/{aid}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_address(
    id: uuid.UUID,
    aid: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> None:
    _verify_patient_access(id, principal)
    assert_can_edit_entity("address", principal)
    repo = ProfileRepository(db)
    success = await repo.delete_address(aid, id, principal)
    if not success:
        raise NotFoundException("Manzil topilmadi")
    await db.commit()


@router.post("/addresses/{aid}/set-primary", response_model=AddressItem)
async def set_primary_address(
    id: uuid.UUID,
    aid: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    assert_can_edit_entity("address", principal)
    repo = ProfileRepository(db)
    addr = await repo.set_primary_address(aid, id, principal)
    if not addr:
        raise NotFoundException("Manzil topilmadi")
    await db.commit()
    await db.refresh(addr)
    return addr


# Conditions
@router.get("/conditions", response_model=list[ConditionItem])
async def list_conditions(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    return await repo.list_conditions(id)


@router.post("/conditions", response_model=ConditionItem, status_code=status.HTTP_201_CREATED)
async def create_condition(
    id: uuid.UUID,
    req: ConditionCreate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    assert_can_edit_entity("condition", principal)
    repo = ProfileRepository(db)
    cond = await repo.create_condition(id, req.model_dump(), principal)
    await db.commit()
    await db.refresh(cond)
    return cond


# Medications
@router.get("/medications", response_model=list[MedicationItem])
async def list_medications(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    return await repo.list_medications(id)


@router.post("/medications", response_model=MedicationItem, status_code=status.HTTP_201_CREATED)
async def create_medication(
    id: uuid.UUID,
    req: MedicationCreate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    assert_can_edit_entity("medication", principal)
    repo = ProfileRepository(db)
    med = await repo.create_medication(id, req.model_dump(), principal)
    await db.commit()
    await db.refresh(med)
    return med


@router.patch("/medications/{mid}", response_model=MedicationItem)
async def update_medication(
    id: uuid.UUID,
    mid: uuid.UUID,
    req: MedicationUpdate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    assert_can_edit_entity("medication", principal)
    repo = ProfileRepository(db)
    med = await repo.get_medication(mid, id)
    if not med:
        raise NotFoundException("Dori topilmadi")

    changes = req.model_dump(exclude_unset=True)
    if changes:
        await repo.update_with_audit(med, changes, principal, id)
        await db.commit()
        await db.refresh(med)
    return med


# Allergies
@router.get("/allergies", response_model=list[AllergyItem])
async def list_allergies(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    return await repo.list_allergies(id)


@router.post("/allergies", response_model=AllergyItem, status_code=status.HTTP_201_CREATED)
async def create_allergy(
    id: uuid.UUID,
    req: AllergyCreate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    assert_can_edit_entity("allergy", principal)
    repo = ProfileRepository(db)
    allergy = await repo.create_allergy(id, req.model_dump(), principal)
    await db.commit()
    await db.refresh(allergy)
    return allergy


# Measurements
@router.get("/measurements", response_model=list[MeasurementItem])
async def list_measurements(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    return await repo.list_measurements(id)


@router.post("/measurements", response_model=MeasurementItem, status_code=status.HTTP_201_CREATED)
async def create_measurement(
    id: uuid.UUID,
    req: MeasurementCreate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    assert_can_edit_entity("measurement", principal)
    repo = ProfileRepository(db)
    meas = await repo.create_measurement(id, req.model_dump(), principal)
    await db.commit()
    await db.refresh(meas)
    return meas


# Risk factors
@router.get("/risk-factors", response_model=RiskFactorsItem | None)
async def get_risk_factors(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    return await repo.get_risk_factors(id)


@router.put("/risk-factors", response_model=RiskFactorsItem)
async def put_risk_factors(
    id: uuid.UUID,
    req: RiskFactorsUpdate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    assert_can_edit_entity("risk_factors", principal)
    repo = ProfileRepository(db)
    rf = await repo.upsert_risk_factors(id, req.model_dump(exclude_unset=True), principal)
    await db.commit()
    await db.refresh(rf)
    return rf


# Admissions
@router.get("/admissions", response_model=list[AdmissionItem])
async def list_admissions(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    _verify_patient_access(id, principal)
    repo = ProfileRepository(db)
    return await repo.list_admissions(id)


@router.post("/admissions", response_model=AdmissionItem, status_code=status.HTTP_201_CREATED)
async def create_admission(
    id: uuid.UUID,
    req: AdmissionCreate,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    assert_can_edit_entity("admission", principal)
    repo = ProfileRepository(db)
    adm = await repo.create_admission(id, req.model_dump(), principal)
    await db.commit()
    await db.refresh(adm)
    return adm


# Audit
@router.get("/audit", response_model=list[ProfileAuditItem])
async def get_audit_trail(
    id: uuid.UUID,
    doctor: CurrentUser = Depends(require_doctor),
    db: AsyncSession = Depends(get_session),
) -> Any:
    repo = ProfileRepository(db)
    return await repo.list_audit_entries(id)


# Digital Twin
@router.get("/twin", response_model=PatientContext)
async def get_patient_digital_twin(
    id: uuid.UUID,
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> Any:
    builder = PatientContextBuilder(db)
    ctx = await builder.build(id)
    if not ctx:
        raise NotFoundException("Bemor topilmadi")
    return ctx


class PinResetRequest(BaseModel):
    new_pin: str


@router.post("/reset-pin")
async def reset_patient_pin(
    id: uuid.UUID,
    req: PinResetRequest,
    doctor: CurrentUser = Depends(require_doctor),
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    if len(req.new_pin.strip()) < 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PIN kamida 4 xonali bo'lishi shart",
        )
    patient = await db.get(Patient, id)
    if not patient:
        raise NotFoundException("Bemor topilmadi")

    patient.pin_hash = hash_password(req.new_pin.strip())
    await db.commit()
    return {"message": "Bemorning yangi PIN kodi muvaffaqiyatli o'rnatildi"}
