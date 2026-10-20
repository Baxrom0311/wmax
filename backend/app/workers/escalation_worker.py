from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import AlertResult
from app.core.db import get_db_context
from app.core.metrics import alerts_total
from app.models.patient import Patient
from app.models.reading import Reading
from app.models.task import Task
from app.repositories.alert_repo import AlertRepository
from app.repositories.reading_repo import usable_reading_clause
from app.services.live_event_service import LiveEventService
from app.services.monitoring_policy import clinical_consent, monitoring_patient_ids
from app.services.notification_service import queue_alert_notifications
from app.services.task_routing import retry_unassigned, route_alert_task

logger = logging.getLogger("wmax.workers.escalation")
OPEN_TASK_STATUSES = ("open", "acknowledged")

# This worker only advances state. The notifier service watches `reminded_at`,
# `escalated_at` and `no_data` alerts and does the actual messaging.


async def check_task_escalations(session: AsyncSession) -> None:
    """Checks open tasks for 20-hour reminders and 24-hour escalations."""
    now = datetime.now(timezone.utc)

    # 1. Reminders: tasks due within 4 hours (e.g., 20h mark for 24h task) that haven't been reminded
    remind_threshold = now + timedelta(hours=4)
    stmt_remind = (
        select(Task)
        .where(
            exists().where(Patient.id == Task.patient_id, Patient.deceased_at.is_(None)),
            Task.kind == "clinical",
            clinical_consent(Task.patient_id, Task.tenant_id),
            Task.status.in_(OPEN_TASK_STATUSES),
            Task.due_at <= remind_threshold,
            Task.due_at > now,
            Task.reminded_at.is_(None),
        )
    )
    res_remind = await session.execute(stmt_remind)
    tasks_to_remind = res_remind.scalars().all()

    for task in tasks_to_remind:
        logger.warning(
            "Task %s for patient %s is due soon at %s. Sending 20h reminder.",
            task.id,
            task.patient_id,
            task.due_at.isoformat(),
        )
        task.reminded_at = now

    # 2. Overdue / Escalations: tasks past due_at that haven't been escalated
    stmt_escalate = (
        select(Task)
        .where(
            exists().where(Patient.id == Task.patient_id, Patient.deceased_at.is_(None)),
            Task.kind == "clinical",
            clinical_consent(Task.patient_id, Task.tenant_id),
            Task.status.in_(OPEN_TASK_STATUSES),
            Task.due_at <= now,
            Task.escalated_at.is_(None),
        )
    )
    res_escalate = await session.execute(stmt_escalate)
    tasks_to_escalate = res_escalate.scalars().all()

    for task in tasks_to_escalate:
        logger.error(
            "Task %s for patient %s expired at %s — marked overdue for escalation.",
            task.id,
            task.patient_id,
            task.due_at.isoformat(),
        )
        task.escalated_at = now
        task.status = "overdue"

    await session.commit()


async def check_patient_silence(session: AsyncSession) -> None:
    """Raise one no_data alert (and a technical check task) when a monitored
    patient's last *usable* reading is older than the silence threshold."""
    now = datetime.now(timezone.utc)
    stmt_patients = select(Patient).where(Patient.id.in_(monitoring_patient_ids()))
    patients = (await session.execute(stmt_patients)).scalars().all()

    alert_repo = AlertRepository(session)

    for patient in patients:
        last_reading_ts = (await session.execute(
            select(Reading.window_start)
            .where(Reading.patient_id == patient.id, usable_reading_clause())
            .order_by(Reading.window_start.desc())
            .limit(1)
        )).scalar_one_or_none()
        if not timewin.is_no_data(last_reading_ts, now):
            continue

        # Only the transition into silence is an event. Repeating it every
        # cycle would re-notify the family about the same silent watch.
        latest_alert = await alert_repo.get_latest(patient.id)
        if latest_alert is not None and latest_alert.level == "no_data":
            continue
        logger.info("Patient %s has been silent since %s. Logging no_data alert.", patient.id, last_reading_ts)
        alert = await alert_repo.insert_idempotent(
            patient_id=patient.id,
            ts=now,
            result=AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            ),
        )
        if alert is not None:
            await LiveEventService(session).publish_alert(alert)
            await route_alert_task(session, alert, "technical")
            await queue_alert_notifications(session, alert, patient)
            alerts_total.labels(level="no_data").inc()
    await session.commit()


async def retry_unassigned_alerts(session: AsyncSession) -> None:
    routed = await retry_unassigned(session)
    if routed:
        logger.info("Routed %s previously unassigned alerts", routed)
    await session.commit()


async def run_escalation_worker(interval_seconds: int = 60) -> None:
    """Periodic worker routine for reminders, escalations, and silence detection."""
    logger.info("Escalation and silence worker started (interval=%ds).", interval_seconds)
    while True:
        try:
            async with get_db_context() as session:
                await check_task_escalations(session)
                await check_patient_silence(session)
                await retry_unassigned_alerts(session)
        except asyncio.CancelledError:
            logger.info("Escalation worker received cancellation. Shutting down gracefully.")
            break
        except Exception as e:
            logger.exception("Error in escalation worker cycle: %s", e)

        await asyncio.sleep(interval_seconds)
