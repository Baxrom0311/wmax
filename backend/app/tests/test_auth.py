from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.auth.service import AuthService
from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
)
from app.models.patient import Patient
from app.models.relative import Relative
from app.models.user import User
from app.schemas.auth import LoginRequest, RelativeLoginRequest


@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_relative_login_rejects_unknown_phone(mock_session):
    auth_service = AuthService(mock_session)
    auth_service.relative_repo.get_assigned_patients = AsyncMock(return_value=[])

    req = RelativeLoginRequest(phone="+998909999999", pin="112233")
    with pytest.raises(AuthenticationException, match="PIN-kod yoki telefon raqami"):
        await auth_service.relative_login(req)


@pytest.mark.asyncio
async def test_relative_login_rejects_wrong_pin(mock_session):
    auth_service = AuthService(mock_session)
    rel_id = uuid.uuid4()
    pat_id = uuid.uuid4()
    correct_pin_hash = hash_password("112233")

    mock_rel = Relative(
        id=rel_id,
        patient_id=pat_id,
        full_name="Farzand",
        relationship="farzandi",
        phone="+998901110011",
        pin_hash=correct_pin_hash,
        access_token="tok123",
    )
    mock_pat = Patient(
        id=pat_id,
        full_name="Otabek",
        age=65,
        sex="m",
        diagnosis="HF",
        district="Urganch",
    )

    auth_service.relative_repo.get_assigned_patients = AsyncMock(
        return_value=[(mock_rel, mock_pat)]
    )

    req = RelativeLoginRequest(phone="+998901110011", pin="999999")
    with pytest.raises(AuthenticationException, match="PIN-kod yoki telefon raqami"):
        await auth_service.relative_login(req)


@pytest.mark.asyncio
async def test_relative_login_issues_relative_role(mock_session):
    auth_service = AuthService(mock_session)
    rel_id = uuid.uuid4()
    pat_id = uuid.uuid4()
    pin_hash = hash_password("112233")

    mock_rel = Relative(
        id=rel_id,
        patient_id=pat_id,
        full_name="Farzand",
        relationship="farzandi",
        phone="+998901110011",
        pin_hash=pin_hash,
        access_token="tok123",
    )
    mock_pat = Patient(
        id=pat_id,
        full_name="Otabek",
        age=65,
        sex="m",
        diagnosis="HF",
        district="Urganch",
    )

    auth_service.relative_repo.get_assigned_patients = AsyncMock(
        return_value=[(mock_rel, mock_pat)]
    )
    auth_service.token_repo.save = AsyncMock()

    with patch("app.auth.service.AlertRepository") as MockAlertRepo:
        mock_alert_repo = MockAlertRepo.return_value
        mock_alert_repo.get_latest = AsyncMock(return_value=None)

        req = RelativeLoginRequest(phone="+998901110011", pin="112233")
        res = await auth_service.relative_login(req)

        # F2 regression check: Caregiver MUST receive role "relative", NEVER "doctor"
        assert res.role == "relative"
        assert len(res.patients) == 1
        assert res.patients[0].id == pat_id
        assert res.patients[0].access_token == "tok123"


@pytest.mark.asyncio
async def test_relative_login_returns_linked_patients(mock_session):
    auth_service = AuthService(mock_session)
    rel_id1 = uuid.uuid4()
    rel_id2 = uuid.uuid4()
    pat_id1 = uuid.uuid4()
    pat_id2 = uuid.uuid4()
    pin_hash = hash_password("112233")

    rel1 = Relative(
        id=rel_id1, patient_id=pat_id1, full_name="Farzand", relationship="o'g'li",
        phone="+998901110011", pin_hash=pin_hash, access_token="tok1"
    )
    pat1 = Patient(id=pat_id1, full_name="Otabek", age=65, sex="m", diagnosis="HF", district="Urganch")

    rel2 = Relative(
        id=rel_id2, patient_id=pat_id2, full_name="Farzand", relationship="o'g'li",
        phone="+998901110011", pin_hash=pin_hash, access_token="tok2"
    )
    pat2 = Patient(id=pat_id2, full_name="Salomat", age=62, sex="f", diagnosis="COPD", district="Xiva")

    auth_service.relative_repo.get_assigned_patients = AsyncMock(
        return_value=[(rel1, pat1), (rel2, pat2)]
    )
    auth_service.token_repo.save = AsyncMock()

    with patch("app.auth.service.AlertRepository") as MockAlertRepo:
        mock_alert_repo = MockAlertRepo.return_value
        mock_alert_repo.get_latest = AsyncMock(return_value=None)

        req = RelativeLoginRequest(phone="+998901110011", pin="112233")
        res = await auth_service.relative_login(req)

        assert len(res.patients) == 2
        patient_ids = {p.id for p in res.patients}
        assert patient_ids == {pat_id1, pat_id2}


@pytest.mark.asyncio
async def test_demo_credentials_rejected_when_disabled(mock_session, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_DEMO_ACCOUNTS", False)
    auth_service = AuthService(mock_session)
    auth_service.user_repo.get_by_phone = AsyncMock(return_value=None)

    req = LoginRequest(phone="+998901234567", password="wmax123")
    with pytest.raises(AuthenticationException, match="Telefon raqami yoki parol noto'g'ri"):
        await auth_service.login(req)


@pytest.mark.asyncio
async def test_demo_credentials_accepted_when_enabled(mock_session, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_DEMO_ACCOUNTS", True)
    auth_service = AuthService(mock_session)
    auth_service.user_repo.get_by_phone = AsyncMock(return_value=None)
    auth_service.token_repo.save = AsyncMock()

    req = LoginRequest(phone="+998901234567", password="wmax123")
    res = await auth_service.login(req)

    assert res.role == "doctor"
    assert res.full_name == "Dr. Bahrom Alimov"


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(mock_session):
    auth_service = AuthService(mock_session)
    inactive_user = User(
        id=uuid.uuid4(),
        full_name="Deactivated Doctor",
        phone="+998905555555",
        password_hash=hash_password("secret123"),
        role="doctor",
        district="Urganch",
        is_active=False,
    )
    auth_service.user_repo.get_by_phone = AsyncMock(return_value=inactive_user)

    req = LoginRequest(phone="+998905555555", password="secret123")
    with pytest.raises(AuthenticationException, match="Hisob faol emas"):
        await auth_service.login(req)


@pytest.mark.asyncio
async def test_refresh_token_rejected_as_access_token(mock_session):
    auth_service = AuthService(mock_session)
    # create an access token instead of a refresh token
    access_tok = create_access_token(
        subject=str(uuid.uuid4()),
        claims={"role": "doctor", "full_name": "Dr. Test"},
    )

    with pytest.raises(AuthenticationException, match="Yaroqsiz refresh token turi"):
        await auth_service.refresh_tokens(access_tok)


@pytest.mark.asyncio
async def test_refresh_preserves_relative_role(mock_session):
    auth_service = AuthService(mock_session)
    rel_id = uuid.uuid4()
    refresh_tok, _, _ = create_refresh_token(
        subject=str(rel_id),
        claims={"role": "relative", "full_name": "Test Caregiver", "phone": "+998901110011"},
    )

    mock_record = MagicMock()
    mock_record.user_id = rel_id
    auth_service.token_repo.get_valid = AsyncMock(return_value=mock_record)
    auth_service.token_repo.revoke = AsyncMock()
    auth_service.token_repo.save = AsyncMock()

    res = await auth_service.refresh_tokens(refresh_tok)
    assert res.role == "relative"
    assert res.full_name == "Test Caregiver"
