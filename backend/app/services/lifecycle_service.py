"""IDEOLOGY J2: once a death is recorded everything stops — from one place.

Stops: open/overdue tasks, pending notifications, subscriptions, device
credentials and assignments. Workers, ingest and delivery also consult
`deceased_at`, so nothing re-starts later.
Keeps: all records (K1), clinic memberships, and the family's read-only
history for FAMILY_HISTORY_AFTER_DEATH (consents are not revoked).
Creates: a technical "return the device" task for the responsible clinician.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DeviceAssignment,
    DeviceCredential,
    Patient,
    PatientSubscription,
    ProfileAudit,
    Task,
)
from app.repositories.task_repo import TaskRepository
from app.services.live_event_service import LiveEventService
from app.services.notification_service import cancel_patient_notifications
from app.services.task_routing import care_tenant_id, responsible_clinician


async def mark_deceased(session: AsyncSession, patient: Patient, *, actor_id: uuid.UUID) -> dict[str, Any]:
    if patient.deceased_at is not None:
        return {"device_return_task_id": None}
    now = datetime.now(timezone.utc)
    patient.deceased_at = now
    patient.deceased_marked_by = actor_id
    events = LiveEventService(session)

    tasks = (await session.execute(
        select(Task).where(Task.patient_id == patient.id, Task.status.in_(("open", "acknowledged", "overdue")))
    )).scalars().all()
    for task in tasks:
        task.status = "cancelled"
        await events.publish_task(task, action="cancelled")

    await cancel_patient_notifications(session, patient.id)

    subscriptions = (await session.execute(
        select(PatientSubscription).where(PatientSubscription.patient_id == patient.id)
    )).scalars().all()
    for subscription in subscriptions:
        subscription.status = "lapsed"

    assignments = (await session.execute(
        select(DeviceAssignment).where(
            DeviceAssignment.patient_id == patient.id,
            DeviceAssignment.released_at.is_(None),
        )
    )).scalars().all()
    for assignment in assignments:
        assignment.released_at = now
        credentials = (await session.execute(
            select(DeviceCredential).where(
                DeviceCredential.device_id == assignment.device_id,
                DeviceCredential.revoked_at.is_(None),
            )
        )).scalars().all()
        for credential in credentials:
            credential.revoked_at = now

    device_task = None
    tenant_id = await care_tenant_id(session, patient.id)
    if assignments and tenant_id is not None:
        assignee_id = await responsible_clinician(session, patient.id, tenant_id, "technical")
        if assignee_id is not None:
            device_task = await TaskRepository(session).create_task(
                patient_id=patient.id,
                tenant_id=tenant_id,
                assignee_account_id=assignee_id,
                due_at=None,
                kind="technical",
                note="Qurilmani oiladan qaytarib olish va qayta ishlatishga tayyorlash.",
            )
            await events.publish_task(device_task, action="created")

    session.add(ProfileAudit(
        patient_id=patient.id, actor_kind="clinician", actor_id=actor_id,
        entity="patient", entity_id=str(patient.id), action="deceased",
        changes={"cancelled_tasks": len(tasks), "released_devices": len(assignments)},
    ))
    await session.flush()
    return {"device_return_task_id": device_task.id if device_task else None}
