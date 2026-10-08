from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from uuid import UUID


class PlanTier(StrEnum):
    FREE = "free"
    FAMILY_PREMIUM = "family_premium"
    CLINIC_SaaS = "clinic_saas"


@dataclass(frozen=True)
class ClinicBedQuota:
    tenant_id: UUID
    active_beds_allowed: int
    current_active_beds: int
    is_active: bool

    @property
    def can_assign_bed(self) -> bool:
        return self.is_active and (self.current_active_beds < self.active_beds_allowed)


@dataclass(frozen=True)
class ClinicianSlaTarget:
    alert_level: str
    max_response_minutes: int
    escalate_to_head_doctor_minutes: int


SLA_POLICY: dict[str, ClinicianSlaTarget] = {
    "red": ClinicianSlaTarget(
        alert_level="red",
        max_response_minutes=15,
        escalate_to_head_doctor_minutes=30,
    ),
    "amber": ClinicianSlaTarget(
        alert_level="amber",
        max_response_minutes=1440,  # 24 hours
        escalate_to_head_doctor_minutes=2880,  # 48 hours
    ),
}


def check_sla_breach(
    alert_level: str,
    created_at: datetime,
    acknowledged_at: datetime | None = None,
    now: datetime | None = None,
) -> tuple[bool, bool]:
    """Returns (is_breached, needs_head_doctor_escalation)."""
    target = SLA_POLICY.get(alert_level.lower())
    if not target:
        return False, False

    current_time = now or datetime.now(timezone.utc)
    effective_end = acknowledged_at or current_time
    duration = effective_end - created_at

    breached = duration > timedelta(minutes=target.max_response_minutes)
    needs_head_doc = duration > timedelta(minutes=target.escalate_to_head_doctor_minutes)
    return breached, needs_head_doc
