from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AddressBase(BaseModel):
    kind: Literal["home", "temporary", "work", "other"] = "home"
    region: str
    district: str
    mahalla: str | None = None
    street: str | None = None
    house: str | None = None
    flat: str | None = None
    landmark: str | None = None
    entrance_note: str | None = None
    lat: float | None = None
    lon: float | None = None
    geo_source: Literal["manual", "device_gps", "geocoded"] | None = None
    geo_accuracy_m: float | None = None
    is_primary: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    kind: Literal["home", "temporary", "work", "other"] | None = None
    region: str | None = None
    district: str | None = None
    mahalla: str | None = None
    street: str | None = None
    house: str | None = None
    flat: str | None = None
    landmark: str | None = None
    entrance_note: str | None = None
    lat: float | None = None
    lon: float | None = None
    geo_source: Literal["manual", "device_gps", "geocoded"] | None = None
    geo_accuracy_m: float | None = None
    is_primary: bool | None = None


class AddressItem(AddressBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ConditionBase(BaseModel):
    icd10: str
    name_uz: str
    name_ru: str | None = None
    kind: Literal["primary", "comorbidity", "past"] = "comorbidity"
    severity_note: str | None = None
    diagnosed_at: date | None = None
    is_active: bool = True


class ConditionCreate(ConditionBase):
    pass


class ConditionUpdate(BaseModel):
    icd10: str | None = None
    name_uz: str | None = None
    name_ru: str | None = None
    kind: Literal["primary", "comorbidity", "past"] | None = None
    severity_note: str | None = None
    diagnosed_at: date | None = None
    is_active: bool | None = None


class ConditionItem(ConditionBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    recorded_by: uuid.UUID | None = None
    created_at: datetime


class MedicationBase(BaseModel):
    name: str
    atc_code: str | None = None
    dose: str
    frequency: str
    route: str | None = "oral"
    started_at: date | None = None
    stopped_at: date | None = None
    stop_reason: str | None = None
    affects_params: dict[str, str] = Field(default_factory=dict)


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    name: str | None = None
    atc_code: str | None = None
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    started_at: date | None = None
    stopped_at: date | None = None
    stop_reason: str | None = None
    affects_params: dict[str, str] | None = None


class MedicationItem(MedicationBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    prescribed_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class AllergyBase(BaseModel):
    substance: str
    reaction: str | None = None
    severity: Literal["mild", "moderate", "severe", "anaphylaxis"] = "moderate"
    noted_at: date | None = None


class AllergyCreate(AllergyBase):
    pass


class AllergyItem(AllergyBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime


class MeasurementCreate(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    sbp_mmhg: int | None = None
    dbp_mmhg: int | None = None
    glucose_mmol: float | None = None
    source: str = "patient"
    note: str | None = None


class MeasurementItem(MeasurementCreate):
    id: int
    patient_id: uuid.UUID
    recorded_at: datetime
    bmi: float | None = None


class RiskFactorsUpdate(BaseModel):
    smoking: Literal["never", "former", "current"] | None = None
    smoking_pack_years: float | None = None
    alcohol: Literal["never", "occasional", "regular"] | None = None
    diabetes: bool | None = None
    hypertension: bool | None = None
    ckd: bool | None = None
    physical_activity: Literal["sedentary", "light", "moderate", "active"] | None = None
    lives_alone: bool | None = None
    mobility: Literal["independent", "assisted", "bedridden"] | None = None


class RiskFactorsItem(BaseModel):
    patient_id: uuid.UUID
    smoking: str | None = None
    smoking_pack_years: float | None = None
    alcohol: str | None = None
    diabetes: bool = False
    hypertension: bool = False
    ckd: bool = False
    physical_activity: str | None = None
    lives_alone: bool = False
    mobility: str | None = None
    updated_at: datetime


class AdmissionCreate(BaseModel):
    hospital_name: str
    department: str | None = None
    admitted_at: date
    discharged_at: date | None = None
    reason: str
    reason_icd10: str | None = None
    outcome: Literal["discharged", "transferred", "deceased", "ongoing"] = "discharged"
    was_readmission: bool = False
    discharge_summary: str | None = None


class AdmissionItem(AdmissionCreate):
    id: uuid.UUID
    patient_id: uuid.UUID
    predicted_by_alert_id: int | None = None
    created_at: datetime


class ProfileAuditItem(BaseModel):
    id: int
    patient_id: uuid.UUID
    actor_kind: str
    actor_id: uuid.UUID | None = None
    entity: str
    entity_id: str | None = None
    action: str
    changes: dict[str, Any]
    at: datetime
    request_id: str | None = None


class PatientProfilePatch(BaseModel):
    full_name: str | None = None
    birth_date: date | None = None
    sex: Literal["m", "f"] | None = None
    district: str | None = None
    phone: str | None = None
    telegram_chat_id: int | None = None
    primary_icd10: str | None = None
    blood_group: Literal["O", "A", "B", "AB"] | None = None
    rh: Literal["pos", "neg"] | None = None
    preferred_lang: Literal["uz", "ru", "en"] | None = None


class PatientFullProfile(BaseModel):
    id: uuid.UUID
    full_name: str
    age: int
    birth_date: date | None = None
    sex: Literal["m", "f"]
    diagnosis: str
    district: str
    phone: str | None = None
    primary_icd10: str | None = None
    blood_group: str | None = None
    rh: str | None = None
    preferred_lang: str = "uz"
    profile_completed_at: datetime | None = None

    primary_address: AddressItem | None = None
    addresses: list[AddressItem] = []
    conditions: list[ConditionItem] = []
    medications: list[MedicationItem] = []
    allergies: list[AllergyItem] = []
    measurements: list[MeasurementItem] = []
    risk_factors: RiskFactorsItem | None = None
    admissions: list[AdmissionItem] = []
