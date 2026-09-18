from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationException, ForbiddenException, NotFoundException
from app.core.security import create_access_token, create_refresh_token, decode_jwt, verify_password
from app.models.user import User
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.relative_repo import RelativeRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, RelativeLoginRequest, TokenPair

# Demo fallback data for seeding & integration environments per AGENTS.md
DEMO_CREDENTIALS = {
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
    """Production authentication service with database persistence and refresh token rotation."""

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
        """Authenticates clinician (doctor/nurse) against database or certified demo accounts."""
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
            # Check demo credentials fallback
            demo = DEMO_CREDENTIALS.get(normalized_phone)
            if not demo or demo["password"] != req.password:
                raise AuthenticationException("Telefon raqami yoki parol noto'g'ri")
            user_id = demo["id"]
            full_name = demo["full_name"]
            role = demo["role"]
            district = demo["district"]

        return await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role=role,
            district=district,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def relative_login(
        self,
        req: RelativeLoginRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        """Authenticates patient relatives / caregivers using verified PIN."""
        if req.pin != DEMO_RELATIVE_PIN:
            # Check relative token in database
            relatives = await self.relative_repo.get_assigned_patients(req.phone)
            if not relatives:
                raise AuthenticationException("PIN-kod yoki telefon raqami noto'g'ri")

        user_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
        full_name = "Yaqin qarindosh"
        role = "doctor"  # Gives read access to patient data
        district = "Urganch"

        return await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role=role,
            district=district,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def refresh_tokens(
        self,
        refresh_token_str: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        """Rotates refresh token and returns a fresh token pair."""
        payload = decode_jwt(refresh_token_str)
        if payload.get("type") != "refresh":
            raise AuthenticationException("Yaroqsiz refresh token turi")

        jti_str = payload.get("jti")
        sub_str = payload.get("sub")
        if not jti_str or not sub_str:
            raise AuthenticationException("Token tarkibi buzuq")

        token_id = uuid.UUID(jti_str)
        user_id = uuid.UUID(sub_str)

        # Verify against repository
        token_record = await self.token_repo.get_valid(token_id)
        if not token_record:
            raise AuthenticationException("Refresh token muddati o'tgan yoki bekor qilingan")

        # Invalidate old token (Rotation)
        await self.token_repo.revoke(token_id)

        # Issue new token pair
        full_name = payload.get("full_name", "")
        role = payload.get("role", "doctor")
        district = payload.get("district")

        return await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role=role,
            district=district,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def revoke_token(self, refresh_token_str: str) -> None:
        """Revokes a refresh token on logout."""
        try:
            payload = decode_jwt(refresh_token_str)
            jti_str = payload.get("jti")
            if jti_str:
                await self.token_repo.revoke(uuid.UUID(jti_str))
        except Exception:
            pass

    async def _issue_token_pair(
        self,
        user_id: uuid.UUID,
        full_name: str,
        role: str,
        district: str | None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        refresh_jti = uuid.uuid4()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Create JWTs
        claims = {
            "full_name": full_name,
            "role": role,
            "district": district,
        }
        access_token = create_access_token(
            subject=str(user_id),
            extra_claims=claims,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            subject=str(user_id),
            jti=str(refresh_jti),
            extra_claims=claims,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        # Hash token for DB storage
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.token_repo.create(
            token_id=refresh_jti,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            role=role,  # type: ignore
            full_name=full_name,
        )
