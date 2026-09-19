from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.auth.service import AuthService
from app.core.exceptions import AuthenticationException
from app.core.security import hash_password
from app.models.patient import Patient
from app.schemas.auth import PatientLoginRequest


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_patient_login_success(mock_session):
    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        full_name="Sabina Karimova",
        phone="+998909998877",
        pin_hash=hash_password("123456"),
        district="Urganch",
        sex="f",
        age=55,
        diagnosis="I25.1",
    )

    service = AuthService(mock_session)
    service.patient_repo.get_by_phone = AsyncMock(return_value=patient)
    service.token_repo.create = AsyncMock()

    tokens = await service.patient_login(
        PatientLoginRequest(phone="+998909998877", pin="123456")
    )

    assert tokens.role == "patient"
    assert tokens.full_name == "Sabina Karimova"
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None


@pytest.mark.asyncio
async def test_patient_login_wrong_pin(mock_session):
    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        full_name="Sabina Karimova",
        phone="+998909998877",
        pin_hash=hash_password("123456"),
        district="Urganch",
        sex="f",
        age=55,
        diagnosis="I25.1",
    )

    service = AuthService(mock_session)
    service.patient_repo.get_by_phone = AsyncMock(return_value=patient)

    with pytest.raises(AuthenticationException):
        await service.patient_login(
            PatientLoginRequest(phone="+998909998877", pin="000000")
        )


@pytest.mark.asyncio
async def test_patient_login_unknown_phone(mock_session):
    service = AuthService(mock_session)
    service.patient_repo.get_by_phone = AsyncMock(return_value=None)

    with pytest.raises(AuthenticationException):
        await service.patient_login(
            PatientLoginRequest(phone="+998900000000", pin="123456")
        )
