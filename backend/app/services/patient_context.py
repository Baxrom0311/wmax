from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from algo_interface import AlertLevel, BaselineEntry, Phase, ReadingVec
from app.models.address import PatientAddress
from app.models.admission import PatientAdmission
from app.models.alert import Alert
from app.models.allergy import PatientAllergy
from app.models.baseline import Baseline
from app.models.condition import PatientCondition
from app.models.measurement import PatientMeasurement
from app.models.medication import PatientMedication
from app.models.patient import Patient
from app.models.reading import Reading
from app.models.relative import Relative
from app.models.risk_factor import PatientRiskFactor
from app.models.task import Task
from app.schemas.profile import (
    AddressItem,
    AdmissionItem,
    AllergyItem,
    ConditionItem,
    MeasurementItem,
    MedicationItem,
    RiskFactorsItem,
)
from app.schemas.trend import Trend

# Python 3.11 f-string ifodasi ichida backslash qabul qilmaydi (PEP 701 faqat 3.12+).
UNKNOWN = "Noma'lum"



class EmergencyContactItem(BaseModel):
    id: uuid.UUID
    full_name: str
    relationship: str
    phone: str
    telegram_chat_id: int | None = None
    is_emergency_contact: bool = True
    contact_priority: int = 10


class PatientContext(BaseModel):
    """Unified read-model snapshot of a patient's complete digital twin context (Architecture V2 Section 8.1)."""

    # Identity
    patient_id: uuid.UUID
    full_name: str
    birth_date: date | None = None
    age: int | None = None
    sex: Literal["m", "f"]
    preferred_lang: str = "uz"

    # Clinical Profile
    conditions: list[ConditionItem] = Field(default_factory=list)
    medications: list[MedicationItem] = Field(default_factory=list)
    allergies: list[AllergyItem] = Field(default_factory=list)
    risk_factors: RiskFactorsItem | None = None
    blood_group: str | None = None
    rh: str | None = None
    latest_measurement: MeasurementItem | None = None
    weight_trend_14d: list[float] = Field(default_factory=list)

    # History
    admissions: list[AdmissionItem] = Field(default_factory=list)
    days_since_discharge: int | None = None
    readmission_count_12m: int = 0

    # Current telemetry state
    phase: Phase = "calib"
    level: AlertLevel = "green"
    composite_score: float = 0.0
    triggered_params: dict[str, float] = Field(default_factory=dict)
    trend: Trend = Field(
        default_factory=lambda: Trend(
            slope=0.0,
            direction="stable",
            recommendation_key="trend.stable",
            days_used=7,
        )
    )
    baselines: list[dict[str, Any]] = Field(default_factory=list)
    recent_vitals: dict[str, Any] = Field(default_factory=dict)
    open_alerts: list[dict[str, Any]] = Field(default_factory=list)
    open_tasks: list[dict[str, Any]] = Field(default_factory=list)

    # Location & Emergency Contacts
    primary_address: AddressItem | None = None
    emergency_contacts: list[EmergencyContactItem] = Field(default_factory=list)

    def for_ai(self) -> dict[str, Any]:
        """Comprehensive context payload structured for Gemini clinical twin prompt (Section 8.3)."""
        return self.model_dump()

    def for_dispatcher(self) -> dict[str, Any]:
        """Rapid-triage payload for emergency dispatchers: address, landmarks, blood, allergies, active meds."""
        return {
            "patient_id": str(self.patient_id),
            "full_name": self.full_name,
            "age": self.age,
            "sex": self.sex,
            "blood_group": f"{self.blood_group or UNKNOWN} ({self.rh or ''})".strip(),
            "primary_address": self.primary_address.model_dump() if self.primary_address else None,
            "allergies": [a.model_dump() for a in self.allergies],
            "active_medications": [m.model_dump() for m in self.medications if m.stopped_at is None],
            "primary_conditions": [c.model_dump() for c in self.conditions if c.kind == "primary"],
            "recent_vitals": self.recent_vitals,
            "emergency_contacts": [c.model_dump() for c in self.emergency_contacts],
        }

    def for_relative(self) -> dict[str, Any]:
        """Sanitized payload for family caregivers: removes raw clinical ICD codes and diagnostic jargons."""
        return {
            "patient_id": str(self.patient_id),
            "full_name": self.full_name,
            "level": self.level,
            "composite_score": self.composite_score,
            "recent_vitals": self.recent_vitals,
            "weight_trend": self.weight_trend_14d,
            "active_medications": [
                {"name": m.name, "dose": m.dose, "frequency": m.frequency}
                for m in self.medications
                if m.stopped_at is None
            ],
            "allergies": [a.substance for a in self.allergies],
            "open_tasks": self.open_tasks,
        }

    def for_patient(self) -> dict[str, Any]:
        """Patient portal payload: self-view with editable profile, medications schedule, and direct doctor details."""
        return self.model_dump()


class PatientContextBuilder:
    """Service assembling PatientContext by querying database tables in a single session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build(self, patient_id: uuid.UUID) -> PatientContext | None:
        patient = await self.session.get(Patient, patient_id)
        if not patient:
            return None

        # 1. Addresses
        addr_res = await self.session.execute(
            select(PatientAddress).where(PatientAddress.patient_id == patient_id).order_by(desc(PatientAddress.is_primary))
        )
        addresses = list(addr_res.scalars().all())
        primary_addr = next((a for a in addresses if a.is_primary), None) or (addresses[0] if addresses else None)
        primary_addr_item = AddressItem.model_validate(primary_addr, from_attributes=True) if primary_addr else None

        # 2. Conditions
        cond_res = await self.session.execute(
            select(PatientCondition).where(PatientCondition.patient_id == patient_id).order_by(desc(PatientCondition.is_active))
        )
        conditions = [ConditionItem.model_validate(c, from_attributes=True) for c in cond_res.scalars().all()]

        # 3. Medications
        med_res = await self.session.execute(
            select(PatientMedication).where(PatientMedication.patient_id == patient_id).order_by(desc(PatientMedication.created_at))
        )
        medications = [MedicationItem.model_validate(m, from_attributes=True) for m in med_res.scalars().all()]

        # 4. Allergies
        all_res = await self.session.execute(
            select(PatientAllergy).where(PatientAllergy.patient_id == patient_id)
        )
        allergies = [AllergyItem.model_validate(a, from_attributes=True) for a in all_res.scalars().all()]

        # 5. Measurements & 14d weight trend
        meas_res = await self.session.execute(
            select(PatientMeasurement)
            .where(PatientMeasurement.patient_id == patient_id)
            .order_by(desc(PatientMeasurement.recorded_at))
            .limit(30)
        )
        measurements = list(meas_res.scalars().all())
        latest_meas = MeasurementItem.model_validate(measurements[0], from_attributes=True) if measurements else None
        weight_trend = [m.weight_kg for m in measurements if m.weight_kg is not None][:14]
        weight_trend.reverse()

        # 6. Risk factors
        rf = await self.session.get(PatientRiskFactor, patient_id)
        risk_factors_item = RiskFactorsItem.model_validate(rf, from_attributes=True) if rf else None

        # 7. Admissions
        adm_res = await self.session.execute(
            select(PatientAdmission).where(PatientAdmission.patient_id == patient_id).order_by(desc(PatientAdmission.admitted_at))
        )
        admissions = [AdmissionItem.model_validate(a, from_attributes=True) for a in adm_res.scalars().all()]
        days_since_discharge = None
        if patient.discharge_date:
            days_since_discharge = (date.today() - patient.discharge_date).days
        year_ago = date.today() - timedelta(days=365)
        readmission_count = sum(1 for a in admissions if a.admitted_at >= year_ago)

        # 8. Relatives / Emergency Contacts
        rel_res = await self.session.execute(
            select(Relative).where(Relative.patient_id == patient_id).order_by(desc(Relative.is_emergency_contact), Relative.contact_priority)
        )
        relatives = list(rel_res.scalars().all())
        emergency_contacts = [
            EmergencyContactItem(
                id=r.id,
                full_name=r.full_name,
                relationship=r.relationship,
                phone=r.phone,
                telegram_chat_id=r.telegram_chat_id,
                is_emergency_contact=r.is_emergency_contact,
                contact_priority=r.contact_priority,
            )
            for r in relatives
        ]

        # 9. Latest telemetry reading & Alert
        read_res = await self.session.execute(
            select(Reading).where(Reading.patient_id == patient_id).order_by(desc(Reading.ts)).limit(1)
        )
        latest_reading = read_res.scalar_one_or_none()
        recent_vitals = {}
        if latest_reading:
            recent_vitals = {
                "ts": latest_reading.ts.isoformat(),
                "hr_mean": latest_reading.hr_mean,
                "spo2": latest_reading.spo2,
                "skin_temp": latest_reading.skin_temp,
                "steps": latest_reading.steps,
                "worn": latest_reading.worn,
                "battery": latest_reading.battery,
            }

        alert_res = await self.session.execute(
            select(Alert).where(Alert.patient_id == patient_id).order_by(desc(Alert.ts)).limit(5)
        )
        alerts = list(alert_res.scalars().all())
        latest_alert = alerts[0] if alerts else None
        current_level: AlertLevel = latest_alert.level if latest_alert else "green"
        composite_score = latest_alert.composite_score if latest_alert else 0.0
        triggered_params = latest_alert.triggered_params if latest_alert else {}

        # 10. Open tasks
        task_res = await self.session.execute(
            select(Task).where(Task.patient_id == patient_id, Task.status.in_(("created", "sent", "seen"))).order_by(Task.due_at)
        )
        tasks = list(task_res.scalars().all())

        # Age calculation
        calculated_age = patient.age
        if patient.birth_date:
            today = date.today()
            calculated_age = today.year - patient.birth_date.year - (
                (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
            )

        return PatientContext(
            patient_id=patient.id,
            full_name=patient.full_name,
            birth_date=patient.birth_date,
            age=calculated_age,
            sex=patient.sex,  # type: ignore[arg-type]
            preferred_lang=patient.preferred_lang,
            conditions=conditions,
            medications=medications,
            allergies=allergies,
            risk_factors=risk_factors_item,
            blood_group=patient.blood_group,
            rh=patient.rh,
            latest_measurement=latest_meas,
            weight_trend_14d=weight_trend,
            admissions=admissions,
            days_since_discharge=days_since_discharge,
            readmission_count_12m=readmission_count,
            phase=patient.phase,  # type: ignore[arg-type]
            level=current_level,
            composite_score=composite_score,
            triggered_params=triggered_params,
            recent_vitals=recent_vitals,
            open_alerts=[{"id": a.id, "level": a.level, "ts": a.ts.isoformat()} for a in alerts],
            open_tasks=[{"id": t.id, "type": t.type, "due_at": t.due_at.isoformat(), "status": t.status} for t in tasks],
            primary_address=primary_addr_item,
            emergency_contacts=emergency_contacts,
        )
