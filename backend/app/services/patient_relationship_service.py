from __future__ import annotations

import uuid
import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models import Account, Patient, PatientAccess, PatientConsent, PatientMembership, Tenant


class PatientRelationshipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_membership(
        self,
        *,
        patient_id: uuid.UUID,
        tenant_id: uuid.UUID,
        kind: str,
        granted_by: uuid.UUID,
    ) -> dict[str, Any]:
        await self._require_patient(patient_id)
        if not await self.session.get(Tenant, tenant_id):
            raise NotFoundException("Klinika", tenant_id)

        existing = (
            await self.session.execute(
                select(PatientMembership).where(
                    PatientMembership.patient_id == patient_id,
                    PatientMembership.tenant_id == tenant_id,
                    PatientMembership.kind == kind,
                    PatientMembership.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing:
            return self._membership_dict(existing)

        if kind == "care":
            care_owner = (
                await self.session.execute(
                    select(PatientMembership).where(
                        PatientMembership.patient_id == patient_id,
                        PatientMembership.kind == "care",
                        PatientMembership.revoked_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if care_owner:
                raise ConflictException("Bemor allaqachon faol care a'zolikka ega")

        membership = PatientMembership(
            patient_id=patient_id,
            tenant_id=tenant_id,
            kind=kind,
            granted_by=granted_by,
        )
        self.session.add(membership)
        await self.session.flush()
        await self.session.commit()
        return self._membership_dict(membership)

    async def revoke_membership(
        self, *, patient_id: uuid.UUID, membership_id: uuid.UUID
    ) -> dict[str, Any]:
        membership = await self.session.get(PatientMembership, membership_id)
        if not membership or membership.patient_id != patient_id:
            raise NotFoundException("A'zolik", membership_id)
        if membership.revoked_at is None:
            membership.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.commit()
        return {"id": str(membership_id), "revoked_at": membership.revoked_at.isoformat()}

    async def invite_access(
        self,
        *,
        patient_id: uuid.UUID,
        phone: str,
        full_name: str,
        role: str,
        relation: str | None,
        invited_by: uuid.UUID,
    ) -> dict[str, Any]:
        await self._require_patient(patient_id)
        account = (
            await self.session.execute(select(Account).where(Account.phone == phone))
        ).scalar_one_or_none()
        if not account:
            account = Account(phone=phone, full_name=full_name)
            self.session.add(account)
            await self.session.flush()

        existing = (
            await self.session.execute(
                select(PatientAccess).where(
                    PatientAccess.patient_id == patient_id,
                    PatientAccess.account_id == account.id,
                    PatientAccess.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing:
            if not existing.access_token:
                existing.access_token = secrets.token_urlsafe(32)
                existing.access_token_created_at = datetime.now(timezone.utc)
                await self.session.commit()
            return self._access_dict(existing)

        access = PatientAccess(
            patient_id=patient_id,
            account_id=account.id,
            role=role,
            relation=relation,
            invited_by=invited_by,
            access_token=secrets.token_urlsafe(32),
            access_token_created_at=datetime.now(timezone.utc),
        )
        self.session.add(access)
        await self.session.flush()
        await self.session.commit()
        return self._access_dict(access)

    async def revoke_access(
        self, *, patient_id: uuid.UUID, access_id: uuid.UUID
    ) -> dict[str, Any]:
        access = await self.session.get(PatientAccess, access_id)
        if not access or access.patient_id != patient_id:
            raise NotFoundException("Ruxsat", access_id)
        if access.revoked_at is None:
            access.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.commit()
        return {"id": str(access_id), "revoked_at": access.revoked_at.isoformat()}

    async def create_consent(
        self,
        *,
        patient_id: uuid.UUID,
        scope: str,
        granted: bool,
        method: str,
        witnessed_by: uuid.UUID,
        target_account_id: uuid.UUID | None,
        target_tenant_id: uuid.UUID | None,
    ) -> dict[str, Any]:
        await self._require_patient(patient_id)
        if target_account_id is not None and not await self.session.get(Account, target_account_id):
            raise NotFoundException("Hisob", target_account_id)
        if target_tenant_id is not None and not await self.session.get(Tenant, target_tenant_id):
            raise NotFoundException("Klinika", target_tenant_id)

        consent = PatientConsent(
            patient_id=patient_id,
            scope=scope,
            granted=granted,
            method=method,
            witnessed_by=witnessed_by,
            target_account_id=target_account_id,
            target_tenant_id=target_tenant_id,
        )
        self.session.add(consent)
        await self.session.flush()
        await self.session.commit()
        return {"id": str(consent.id), "scope": consent.scope, "granted": consent.granted}

    async def revoke_consent(
        self, *, patient_id: uuid.UUID, consent_id: uuid.UUID
    ) -> dict[str, Any]:
        consent = await self.session.get(PatientConsent, consent_id)
        if not consent or consent.patient_id != patient_id:
            raise NotFoundException("Rozilik", consent_id)
        if consent.revoked_at is None:
            consent.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.commit()
        return {"id": str(consent_id), "revoked_at": consent.revoked_at.isoformat()}

    def _membership_dict(self, membership: PatientMembership) -> dict[str, Any]:
        return {
            "id": str(membership.id),
            "patient_id": str(membership.patient_id),
            "tenant_id": str(membership.tenant_id),
            "kind": membership.kind,
        }

    async def _require_patient(self, patient_id: uuid.UUID) -> Patient:
        patient = await self.session.get(Patient, patient_id)
        if not patient:
            raise NotFoundException("Bemor", patient_id)
        return patient

    def _access_dict(self, access: PatientAccess) -> dict[str, Any]:
        return {
            "id": str(access.id),
            "patient_id": str(access.patient_id),
            "account_id": str(access.account_id),
            "role": access.role,
            "access_token": access.access_token,
        }
