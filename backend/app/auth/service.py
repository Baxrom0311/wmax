from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.patient import Patient
from app.models.relative import Relative
from app.models import PatientAccess
from app.repositories.alert_repo import AlertRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.relative_repo import RelativeRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, PatientLoginRequest, RelativeLoginRequest, TokenPair
from app.schemas.common import CLINICIAN_ROLES
from app.schemas.relative import RelativeLoginResponse, RelativePatientItem
from app.services.sms import now_utc, send_sms_code, should_return_dev_code

ALLOWED_TOKEN_ROLES: frozenset[str] = CLINICIAN_ROLES | {"relative", "patient"}

# A valid bcrypt hash of an unguessable value, used purely to equalise timing
# on the "no such account" branch.
DUMMY_PASSWORD_HASH = "$2b$12$4HdxV6TY.jIgSenOSWI2OuLghz5KbdKxukZvYzt5iJeMYNjlHBVXu"
DUMMY_PIN_HASH = "$2b$12$Ay8VCjQ80uP/2PYTTPz3ru0/p2Dei8B74mpkKzSWl4NDwtld9qUmC"

# Demo fallback accounts.
# These bypass the user table entirely, so they are only consulted when
# settings.ENABLE_DEMO_ACCOUNTS is on — never in a production deployment.
DEMO_CREDENTIALS: dict[str, dict[str, Any]] = {
    "+998901234567": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "password": "wmax123",
        "full_name": "Dr. Bahrom Alimov",
        "role": "doctor",
        "district": "Urganch",
    },
    "901234567": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "password": "wmax123",
        "full_name": "Dr. Bahrom Alimov",
        "role": "doctor",
        "district": "Urganch",
    },
    "+998901234568": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "password": "wmax123",
        "full_name": "Hamshira Dilnoza",
        "role": "nurse",
        "district": "Xiva",
    },
    "901234568": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "password": "wmax123",
        "full_name": "Hamshira Dilnoza",
        "role": "nurse",
        "district": "Xiva",
    },
}

INVALID_CREDENTIALS_MESSAGE = "Telefon raqami yoki parol noto'g'ri"
INVALID_PIN_MESSAGE = "PIN-kod yoki telefon raqami noto'g'ri"
SMS_CODE_TTL_SECONDS = 300
_SMS_CODES: dict[str, tuple[str, datetime]] = {}


async def _store_sms_code(phone: str, code: str, ttl: int = SMS_CODE_TTL_SECONDS) -> None:
    if getattr(settings, "REDIS_URL", None):
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            async with client:
                await client.setex(f"wmax:sms:{phone}", ttl, f"{code}:0")
                return
        except Exception:
            pass
    expires_at = now_utc() + timedelta(seconds=ttl)
    _SMS_CODES[phone] = (code, expires_at)


async def _verify_sms_code(phone: str, code: str) -> bool:
    if getattr(settings, "REDIS_URL", None):
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            async with client:
                val = await client.get(f"wmax:sms:{phone}")
                if not val:
                    return False
                parts = val.split(":")
                stored_code = parts[0]
                attempts = int(parts[1]) if len(parts) > 1 else 0
                if attempts >= 5:
                    await client.delete(f"wmax:sms:{phone}")
                    return False
                if stored_code != code:
                    await client.set(f"wmax:sms:{phone}", f"{stored_code}:{attempts + 1}", keepttl=True)
                    return False
                await client.delete(f"wmax:sms:{phone}")
                return True
        except Exception:
            pass
    stored = _SMS_CODES.get(phone)
    if not stored or stored[0] != code or stored[1] < now_utc():
        return False
    _SMS_CODES.pop(phone, None)
    return True


class AuthService:
    """Production auth service: DB-backed login, refresh token rotation, revocation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.relative_repo = RelativeRepository(session)
        self.patient_repo = PatientRepository(session)
        self.token_repo = RefreshTokenRepository(session)

    async def request_code(self, phone: str) -> tuple[int, str | None]:
        normalized_phone = phone.strip()
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = now_utc() + timedelta(seconds=SMS_CODE_TTL_SECONDS)
        await _store_sms_code(normalized_phone, code)
        await send_sms_code(phone=normalized_phone, code=code, expires_at=expires_at)
        return SMS_CODE_TTL_SECONDS, code if should_return_dev_code() else None

    async def verify_code(self, phone: str, code: str) -> TokenPair:
        normalized_phone = phone.strip()
        valid = await _verify_sms_code(normalized_phone, code)
        if not valid:
            raise AuthenticationException("SMS kod noto'g'ri yoki muddati o'tgan")

        user = await self.user_repo.get_by_phone(normalized_phone)
        if user:
            tenant_roles = await self.user_repo.accounts.get_active_tenant_roles(user.id)
            role = tenant_roles[0].role if tenant_roles else getattr(user, "role", None)
            if role not in CLINICIAN_ROLES:
                assignments = await self.relative_repo.get_assigned_patients(normalized_phone)
                if assignments:
                    return await self._issue_token_pair(
                        user_id=user.id,
                        full_name=user.full_name,
                        role="relative",
                        district=None,
                        phone=normalized_phone,
                        patient_ids=[patient.id for _access, patient in assignments],
                    )
                pending = (
                    await self.session.execute(
                        select(PatientAccess.id).where(
                            PatientAccess.account_id == user.id,
                            PatientAccess.accepted_at.is_(None),
                            PatientAccess.revoked_at.is_(None),
                        ).limit(1)
                    )
                ).scalar_one_or_none()
                if pending is None:
                    raise AuthenticationException("Klinika yoki taklif qilingan caregiver ruxsati topilmadi")
                # This token can only accept the invitation. It has no patient
                # scope until patient consent and invitation acceptance exist.
                return await self._issue_token_pair(
                    user_id=user.id,
                    full_name=user.full_name,
                    role="relative",
                    district=None,
                    phone=normalized_phone,
                    patient_ids=[],
                )
            return await self._issue_token_pair(
                user_id=user.id,
                full_name=user.full_name,
                role=role,
                district=getattr(user, "district", None),
                phone=normalized_phone,
                tenant_ids=[member.tenant_id for member in tenant_roles],
            )

        assignments = await self.relative_repo.get_assigned_patients(normalized_phone)
        if assignments:
            principal = assignments[0][0]
            principal_id = getattr(principal, "account_id", None) or principal.id
            return await self._issue_token_pair(
                user_id=principal_id,
                full_name=getattr(principal, "full_name", "Qarovchi"),
                role="relative",
                district=None,
                phone=normalized_phone,
                patient_ids=[patient.id for _relative, patient in assignments],
            )

        patient = await self.patient_repo.get_by_phone(normalized_phone)
        if patient:
            return await self._issue_token_pair(
                user_id=patient.id,
                full_name=patient.full_name,
                role="patient",
                district=getattr(patient, "district", None),
                phone=normalized_phone,
                patient_ids=[patient.id],
            )

        raise AuthenticationException("Hisob topilmadi")

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
            if not user.is_active:
                raise AuthenticationException("Hisob faol emas")
            if not verify_password(req.password, user.password_hash):
                raise AuthenticationException(INVALID_CREDENTIALS_MESSAGE)
            tenant_roles = await self.user_repo.accounts.get_active_tenant_roles(user.id)
            tenant_ids = [member.tenant_id for member in tenant_roles]
            user_id = user.id
            full_name = user.full_name
            role = tenant_roles[0].role if tenant_roles else getattr(user, "role", None)
            if role not in CLINICIAN_ROLES:
                raise AuthenticationException("Klinika a'zoligi topilmadi")
            district = getattr(user, "district", None)
        elif settings.ENABLE_DEMO_ACCOUNTS:
            demo = DEMO_CREDENTIALS.get(normalized_phone)
            if not demo or not (
                secrets.compare_digest(str(demo["password"]), req.password)
                or secrets.compare_digest("wmax123", req.password)
            ):
                raise AuthenticationException(INVALID_CREDENTIALS_MESSAGE)
            user_id = demo["id"]  # type: ignore[assignment]
            full_name = demo["full_name"]
            role = demo["role"]
            district = demo["district"]
            tenant_ids = []
        else:
            # Burn a bcrypt round so an unknown phone number is not
            # distinguishable from a wrong password by response time.
            verify_password(req.password, DUMMY_PASSWORD_HASH)
            raise AuthenticationException(INVALID_CREDENTIALS_MESSAGE)

        return await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role=role,
            district=district,
            tenant_ids=tenant_ids,
        )

    async def relative_login(
        self,
        req: RelativeLoginRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> RelativeLoginResponse:
        """Authenticates a caregiver against the bcrypt PIN stored on their record.

        A caregiver is never a clinician: the issued token carries role
        "relative" and is scoped to the patients they are actually linked to.
        """
        normalized_phone = req.phone.strip()
        assignments = await self.relative_repo.get_assigned_patients(normalized_phone)
        if not assignments:
            # Still burn a bcrypt comparison so a missing phone number and a
            # wrong PIN take indistinguishable time.
            verify_password(req.pin, DUMMY_PIN_HASH)
            raise AuthenticationException(INVALID_PIN_MESSAGE)

        matched = next(
            (
                rel
                for rel, _patient in assignments
                if getattr(rel, "pin_hash", None) and verify_password(req.pin, rel.pin_hash)
            ),
            None,
        )
        if matched is None:
            raise AuthenticationException(INVALID_PIN_MESSAGE)

        account_obj = getattr(matched, "account", None)
        user_id = account_obj.id if account_obj else getattr(matched, "account_id", matched.id)
        full_name = getattr(matched, "full_name", "")

        token_pair = await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role="relative",
            district=None,
            phone=normalized_phone,
            patient_ids=[patient.id for _rel, patient in assignments],
        )

        return RelativeLoginResponse(
            **token_pair.model_dump(),
            patients=await self._build_patient_items(assignments),
        )

    async def patient_login(
        self,
        req: PatientLoginRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        """Authenticates a patient using their phone and PIN hash."""
        normalized_phone = req.phone.strip()
        patient = await self.patient_repo.get_by_phone(normalized_phone)
        if not patient or not patient.pin_hash:
            # Burn bcrypt round to equalize timing against timing attacks
            verify_password(req.pin, DUMMY_PIN_HASH)
            raise AuthenticationException(INVALID_PIN_MESSAGE)

        if not verify_password(req.pin, patient.pin_hash):
            raise AuthenticationException(INVALID_PIN_MESSAGE)

        return await self._issue_token_pair(
            user_id=patient.id,
            full_name=patient.full_name,
            role="patient",
            district=patient.district,
            phone=normalized_phone,
            patient_ids=[patient.id],
        )

    async def _build_patient_items(
        self, assignments: list[tuple[Relative, Patient]]
    ) -> list[RelativePatientItem]:
        """Maps a caregiver's linked patients to the portal's list payload."""
        alert_repo = AlertRepository(self.session)
        items: list[RelativePatientItem] = []

        for relative, patient in assignments:
            latest_alert = await alert_repo.get_latest(patient.id)
            items.append(
                RelativePatientItem(
                    id=patient.id,
                    full_name=patient.full_name,
                    relationship=getattr(relative, "relationship", ""),
                    access_token=getattr(relative, "access_token", "") or "",
                    level=latest_alert.level if latest_alert else "no_data",
                    diagnosis=patient.diagnosis or "",
                    age=patient.age or 0,
                    last_reading_at=latest_alert.ts if latest_alert else None,
                )
            )

        return items

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
        role = payload.get("role")
        if role not in ALLOWED_TOKEN_ROLES:
            raise AuthenticationException("Token tarkibi buzuq")
        district = payload.get("district")
        phone = payload.get("phone")
        tenant_ids = [uuid.UUID(item) for item in payload.get("tenant_ids", [])]
        patient_ids = [uuid.UUID(item) for item in payload.get("patient_ids", [])]

        return await self._issue_token_pair(
            user_id=user_id,
            full_name=full_name,
            role=role,
            district=district,
            phone=phone,
            tenant_ids=tenant_ids,
            patient_ids=patient_ids,
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
        phone: str | None = None,
        tenant_ids: list[uuid.UUID] | None = None,
        patient_ids: list[uuid.UUID] | None = None,
    ) -> TokenPair:
        claims = {
            "full_name": full_name,
            "role": role,
            "district": district,
            "phone": phone,
            "tenant_ids": [str(item) for item in tenant_ids or []],
            "patient_ids": [str(item) for item in patient_ids or []],
        }

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

        # Store hash in DB against the owner column matching this principal:
        # staff -> user_id, caregiver -> relative_id, patient -> patient_id.
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        owner: dict[str, uuid.UUID] = {  # noqa: E501
            "patient": {"patient_id": user_id},
        }.get(role, {"user_id": user_id})
        await self.token_repo.create(
            token_hash=token_hash,
            expires_at=expires_at,
            **owner,
        )
        await self.session.commit()

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_TTL_MIN * 60,
            role=role,  # type: ignore[arg-type]
            full_name=full_name,
        )
