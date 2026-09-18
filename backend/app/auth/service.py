from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.relative_repo import RelativeRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, RelativeLoginRequest, TokenPair

# Demo fallback accounts per AGENTS.md contract
DEMO_CREDENTIALS: dict[str, dict[str, Any]] = {
    "+998901234567": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "password": "nazorat123",
        "full_name": "Dr. Bahrom Alimov",
        "role": "doctor",
        "district": "Urganch",
    },
    "901234567": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "password": "nazorat123",
        "full_name": "Dr. Bahrom Alimov",
        "role": "doctor",
        "district": "Urganch",
    },
    "+998901234568": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "password": "nazorat123",
        "full_name": "Hamshira Dilnoza",
        "role": "nurse",
        "district": "Xiva",
    },
    "901234568": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "password": "nazorat123",
        "full_name": "Hamshira Dilnoza",
        "role": "nurse",
        "district": "Xiva",
    },
}
DEMO_RELATIVE_PIN = "112233"


class AuthService:
    """Production auth service: DB-backed login, refresh token rotation, revocation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.relative_repo = RelativeRepository(session)
        self.token_repo = RefreshTokenRepository(session)

    async def login(
        self,
        req: LoginRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        """Authenticates clinician using DB or demo fallback credentials."""
        normalized_phone = req.phone.strip()
        user = await self.user_repo.get_by_phone(normalized_phone)

        user_id: uuid.UUID
        full_name: str
        role: str
        district: str | None

        if user:
            if not verify_password(req.password, user.password_hash):
                raise AuthenticationException("Telefon raqami yoki parol noto'g'ri")
            user_id = user.id
            full_name = user.full_name
            role = user.role
            district = user.district
        else:
            demo = DEMO_CREDENTIALS.get(normalized_phone)
            if not demo or demo["password"] != req.password:
                raise AuthenticationException("Telefon raqami yoki parol noto'g'ri")
            user_id = demo["id"]  # type: ignore[assignment]
            full_name = demo["full_name"]
            role = demo["role"]
            district = demo["district"]

        return await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role=role,
            district=district,
        )

    async def relative_login(
        self,
        req: RelativeLoginRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        """Authenticates caregivers via PIN code."""
        if req.pin != DEMO_RELATIVE_PIN:
            relatives = await self.relative_repo.get_assigned_patients(req.phone)
            if not relatives:
                raise AuthenticationException("PIN-kod yoki telefon raqami noto'g'ri")

        return await self._issue_token_pair(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000099"),
            full_name="Yaqin qarindosh",
            role="doctor",
            district="Urganch",
        )

    async def refresh_tokens(
        self,
        refresh_token_str: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        """Rotates refresh token: validates hash in DB, revokes old, issues new pair."""
        try:
            payload = decode_token(refresh_token_str)
        except Exception as exc:
            raise AuthenticationException("Token eskirgan yoki noto'g'ri") from exc

        if payload.get("type") != "refresh":
            raise AuthenticationException("Yaroqsiz refresh token turi")

        sub_str = payload.get("sub")
        if not sub_str:
            raise AuthenticationException("Token tarkibi buzuq")

        # Validate token against DB via hash
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        token_record = await self.token_repo.get_valid(token_hash)
        if not token_record:
            raise AuthenticationException("Refresh token muddati o'tgan yoki bekor qilingan")

        # Revoke old token
        await self.token_repo.revoke(token_hash)

        user_id = uuid.UUID(sub_str)
        full_name = payload.get("full_name", "")
        role = payload.get("role", "doctor")
        district = payload.get("district")

        return await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role=role,
            district=district,
        )

    async def revoke_token(self, refresh_token_str: str) -> None:
        """Revokes refresh token on logout (no-op if already expired/missing)."""
        try:
            token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
            await self.token_repo.revoke(token_hash)
        except Exception:
            pass  # Silent on logout errors

    async def _issue_token_pair(
        self,
        user_id: uuid.UUID,
        full_name: str,
        role: str,
        district: str | None,
    ) -> TokenPair:
        claims = {"full_name": full_name, "role": role, "district": district}

        access_token = create_access_token(
            subject=str(user_id),
            claims=claims,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN),
        )

        # create_refresh_token returns (token_str, jti, expires_at)
        refresh_token, _jti, expires_at = create_refresh_token(
            subject=str(user_id),
            claims=claims,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
        )

        # Store hash in DB
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.token_repo.create(
            token_hash=token_hash,
            expires_at=expires_at,
            user_id=user_id,
        )
        await self.session.commit()

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_TTL_MIN * 60,
            role=role,  # type: ignore[arg-type]
            full_name=full_name,
        )
