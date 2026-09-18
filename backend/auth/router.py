"""Production database-backed auth router for A6 & A1."""
from __future__ import annotations

from app.auth.router import (
    CurrentUser,
    LoginRequest,
    LogoutResponse,
    RefreshRequest,
    RelativeLoginRequest,
    TokenPair,
    router,
)

__all__ = [
    "LoginRequest",
    "RelativeLoginRequest",
    "RefreshRequest",
    "TokenPair",
    "CurrentUser",
    "LogoutResponse",
    "router",
]
