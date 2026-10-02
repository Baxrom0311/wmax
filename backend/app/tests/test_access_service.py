from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.models import PatientAccess
from app.services.access_service import AccessService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _access(*, account_id: uuid.UUID, revoked: bool = False) -> PatientAccess:
    return PatientAccess(
        id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        account_id=account_id,
        role="caregiver",
        relation="farzand",
        granted_at=datetime(2026, 9, 22, 9, 0, tzinfo=timezone.utc),
        revoked_at=datetime.now(timezone.utc) if revoked else None,
    )


@pytest.mark.asyncio
async def test_accept_invitation_commits_owner_access(mock_session, monkeypatch):
    account_id = uuid.uuid4()
    access = _access(account_id=account_id)
    service = AccessService(mock_session)
    service.repo.get_by_id = AsyncMock(return_value=access)

    result = await service.accept_invitation(access_id=access.id, account_id=account_id)

    assert result["accepted"] is True
    assert result["id"] == str(access.id)
    assert result["patient_id"] == str(access.patient_id)
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_accept_invitation_rejects_missing_access(mock_session):
    service = AccessService(mock_session)
    service.repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundException):
        await service.accept_invitation(access_id=uuid.uuid4(), account_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_accept_invitation_rejects_other_account(mock_session):
    access = _access(account_id=uuid.uuid4())
    service = AccessService(mock_session)
    service.repo.get_by_id = AsyncMock(return_value=access)

    with pytest.raises(ForbiddenException):
        await service.accept_invitation(access_id=access.id, account_id=uuid.uuid4())

    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_accept_invitation_rejects_revoked_access(mock_session):
    account_id = uuid.uuid4()
    access = _access(account_id=account_id, revoked=True)
    service = AccessService(mock_session)
    service.repo.get_by_id = AsyncMock(return_value=access)

    with pytest.raises(ValidationException):
        await service.accept_invitation(access_id=access.id, account_id=account_id)

    mock_session.commit.assert_not_awaited()
