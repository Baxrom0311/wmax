from __future__ import annotations

import uuid

import pytest

from app.api.profile import _verify_patient_access
from app.core.exceptions import ForbiddenException
from app.schemas.auth import CurrentUser


def test_relative_profile_scope_requires_patient_link():
    patient_id = uuid.uuid4()
    principal = CurrentUser(
        id=uuid.uuid4(),
        full_name="Relative",
        role="relative",
        patient_ids=[],
    )

    with pytest.raises(ForbiddenException):
        _verify_patient_access(patient_id, principal)

    principal.patient_ids.append(patient_id)
    _verify_patient_access(patient_id, principal)


def test_patient_profile_scope_allows_self_only():
    patient_id = uuid.uuid4()
    principal = CurrentUser(id=patient_id, full_name="Patient", role="patient")

    _verify_patient_access(patient_id, principal)

    with pytest.raises(ForbiddenException):
        _verify_patient_access(uuid.uuid4(), principal)
