"""Turn an amber/red/no_data alert into a task for one responsible clinician.

D5: no task without an eligible, explicitly responsible assignee. B6: the
assignee comes from the same territory rule that decides visibility. F2: low
quality data asks for a technical check, never a clinical deadline. When nobody
is responsible the alert keeps `task_routing_status = 'unassigned'`, which
operators can see and the escalation worker retries.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, literal, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clinical_scope import TERRITORY_ROLES, clinician_patient_ids
from app.models import Alert, Patient, PatientMembership, Task, TenantMember
from app.repositories.task_repo import OPEN_TASK_STATUSES, TaskRepository
from app.services.live_event_service import LiveEventService
from app.services.monitoring_policy import clinical_consent

logger = logging.getLogger(__name__)

CLINICAL_DUE = {"red": timedelta(hours=2), "amber": timedelta(hours=24)}
TASK_NOTES = {
    "clinical": "Avtomatik klinik signal: {level}. Bemor bilan bog'laning.",
    "technical": "Ma'lumot sifati past yoki o'lchov yo'q: soat taqilganini va ulanishini tekshiring.",
}


async def care_tenant_id(session: AsyncSession, patient_id: Any):
    """The consented care owner clinic, or None (C1/C2: no owner, no task)."""
    return (await session.execute(
        select(PatientMembership.tenant_id).where(
            PatientMembership.patient_id == patient_id,
            PatientMembership.kind == "care",
            PatientMembership.revoked_at.is_(None),
            clinical_consent(patient_id, PatientMembership.tenant_id),
        )
    )).scalar_one_or_none()


async def responsible_clinician(session: AsyncSession, patient_id: Any, tenant_id: Any, kind: str):
    """Doctor or nurse whose territory covers the patient's primary address."""
    preference = ("nurse", "doctor") if kind == "technical" else ("doctor", "nurse")
    member = (await session.execute(
        select(TenantMember)
        .where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.left_at.is_(None),
            TenantMember.role.in_(TERRITORY_ROLES),
            # Correlated per member: same rule as worklist visibility.
            literal(patient_id, PGUUID(as_uuid=True)).in_(
                clinician_patient_ids(TenantMember.account_id, [tenant_id])
            ),
        )
        .order_by(
            case((TenantMember.role == preference[0], 0), else_=1),
            TenantMember.joined_at.asc(),
        )
        .limit(1)
    )).scalar_one_or_none()
    return member.account_id if member else None


async def route_alert_task(session: AsyncSession, alert: Alert, kind: str) -> Task | None:
    alert.task_kind = kind
    tenant_id = await care_tenant_id(session, alert.patient_id)
    if tenant_id is None:
        alert.task_routing_status = "not_required"
        alert.task_routing_error = "no_consented_care_owner"
        return None

    existing = (await session.execute(
        select(Task.id).where(
            Task.patient_id == alert.patient_id,
            Task.tenant_id == tenant_id,
            Task.kind == kind,
            Task.status.in_(OPEN_TASK_STATUSES),
        ).limit(1)
    )).scalar_one_or_none()
    if existing is not None:
        alert.task_routing_status = "open_task_exists"
        alert.task_routing_error = None
        return None

    assignee_id = await responsible_clinician(session, alert.patient_id, tenant_id, kind)
    if assignee_id is None:
        alert.task_routing_status = "unassigned"
        alert.task_routing_error = "no_responsible_clinician_for_mahalla"
        logger.warning("Alert %s for patient %s has no responsible clinician", alert.id, alert.patient_id)
        return None

    due = CLINICAL_DUE.get(alert.level) if kind == "clinical" else None
    task = await TaskRepository(session).create_task(
        patient_id=alert.patient_id,
        tenant_id=tenant_id,
        assignee_account_id=assignee_id,
        # Technical checks carry no clinical deadline and never escalate.
        due_at=datetime.now(timezone.utc) + due if due else None,
        kind=kind,
        alert_id=alert.id,
        note=TASK_NOTES[kind].format(level=alert.level.upper()),
    )
    alert.task_routing_status = "routed"
    alert.task_routing_error = None
    await LiveEventService(session).publish_task(task, action="created")
    return task


async def retry_unassigned(session: AsyncSession, *, max_age: timedelta = timedelta(hours=24)) -> int:
    """Retry routing once someone has been made responsible for the mahalla."""
    alerts = (await session.execute(
        select(Alert)
        .join(Patient, Patient.id == Alert.patient_id)
        .where(
            Alert.task_routing_status == "unassigned",
            Alert.ts >= datetime.now(timezone.utc) - max_age,
            Patient.deceased_at.is_(None),
        )
        .order_by(Alert.ts.asc())
        .limit(200)
    )).scalars().all()
    routed = 0
    for alert in alerts:
        if await route_alert_task(session, alert, alert.task_kind or "clinical") is not None:
            routed += 1
    return routed
