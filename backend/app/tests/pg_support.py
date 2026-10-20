"""Disposable-PostgreSQL support for workflow regression tests.

Set WMAX_TEST_DATABASE_URL to an *explicitly disposable* database that has
been migrated with `alembic upgrade head`. Each test runs inside one outer
transaction that is rolled back, so service-level commits become savepoints.
Without the variable these tests are skipped: SQLite/mocks cannot validate the
PostgreSQL SQL, constraints and partial indexes these workflows depend on.
"""
from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.security import create_access_token
from app.models import (
    Account,
    AccountIdentity,
    Device,
    DeviceAssignment,
    MemberTerritory,
    Patient,
    PatientAccess,
    PatientAddress,
    PatientConsent,
    PatientMembership,
    Tenant,
    TenantMember,
)

PG_URL = os.getenv("WMAX_TEST_DATABASE_URL")

requires_pg = pytest.mark.skipif(
    not PG_URL, reason="WMAX_TEST_DATABASE_URL (disposable, migrated PostgreSQL) not set"
)


@asynccontextmanager
async def rollback_session():
    engine = create_async_engine(PG_URL, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            outer = await connection.begin()
            session = AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
                autoflush=False,
            )
            try:
                yield session
            finally:
                await session.close()
                await outer.rollback()
    finally:
        await engine.dispose()


def _phone() -> str:
    return "+99890" + str(uuid.uuid4().int)[:7]


@dataclass
class World:
    """Small synthetic clinic graph. Never contains real patient data."""

    session: AsyncSession

    async def tenant(self, name: str = "Test OvaBMU") -> Tenant:
        tenant = Tenant(kind="ovabmu", name=f"{name} {uuid.uuid4().hex[:6]}", region="Xorazm", district="Urganch")
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def account(self, name: str = "Synthetic Staff", *, telegram: str | None = None) -> Account:
        account = Account(phone=_phone(), full_name=name, is_active=True)
        self.session.add(account)
        await self.session.flush()
        if telegram:
            self.session.add(AccountIdentity(
                account_id=account.id, provider="telegram", external_id=telegram,
                verified_at=datetime.now(timezone.utc),
            ))
            await self.session.flush()
        return account

    async def member(
        self, tenant: Tenant, role: str, *, mahallas: tuple[str, ...] = (),
        account: Account | None = None, telegram: str | None = None,
    ) -> tuple[Account, TenantMember]:
        account = account or await self.account(f"Synthetic {role}", telegram=telegram)
        member = TenantMember(tenant_id=tenant.id, account_id=account.id, role=role)
        self.session.add(member)
        await self.session.flush()
        for mahalla in mahallas:
            self.session.add(MemberTerritory(tenant_member_id=member.id, mahalla=mahalla))
        await self.session.flush()
        return account, member

    async def patient(
        self, tenant: Tenant | None, *, mahalla: str | None = "Navbahor", consent: bool = True,
    ) -> Patient:
        patient = Patient(full_name=f"Synthetic Patient {uuid.uuid4().hex[:6]}", district="Urganch")
        self.session.add(patient)
        await self.session.flush()
        if mahalla:
            self.session.add(PatientAddress(
                patient_id=patient.id, region="Xorazm", district="Urganch", mahalla=mahalla, is_primary=True,
            ))
        if tenant is not None:
            self.session.add(PatientMembership(patient_id=patient.id, tenant_id=tenant.id, kind="care"))
            if consent:
                self.session.add(PatientConsent(
                    patient_id=patient.id, scope="clinical_monitoring", granted=True,
                    method="verbal_by_clinician", target_tenant_id=tenant.id,
                ))
        await self.session.flush()
        return patient

    async def caregiver(self, patient: Patient, *, telegram: str | None = None) -> Account:
        account = await self.account("Synthetic Caregiver", telegram=telegram)
        self.session.add(PatientAccess(
            patient_id=patient.id, account_id=account.id, relation="child",
            accepted_at=datetime.now(timezone.utc),
        ))
        self.session.add(PatientConsent(
            patient_id=patient.id, scope="family_access", granted=True, method="in_app",
            target_account_id=account.id,
        ))
        await self.session.flush()
        return account

    async def device(self, patient: Patient, *, since: timedelta = timedelta(days=8)) -> Device:
        device = Device(serial=f"SYN-{uuid.uuid4().hex[:10]}", model="synthetic-watch", status="assigned")
        self.session.add(device)
        await self.session.flush()
        self.session.add(DeviceAssignment(
            device_id=device.id, patient_id=patient.id,
            assigned_at=datetime.now(timezone.utc) - since,
        ))
        await self.session.flush()
        return device


def bearer(account: Account, role: str, *, tenant_ids=(), patient_ids=(), minutes: int = 15) -> str:
    return create_access_token(
        subject=str(account.id),
        claims={
            "role": role,
            "full_name": account.full_name,
            "tenant_ids": [str(item) for item in tenant_ids],
            "patient_ids": [str(item) for item in patient_ids],
        },
        expires_delta=timedelta(minutes=minutes),
    )
