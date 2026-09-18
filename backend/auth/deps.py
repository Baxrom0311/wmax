"""A6 auth implementation — JWT Bearer authentication and RBAC.

Preserves exact contracts and shapes expected by A1 (backend-core).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .security import decode_token

Role = Literal["doctor", "nurse", "admin"]


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    full_name: str
    role: Role
    district: str | None = None


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> CurrentUser:
    """FastAPI dependency: verifies JWT Bearer token and returns CurrentUser."""
    if not credentials:
        # Fallback for local development stub if no Authorization header provided
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya talab qilinadi",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = UUID(payload["sub"])
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
    """FastAPI dependency factory: Depends(require_role('doctor'))."""

    async def _dep(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu amalni bajarish uchun yetarli huquq yo'q",
            )
        return current_user

    return _dep


# A6 mounts its endpoints here; A1 does: app.include_router(auth_router)
try:
    from auth.router import router as auth_router  # type: ignore
except Exception:  # noqa: BLE001
    from fastapi import APIRouter

    auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
