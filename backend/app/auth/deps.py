from __future__ import annotations

import uuid
from typing import Literal

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.schemas.auth import CurrentUser
from app.schemas.common import CLINICIAN_ROLES

security_scheme = HTTPBearer(auto_error=False)

Role = Literal["doctor", "nurse", "admin", "dispatcher"]

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token yaroqsiz yoki muddati o'tgan",
    headers={"WWW-Authenticate": "Bearer"},
)


def _decode_bearer(credentials: HTTPAuthorizationCredentials | None) -> CurrentUser:
    """Decodes a Bearer access token into a CurrentUser, or raises 401."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya talab qilinadi",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception as err:
        raise CREDENTIALS_EXCEPTION from err

    # A refresh token must never be accepted where an access token is expected.
    if payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, TypeError) as err:
        raise CREDENTIALS_EXCEPTION from err

    role = payload.get("role")
    if role not in CLINICIAN_ROLES and role not in {"relative", "patient"}:
        raise CREDENTIALS_EXCEPTION

    return CurrentUser(
        id=user_id,
        full_name=payload.get("full_name", "Noma'lum"),
        role=role,
        district=payload.get("district"),
        phone=payload.get("phone"),
    )


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
) -> CurrentUser:
    """Any authenticated principal — clinician, caregiver, or patient."""
    return _decode_bearer(credentials)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
) -> CurrentUser:
    """Authenticated clinical staff only (doctor, nurse, admin, dispatcher).

    Caregiver and patient tokens are rejected here: they authenticate against different
    tables/scopes and must never reach the clinician worklist.
    """
    principal = _decode_bearer(credentials)
    if principal.role not in CLINICIAN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu amalni bajarish uchun yetarli huquq yo'q",
        )
    return principal


async def get_current_relative(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
) -> CurrentUser:
    """Authenticated caregiver only."""
    principal = _decode_bearer(credentials)
    if principal.role != "relative":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu amalni bajarish uchun yetarli huquq yo'q",
        )
    return principal


async def get_current_patient(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
) -> CurrentUser:
    """Authenticated patient only."""
    principal = _decode_bearer(credentials)
    if principal.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu amalni bajarish uchun yetarli huquq yo'q",
        )
    return principal


def require_role(*roles: Role):
    """FastAPI dependency factory enforcing RBAC rules: Depends(require_role('doctor'))."""

    async def _dep(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu amalni bajarish uchun yetarli huquq yo'q",
            )
        return current_user

    return _dep


require_doctor = require_role("doctor", "admin")
require_clinician = require_role("doctor", "nurse", "admin", "dispatcher")
require_dispatcher = require_role("dispatcher", "doctor", "admin")
