from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.auth import service as auth_service_module
from app.auth.service import AuthService, _SMS_CODES
from app.core.config import settings
from app.core.exceptions import ValidationException
from app.services.sms import EskizSmsProvider, send_sms_text


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_request_code_sends_sms_and_returns_dev_code_in_non_production(
    mock_session, monkeypatch
):
    monkeypatch.setattr(settings, "ENV", "development")
    sender = AsyncMock()
    monkeypatch.setattr(auth_service_module, "send_sms_code", sender)
    _SMS_CODES.clear()

    expires_in, dev_code = await AuthService(mock_session).request_code("+998901234567")

    assert expires_in == auth_service_module.SMS_CODE_TTL_SECONDS
    assert dev_code is not None
    assert _SMS_CODES["+998901234567"][0] == dev_code
    sender.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_code_hides_dev_code_in_production(mock_session, monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    sender = AsyncMock()
    monkeypatch.setattr(auth_service_module, "send_sms_code", sender)
    _SMS_CODES.clear()

    _expires_in, dev_code = await AuthService(mock_session).request_code("+998901234567")

    assert dev_code is None
    sender.assert_awaited_once()


@pytest.mark.asyncio
async def test_unconfigured_eskiz_and_emergency_sms_never_claim_delivery(monkeypatch):
    monkeypatch.setattr(settings, "SMS_PROVIDER", "eskiz")
    with pytest.raises(ValidationException, match="adapter ulanmagan"):
        await EskizSmsProvider().send_code(
            phone="+998900000000", code="123456", expires_at=auth_service_module.now_utc()
        )
    assert await send_sms_text(phone="+998900000000", message="test") is False
