"""STUB — Task 0. A6 replaces this file with the real implementation.

It exists so that A1 (backend-core) can write
    from auth.deps import get_current_user, require_role
on its very first line of code and never wait for A6.

The signatures below are part of the contract. A6 may change the BODY,
never the NAMES or the SHAPE.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

Role = Literal["doctor", "nurse", "admin"]


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    full_name: str
    role: Role
    district: str | None = None


async def get_current_user() -> CurrentUser:
    """FastAPI dependency. STUB: returns a fixed demo doctor.

    A6 replaces the body with real JWT verification (Authorization: Bearer).
    """
    return CurrentUser(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        full_name="STUB Doctor",
        role="doctor",
        district="Urganch",
    )


def require_role(*roles: Role):
    """FastAPI dependency factory: Depends(require_role('doctor'))."""

    async def _dep() -> CurrentUser:
        return await get_current_user()

    return _dep


# A6 mounts its endpoints here; A1 does:  app.include_router(auth_router)
# with prefix "/api/v1/auth" already baked in.
try:  # pragma: no cover - real router arrives with A6
    from auth.router import router as auth_router  # type: ignore
except Exception:  # noqa: BLE001
    from fastapi import APIRouter

    auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
