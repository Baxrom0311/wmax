from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

AlertLevel = Literal["green", "amber", "red", "no_data"]
TaskKind = Literal["clinical", "technical"]
PromiseLevel = Literal["accountable", "awareness"]


class TargetKind(StrEnum):
    CLINICIAN = "clinician"
    CAREGIVER = "caregiver"
    EMERGENCY_QUEUE = "emergency_queue"


class TenantRole(StrEnum):
    NURSE = "nurse"
    DOCTOR = "doctor"
    HEAD_DOCTOR = "head_doctor"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"


class PlatformRole(StrEnum):
    RESEARCH = "platform_research"
    SUPPORT = "platform_support"


@dataclass(frozen=True)
class CareOwner:
    tenant_id: UUID
    account_id: UUID
    name: str
    licence_active: bool


@dataclass(frozen=True)
class CaregiverRef:
    account_id: UUID
    subscription_active: bool = False


@dataclass(frozen=True)
class PatientState:
    patient_id: UUID
    care_owner: CareOwner | None
    caregivers: tuple[CaregiverRef, ...] = ()
    subscription_active: bool = False


@dataclass(frozen=True)
class Target:
    kind: TargetKind
    account_id: UUID | None = None
    tenant_id: UUID | None = None
    patient_id: UUID | None = None


@dataclass(frozen=True)
class TenantMembership:
    tenant_id: UUID
    role: TenantRole
    mahallas: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ViewerContext:
    account_id: UUID | None
    tenant_memberships: tuple[TenantMembership, ...] = ()
    patient_access_ids: frozenset[UUID] = frozenset()
    platform_role: PlatformRole | None = None
    support_reason: str | None = None


@dataclass(frozen=True)
class AccessScope:
    tenant_ids: frozenset[UUID] = frozenset()
    mahallas: frozenset[str] = frozenset()
    patient_ids: frozenset[UUID] = frozenset()
    all_patients: bool = False
    anonymized: bool = False
    support_reason: str | None = None


@dataclass(frozen=True)
class Gap:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class DataQuality:
    score: float
    days_with_data: int
    days_total: int
    gaps: tuple[Gap, ...] = ()
    anomalies: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssignmentWindow:
    device_id: str
    patient_id: UUID
    assigned_at: datetime
    released_at: datetime | None = None


@dataclass(frozen=True)
class Membership:
    patient_id: UUID
    tenant_id: UUID
    granted_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date


@dataclass(frozen=True)
class PatientDayReport:
    period: DateRange
    patient_days_total: int
    patient_days_with_data: int
    patient_days: frozenset[tuple[UUID, date]]


@dataclass(frozen=True)
class Licence:
    device_count: int
    min_days_per_device: int
    price_per_patient_day_uzs: int


@dataclass(frozen=True)
class InvoiceLines:
    patient_days_total: int
    patient_days_with_data: int
    min_commitment: int
    billed_days: int
    amount_uzs: int
