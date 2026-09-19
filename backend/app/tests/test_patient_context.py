from __future__ import annotations

import uuid
from datetime import datetime, timezone
from app.schemas.profile import (
    AddressItem,
    AllergyItem,
    ConditionItem,
    MedicationItem,
    RiskFactorsItem,
)
from app.services.patient_context import PatientContext, EmergencyContactItem


def test_patient_context_for_dispatcher():
    patient_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    ctx = PatientContext(
        patient_id=patient_id,
        full_name="Bemor Eshmatov",
        sex="m",
        age=65,
        blood_group="A",
        rh="pos",
        primary_address=AddressItem(
            id=uuid.uuid4(),
            patient_id=patient_id,
            region="Xorazm",
            district="Urganch sh.",
            street="Al-Xorazmiy",
            landmark="GUM ro'parasi",
            entrance_note="2-podyezd",
            created_at=now,
            updated_at=now,
        ),
        conditions=[
            ConditionItem(
                id=uuid.uuid4(),
                patient_id=patient_id,
                name_uz="Yurak ishemik kasalligi",
                icd10="I25.1",
                kind="primary",
                created_at=now,
            ),
            ConditionItem(
                id=uuid.uuid4(),
                patient_id=patient_id,
                name_uz="Gipertoniya",
                icd10="I10",
                kind="comorbidity",
                created_at=now,
            ),
        ],
        medications=[
            MedicationItem(
                id=uuid.uuid4(),
                patient_id=patient_id,
                name="Bisoprolol",
                dose="5mg",
                frequency="1 maxal",
                affects_params={"hr": "lowers"},
                created_at=now,
                updated_at=now,
            ),
        ],
        allergies=[
            AllergyItem(
                id=uuid.uuid4(),
                patient_id=patient_id,
                substance="Penitsillin",
                reaction="Anafilaksiya",
                severity="severe",
                created_at=now,
            ),
        ],
        emergency_contacts=[
            EmergencyContactItem(
                id=uuid.uuid4(),
                full_name="Vali Eshmatov",
                relationship="O'g'li",
                phone="+998901112233",
            ),
        ],
    )

    disp = ctx.for_dispatcher()
    assert disp["full_name"] == "Bemor Eshmatov"
    assert disp["blood_group"] == "A (pos)"
    assert disp["primary_address"]["landmark"] == "GUM ro'parasi"
    assert len(disp["allergies"]) == 1
    assert disp["allergies"][0]["substance"] == "Penitsillin"
    assert len(disp["active_medications"]) == 1
    assert len(disp["emergency_contacts"]) == 1


def test_patient_context_for_relative_sanitizes_icd_and_diagnosis():
    patient_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    ctx = PatientContext(
        patient_id=patient_id,
        full_name="Bemor Eshmatov",
        sex="m",
        age=65,
        level="amber",
        composite_score=1.85,
        conditions=[
            ConditionItem(
                id=uuid.uuid4(),
                patient_id=patient_id,
                name_uz="Yurak ishemik kasalligi",
                icd10="I25.1",
                kind="primary",
                created_at=now,
            ),
        ],
        medications=[
            MedicationItem(
                id=uuid.uuid4(),
                patient_id=patient_id,
                name="Bisoprolol",
                dose="5mg",
                frequency="1 maxal",
                created_at=now,
                updated_at=now,
            ),
        ],
        weight_trend_14d=[70.0, 71.5],
    )

    rel = ctx.for_relative()
    assert rel["full_name"] == "Bemor Eshmatov"
    assert rel["level"] == "amber"
    assert len(rel["active_medications"]) == 1
    assert rel["active_medications"][0]["name"] == "Bisoprolol"
    assert rel["weight_trend"] == [70.0, 71.5]
    # ICD10 codes and raw diagnosis should NOT be leaked in caregiver view
    assert "conditions" not in rel
    assert "icd10" not in str(rel)
