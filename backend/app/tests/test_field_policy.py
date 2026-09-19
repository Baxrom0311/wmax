from __future__ import annotations

import uuid
import pytest
from app.auth.field_policy import can_edit_field, assert_can_edit
from app.core.exceptions import ForbiddenException
from app.schemas.auth import CurrentUser


def test_doctor_can_edit_all_fields():
    doc = CurrentUser(id=uuid.uuid4(), full_name="Dr. Bahrom", role="doctor")
    assert can_edit_field(doc, "patient_conditions", "icd10") is True
    assert can_edit_field(doc, "patient_medications", "dose") is True
    assert can_edit_field(doc, "patient_measurements", "weight_kg") is True
    assert can_edit_field(doc, "patient_addresses", "landmark") is True
    assert_can_edit(doc, "patient_conditions", {"icd10": "I25.1"})
    assert_can_edit(doc, "patient_medications", {"dose": "5mg"})


def test_nurse_cannot_edit_restricted_clinical_fields():
    nurse = CurrentUser(id=uuid.uuid4(), full_name="Hamshira Dilnoza", role="nurse")
    assert can_edit_field(nurse, "patient_conditions", "icd10") is False
    assert can_edit_field(nurse, "patients", "diagnosis") is False
    assert can_edit_field(nurse, "patient_measurements", "weight_kg") is True
    assert can_edit_field(nurse, "patient_medications", "dose") is True
    assert can_edit_field(nurse, "patient_admissions", "reason") is True

    with pytest.raises(ForbiddenException) as exc_info:
        assert_can_edit(nurse, "patient_conditions", {"icd10": "I25.1"})
    assert "icd10" in str(exc_info.value)


def test_relative_can_edit_address_and_weight_only():
    rel = CurrentUser(id=uuid.uuid4(), full_name="Karim Valiyev", role="relative")
    assert can_edit_field(rel, "patient_addresses", "landmark") is True
    assert can_edit_field(rel, "relatives", "phone") is True
    assert can_edit_field(rel, "patient_measurements", "weight_kg") is True

    # Relative CANNOT edit condition or clinical phase or medications
    assert can_edit_field(rel, "patient_conditions", "icd10") is False
    assert can_edit_field(rel, "patient_medications", "dose") is False
    assert can_edit_field(rel, "patients", "diagnosis") is False

    with pytest.raises(ForbiddenException):
        assert_can_edit(rel, "patient_conditions", {"icd10": "I25.1"})


def test_patient_can_edit_own_landmark_and_weight():
    pat = CurrentUser(id=uuid.uuid4(), full_name="Bemor Ali", role="patient")
    assert can_edit_field(pat, "patient_addresses", "landmark") is True
    assert can_edit_field(pat, "patient_measurements", "weight_kg") is True
    assert can_edit_field(pat, "patients", "phone") is True
    assert can_edit_field(pat, "patient_conditions", "icd10") is False
    assert can_edit_field(pat, "patient_admissions", "reason") is False
