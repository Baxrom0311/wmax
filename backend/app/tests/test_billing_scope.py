from __future__ import annotations

import uuid

import pytest

from app.core.exceptions import ForbiddenException
from app.schemas.auth import CurrentUser
from app.api.billing import _assert_patient_billing_scope


def test_patient_billing_scope_allows_self():
    patient_id = uuid.uuid4()
    principal = CurrentUser(id=patient_id, full_name="Patient", role="patient")

    _assert_patient_billing_scope(principal, patient_id)


def test_patient_billing_scope_rejects_other_patient():
    principal = CurrentUser(id=uuid.uuid4(), full_name="Patient", role="patient")

    with pytest.raises(ForbiddenException):
        _assert_patient_billing_scope(principal, uuid.uuid4())


def test_relative_billing_scope_requires_patient_link():
    patient_id = uuid.uuid4()
    principal = CurrentUser(
        id=uuid.uuid4(),
        full_name="Relative",
        role="relative",
        patient_ids=[],
    )

    with pytest.raises(ForbiddenException):
        _assert_patient_billing_scope(principal, patient_id)

    principal.patient_ids.append(patient_id)
    _assert_patient_billing_scope(principal, patient_id)
