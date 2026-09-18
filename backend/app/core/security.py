from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with automatic salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash in constant time."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Generates a signed JWT access token with JTI and expiry."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN))

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    if claims:
        payload.update(claims)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_refresh_token(
    subject: str,
    claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
    jti: str | None = None,
) -> tuple[str, str, datetime]:
    """Generates a signed JWT refresh token and returns (token, jti, expires_at)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS))
    token_jti = jti or str(uuid.uuid4())

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "jti": token_jti,
        "type": "refresh",
    }
    if claims:
        payload.update(claims)

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token, token_jti, expire


def decode_token(token: str) -> dict[str, Any]:
    """Validates signature and claims of a JWT token, raising jwt exceptions if invalid."""
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALG],
        options={"require": ["exp", "sub", "iat", "type"]},
    )


# Alias for clarity
decode_jwt = decode_token
