from __future__ import annotations

import uuid
from typing import Literal

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationException, ForbiddenException
from app.core.security import decode_token
from app.schemas.auth import CurrentUser

security_scheme = HTTPBearer(auto_error=False)

Role = Literal["doctor", "nurse", "admin"]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
) -> CurrentUser:
    """FastAPI dependency: extracts and validates Bearer token, returning authenticated CurrentUser."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya talab qilinadi",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") == "refresh":
            raise AuthenticationException("Access token o'rniga refresh token yuborildi")

        user_id = uuid.UUID(payload["sub"])
        full_name = payload.get("full_name", "Noma'lum")
        role = payload.get("role", "doctor")
        district = payload.get("district")

        return CurrentUser(
            id=user_id,
            full_name=full_name,
            role=role,
            district=district,
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati o'tgan",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err


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


require_doctor = require_role("doctor")
require_clinician = require_role("doctor", "nurse")
