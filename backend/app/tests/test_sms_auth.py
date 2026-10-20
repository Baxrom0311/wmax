from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from app.auth import service as auth_service_module
from app.auth.service import AuthService, _SMS_CODES
from app.core.config import settings
from app.core.exceptions import ValidationException
from app.services.sms import ESKIZ_BASE_URL, EskizSmsProvider, send_sms_code


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


@pytest.fixture
def eskiz(monkeypatch):
    monkeypatch.setattr(settings, "SMS_PROVIDER", "eskiz")
    monkeypatch.setattr(settings, "ESKIZ_TOKEN", "")
    monkeypatch.setattr(settings, "ESKIZ_EMAIL", "ops@example.test")
    monkeypatch.setattr(settings, "ESKIZ_PASSWORD", "synthetic")
    monkeypatch.setattr(EskizSmsProvider, "_token", None)
    calls: list[httpx.Request] = []

    def factory(handler):
        def client():
            def record(request):
                calls.append(request)
                return handler(request)

            return httpx.AsyncClient(transport=httpx.MockTransport(record), base_url=ESKIZ_BASE_URL)

        return EskizSmsProvider(client_factory=client)

    return factory, calls


@pytest.mark.asyncio
async def test_unconfigured_eskiz_refuses_login_sms(monkeypatch):
    monkeypatch.setattr(settings, "SMS_PROVIDER", "eskiz")
    monkeypatch.setattr(settings, "ESKIZ_TOKEN", "")
    monkeypatch.setattr(settings, "ESKIZ_EMAIL", "")
    monkeypatch.setattr(settings, "ESKIZ_PASSWORD", "")
    with pytest.raises(ValidationException, match="adapter ulanmagan"):
        await send_sms_code(phone="+998900000000", code="123456", expires_at=auth_service_module.now_utc())


@pytest.mark.asyncio
async def test_eskiz_submit_logs_in_and_returns_provider_reference(eskiz):
    factory, calls = eskiz

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("auth/login"):
            return httpx.Response(200, json={"message": "token_generated", "data": {"token": "T1"}})
        assert request.headers["Authorization"] == "Bearer T1"
        form = dict(item.split("=", 1) for item in request.content.decode().split("&"))
        assert form["mobile_phone"] == "998900000000"
        return httpx.Response(200, json={"id": "59bf10a2-aba8-4694-8fd5-0be20102a580", "status": "waiting"})

    reference = await factory(handler).submit(phone="+998900000000", message="test")
    assert reference == "59bf10a2-aba8-4694-8fd5-0be20102a580"
    assert [c.url.path for c in calls] == ["/api/auth/login", "/api/message/sms/send"]


@pytest.mark.asyncio
async def test_eskiz_acceptance_is_not_delivery_and_status_is_read_from_report(eskiz):
    factory, _calls = eskiz
    EskizSmsProvider._token = "cached"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("status_by_id/59bf10a2-aba8-4694-8fd5-0be20102a580")
        return httpx.Response(200, json={"status": "success", "data": {"status": "DELIVERED"}})

    assert await factory(handler).delivery_status("59bf10a2-aba8-4694-8fd5-0be20102a580") == "DELIVERED"
    with pytest.raises(ValueError):
        await factory(handler).delivery_status("../../auth/user")


@pytest.mark.asyncio
async def test_eskiz_relogs_in_once_after_expired_token(eskiz):
    factory, calls = eskiz
    EskizSmsProvider._token = "expired"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("auth/login"):
            return httpx.Response(200, json={"data": {"token": "fresh"}})
        if request.headers["Authorization"] == "Bearer expired":
            return httpx.Response(401, json={"message": "Expired"})
        return httpx.Response(200, json={"id": "1", "status": "waiting"})

    assert await factory(handler).submit(phone="+998900000000", message="x") == "1"
    assert EskizSmsProvider._token == "fresh"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_login_sms_failure_does_not_leak_provider_details(eskiz, monkeypatch, caplog):
    factory, _calls = eskiz

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="secret-token 123456")

    mocked = factory(handler)._client_factory
    original_init = EskizSmsProvider.__init__
    monkeypatch.setattr(
        EskizSmsProvider, "__init__", lambda self, client_factory=None: original_init(self, client_factory=mocked),
    )
    with pytest.raises(ValidationException) as exc:
        await send_sms_code(phone="+998900000000", code="123456", expires_at=auth_service_module.now_utc())
    assert "123456" not in str(exc.value.detail if hasattr(exc.value, "detail") else exc.value)
    assert "secret-token" not in caplog.text
