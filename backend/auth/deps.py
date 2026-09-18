"""A6 auth implementation — JWT Bearer authentication and RBAC with DB persistence."""
from __future__ import annotations

from app.auth.deps import (
    CurrentUser,
    Role,
    get_current_user,
    require_clinician,
    require_doctor,
    require_role,
)
from app.auth.router import router as auth_router

__all__ = [
    "CurrentUser",
    "Role",
    "get_current_user",
    "require_role",
    "require_doctor",
    "require_clinician",
    "auth_router",
]
