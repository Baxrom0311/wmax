from __future__ import annotations

import logging
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


async def send_sms_code(*, phone: str, code: str, expires_at: datetime) -> None:
    provider = settings.SMS_PROVIDER.strip().lower()
    if provider == "log":
        await LoggingSmsProvider().send_code(phone=phone, code=code, expires_at=expires_at)
        return
    raise ValidationException(f"SMS provayderi qo'llab-quvvatlanmaydi: {provider}")


def should_return_dev_code() -> bool:
    return settings.ENV != "production"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
