from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.patient import Patient
from app.models.relative import Relative
from app.services.relative_service import RelativeService, is_access_token_expired


@pytest.mark.asyncio
async def test_caregiver_cannot_read_other_caregivers_token():
    session = AsyncMock()
    service = RelativeService(session)

    target_token = "token_intended_for_ali"
    mock_relative = Relative(
        id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        full_name="Ali",
        relationship="farzandi",
        phone="+998901110011",
        access_token=target_token,
        created_at=datetime.now(timezone.utc),
    )
    service.relative_repo.get_by_token = AsyncMock(return_value=mock_relative)

    # Different caregiver phone trying to access Ali's token
    with pytest.raises(ForbiddenException, match="Bu havola sizga tegishli emas"):
        await service.get_relative_view(target_token, caregiver_phone="+998909998877")


@pytest.mark.asyncio
async def test_expired_access_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "RELATIVE_TOKEN_TTL_DAYS", 90)
    session = AsyncMock()
    service = RelativeService(session)

    expired_created_at = datetime.now(timezone.utc) - timedelta(days=91)
    mock_relative = Relative(
        id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        full_name="Vali",
        relationship="farzandi",
        phone="+998901110011",
        access_token="expired_token_test",
        created_at=expired_created_at,
    )
    service.relative_repo.get_by_token = AsyncMock(return_value=mock_relative)

    assert is_access_token_expired(expired_created_at) is True

    with pytest.raises(ForbiddenException, match="Havola muddati tugagan"):
        await service.get_relative_view("expired_token_test", caregiver_phone="+998901110011")


@pytest.mark.asyncio
async def test_unexpired_access_token_accepted(monkeypatch):
    monkeypatch.setattr(settings, "RELATIVE_TOKEN_TTL_DAYS", 90)
    valid_created_at = datetime.now(timezone.utc) - timedelta(days=10)
    assert is_access_token_expired(valid_created_at) is False
