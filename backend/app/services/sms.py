from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.core.config import settings
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class SmsProvider(Protocol):
    async def send_code(self, *, phone: str, code: str, expires_at: datetime) -> None:
        ...


@dataclass
class LoggingSmsProvider:
    async def send_code(self, *, phone: str, code: str, expires_at: datetime) -> None:
        if settings.ENV == "production":
            raise ValidationException("Production SMS provayderi sozlanmagan")
        logger.info(
            "SMS login code for %s: %s, expires_at=%s",
            phone,
            code,
            expires_at.isoformat(),
        )


ESKIZ_BASE_URL = "https://notify.eskiz.uz/api/"
ESKIZ_DELIVERED = "DELIVERED"
# Terminal provider states (Eskiz docs: UNDELIV/UNDELIVERABLE, EXPIRED, REJECTD, DELETED).
ESKIZ_FAILED = frozenset({"UNDELIV", "UNDELIVERABLE", "EXPIRED", "REJECTD", "REJECTED", "DELETED", "FAILED"})


class SmsProviderError(Exception):
    """Provider refused or could not be reached. Never contains message text."""


class EskizSmsProvider:
    """Eskiz public API. Provider acceptance is not delivery.

    Contract: https://documenter.getpostman.com/view/663428/RzfmES4z
    `submit` returns Eskiz's request id once the message is queued ("waiting");
    `delivery_status` later reports DELIVERED or a terminal failure. There is no
    automatic resend here: the durable notification worker owns retries.
    """

    _token: str | None = None

    def __init__(self, client_factory=None) -> None:
        import httpx

        self._client_factory = client_factory or (lambda: httpx.AsyncClient(timeout=10.0, base_url=ESKIZ_BASE_URL))

    @staticmethod
    def configured() -> bool:
        return bool(settings.ESKIZ_TOKEN or (settings.ESKIZ_EMAIL and settings.ESKIZ_PASSWORD))

    async def _login(self, client) -> str:
        response = await client.post("auth/login", data={
            "email": settings.ESKIZ_EMAIL, "password": settings.ESKIZ_PASSWORD,
        })
        if response.status_code != 200:
            raise SmsProviderError(f"eskiz_login_http_{response.status_code}")
        token = (response.json().get("data") or {}).get("token")
        if not token:
            raise SmsProviderError("eskiz_login_no_token")
        EskizSmsProvider._token = token
        return token

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        if not self.configured():
            raise SmsProviderError("eskiz_not_configured")
        async with self._client_factory() as client:
            token = settings.ESKIZ_TOKEN or EskizSmsProvider._token or await self._login(client)
            response = await client.request(method, path, headers={"Authorization": f"Bearer {token}"}, **kwargs)
            if response.status_code == 401 and settings.ESKIZ_EMAIL and settings.ESKIZ_PASSWORD:
                token = await self._login(client)
                response = await client.request(method, path, headers={"Authorization": f"Bearer {token}"}, **kwargs)
            if response.status_code >= 400:
                raise SmsProviderError(f"eskiz_http_{response.status_code}")
            return response.json()

    async def submit(self, *, phone: str, message: str) -> str:
        payload = await self._request("POST", "message/sms/send", data={
            "mobile_phone": phone.lstrip("+"), "message": message, "from": settings.ESKIZ_SENDER,
        })
        if payload.get("status") != "waiting" or not payload.get("id"):
            raise SmsProviderError("eskiz_not_accepted")
        return str(payload["id"])

    async def delivery_status(self, reference: str) -> str:
        # References come from the provider but must never become arbitrary paths.
        reference = reference if reference.isdigit() else str(uuid.UUID(reference))
        payload = await self._request("GET", f"message/sms/status_by_id/{reference}")
        return str((payload.get("data") or {}).get("status", "UNKNOWN")).upper()

    async def send_code(self, *, phone: str, code: str, expires_at: datetime) -> None:
        await self.submit(phone=phone, message=f"WMAX tasdiqlash kodi: {code}")


async def send_sms_code(*, phone: str, code: str, expires_at: datetime) -> None:
    provider = settings.SMS_PROVIDER.strip().lower()
    if provider == "log":
        await LoggingSmsProvider().send_code(phone=phone, code=code, expires_at=expires_at)
        return
    if provider != "eskiz":
        raise ValidationException("SMS provayderi qo'llab-quvvatlanmaydi")
    if not EskizSmsProvider.configured():
        raise ValidationException("Eskiz SMS adapter ulanmagan; ESKIZ_TOKEN yoki ESKIZ_EMAIL/ESKIZ_PASSWORD talab qilinadi")
    try:
        await EskizSmsProvider().send_code(phone=phone, code=code, expires_at=expires_at)
    except Exception as exc:
        # Provider errors may echo credentials or the code itself; never forward them.
        logger.error("Login SMS was not accepted by provider: %s", type(exc).__name__)
        raise ValidationException("SMS yuborilmadi; keyinroq qayta urinib ko'ring") from exc


def should_return_dev_code() -> bool:
    return settings.ENV != "production"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
