from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictException
from app.models import Account, PatientAccess, PatientConsent, PatientMembership
from app.services.patient_relationship_service import PatientRelationshipService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.mark.asyncio
async def test_create_membership_is_idempotent_for_same_active_membership(mock_session):
    patient_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    existing = PatientMembership(
        id=uuid.uuid4(),
        patient_id=patient_id,
        tenant_id=tenant_id,
        kind="care",
    )
    mock_session.execute.return_value = _result(existing)

    result = await PatientRelationshipService(mock_session).create_membership(
        patient_id=patient_id,
        tenant_id=tenant_id,
        kind="care",
        granted_by=uuid.uuid4(),
    )

    assert result["id"] == str(existing.id)
    mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_membership_rejects_second_care_owner(mock_session):
    patient_id = uuid.uuid4()
    first_result = _result(None)
    second_result = _result(
        PatientMembership(
            id=uuid.uuid4(),
            patient_id=patient_id,
            tenant_id=uuid.uuid4(),
            kind="care",
        )
    )
    mock_session.execute.side_effect = [first_result, second_result]

    with pytest.raises(ConflictException):
        await PatientRelationshipService(mock_session).create_membership(
            patient_id=patient_id,
            tenant_id=uuid.uuid4(),
            kind="care",
            granted_by=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_invite_access_returns_existing_active_access(mock_session):
    patient_id = uuid.uuid4()
    account = Account(id=uuid.uuid4(), phone="+998901234567", full_name="Caregiver")
    access = PatientAccess(
        id=uuid.uuid4(),
        patient_id=patient_id,
        account_id=account.id,
        role="caregiver",
    )
    mock_session.execute.side_effect = [_result(account), _result(access)]

    result = await PatientRelationshipService(mock_session).invite_access(
        patient_id=patient_id,
        phone=account.phone,
        full_name=account.full_name,
        role="caregiver",
        relation="farzand",
        invited_by=uuid.uuid4(),
    )

    assert result["id"] == str(access.id)
    mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_consent_is_idempotent(mock_session):
    revoked_at = datetime.now(timezone.utc)
    consent = PatientConsent(
        id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        scope="family_access",
        granted=True,
        method="verbal_by_clinician",
        revoked_at=revoked_at,
    )
    mock_session.get = AsyncMock(return_value=consent)

    result = await PatientRelationshipService(mock_session).revoke_consent(
        patient_id=consent.patient_id,
        consent_id=consent.id,
    )

    assert result["revoked_at"] == revoked_at.isoformat()
    mock_session.commit.assert_not_awaited()
