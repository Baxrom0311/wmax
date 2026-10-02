from __future__ import annotations

import logging
import secrets
import hashlib
import uuid
from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.rls import set_rls_context
from app.core.security import create_access_token, decode_token
from app.models.device import DeviceCredential

logger = logging.getLogger("wmax.auth.device")

INGEST_KEY_HEADER = "X-Ingest-Key"
device_bearer_scheme = HTTPBearer(auto_error=False)
ingest_api_key_header = APIKeyHeader(
    name=INGEST_KEY_HEADER,
    auto_error=False,
    scheme_name="IngestApiKey",
    description="Wearable fleet ingest secret key (X-Ingest-Key header)",
)


@dataclass(frozen=True)
class DevicePrincipal:
    device_id: uuid.UUID
    credential_id: uuid.UUID


def create_device_token(
    device_id: uuid.UUID,
    credential_id: uuid.UUID,
    expires_delta: timedelta | None = None,
    credential_secret: str | None = None,
) -> str:
    claims: dict[str, str] = {
        "type": "device",
        "credential_id": str(credential_id),
    }
    if credential_secret is not None:
        claims["credential_secret"] = credential_secret
    return create_access_token(
        subject=str(device_id),
        claims=claims,
        expires_delta=expires_delta or timedelta(days=365),
    )


async def get_current_device(
    credentials: HTTPAuthorizationCredentials | None = Security(device_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> DevicePrincipal:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Qurilma tokeni talab qilinadi",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "device":
            raise ValueError("not a device token")
        device_id = uuid.UUID(payload["sub"])
        credential_id = uuid.UUID(payload["credential_id"])
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Qurilma tokeni yaroqsiz",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    credential = await session.get(DeviceCredential, credential_id)
    if (
        credential is None
        or credential.device_id != device_id
        or credential.revoked_at is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Qurilma tokeni bekor qilingan",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credential_secret = payload.get("credential_secret")
    if credential_secret is not None and not secrets.compare_digest(
        credential.secret_hash,
        hashlib.sha256(str(credential_secret).encode()).hexdigest(),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Qurilma credential yaroqsiz",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await set_rls_context(session, device_id=device_id)
    return DevicePrincipal(device_id=device_id, credential_id=credential_id)


async def verify_ingest_key(
    x_ingest_key: str | None = Security(ingest_api_key_header),
) -> None:
    """Authenticates a wearable companion app uploading physiological readings.

    Without this, anyone who can reach the API can post readings for any
    patient_id — fabricating red alerts or masking a real deterioration.

    The key is shared by all devices; it authenticates the fleet, not the
    individual watch. Per-device credentials are the next step, but a fleet
    secret already closes the open-to-the-internet hole.
    """
    expected = settings.INGEST_API_KEY

    if not expected:
        # Production boot refuses to start without a key (see
        # validate_production_settings), so this branch is dev/test only.
        logger.warning(
            "INGEST_API_KEY is not configured — accepting unauthenticated ingest. "
            "This is only permitted outside production."
        )
        return

    if not x_ingest_key or not secrets.compare_digest(x_ingest_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Qurilma kaliti yaroqsiz",
        )
