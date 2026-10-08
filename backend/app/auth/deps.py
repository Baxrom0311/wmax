from __future__ import annotations

import uuid
from typing import Literal

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.rls import set_rls_context
from app.core.security import decode_token
from app.models import PatientAccess, PatientConsent, TenantMember
from app.schemas.auth import CurrentUser
from app.schemas.common import CLINICIAN_ROLES

security_scheme = HTTPBearer(auto_error=False)

Role = Literal["doctor", "nurse", "admin", "dispatcher"]

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token yaroqsiz yoki muddati o'tgan",
    headers={"WWW-Authenticate": "Bearer"},
)


def _uuid_list(raw: object) -> list[uuid.UUID]:
    if not isinstance(raw, list):
        return []
    values: list[uuid.UUID] = []
    for item in raw:
        try:
            values.append(uuid.UUID(str(item)))
        except (ValueError, TypeError):
            continue
    return values


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

    tenant_ids = _uuid_list(payload.get("tenant_ids"))
    patient_ids = _uuid_list(payload.get("patient_ids"))

    return CurrentUser(
        id=user_id,
        full_name=payload.get("full_name", "Noma'lum"),
        role=role,
        district=payload.get("district"),
        phone=payload.get("phone"),
        tenant_ids=tenant_ids,
        patient_ids=patient_ids,
    )


async def _apply_rls_context(
    principal: CurrentUser, session: AsyncSession | object
) -> CurrentUser:
    if hasattr(session, "execute"):
        db = session  # type: ignore[assignment]
        # Bootstrap PostgreSQL RLS with the signed scope so relationship reads
        # below are visible; then replace it with the current database scope.
        await set_rls_context(
            db,
            account_id=principal.id if principal.role != "patient" else None,
            tenant_ids=principal.tenant_ids,
            patient_ids=principal.patient_ids,
        )
        if principal.role in CLINICIAN_ROLES:
            rows = await db.execute(
                select(TenantMember.tenant_id).where(
                    TenantMember.account_id == principal.id,
                    TenantMember.left_at.is_(None),
                )
            )
            principal.tenant_ids = list(rows.scalars().all())
        elif principal.role == "relative":
            rows = await db.execute(
                select(PatientAccess.patient_id)
                .join(
                    PatientConsent,
                    PatientConsent.patient_id == PatientAccess.patient_id,
                )
                .where(
                    PatientAccess.account_id == principal.id,
                    PatientAccess.accepted_at.is_not(None),
                    PatientAccess.revoked_at.is_(None),
                    PatientConsent.scope == "family_access",
                    PatientConsent.granted.is_(True),
                    PatientConsent.revoked_at.is_(None),
                    PatientConsent.target_account_id == principal.id,
                )
            )
            principal.patient_ids = list(set(rows.scalars().all()))
        elif principal.role == "patient":
            principal.patient_ids = [principal.id]
        await set_rls_context(
            session,  # type: ignore[arg-type]
            account_id=principal.id if principal.role != "patient" else None,
            tenant_ids=principal.tenant_ids,
            patient_ids=principal.patient_ids,
        )
    return principal


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """Any authenticated principal — clinician, caregiver, or patient."""
    return await _apply_rls_context(_decode_bearer(credentials), session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
    session: AsyncSession = Depends(get_session),
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
    return await _apply_rls_context(principal, session)


async def get_current_relative(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """Authenticated caregiver only."""
    principal = _decode_bearer(credentials)
    if principal.role != "relative":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu amalni bajarish uchun yetarli huquq yo'q",
        )
    return await _apply_rls_context(principal, session)


async def get_current_patient(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """Authenticated patient only."""
    principal = _decode_bearer(credentials)
    if principal.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu amalni bajarish uchun yetarli huquq yo'q",
        )
    return await _apply_rls_context(principal, session)


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
require_admin = require_role("admin")
