from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import AlertResult
from app.core.db import get_db_context
from app.core.metrics import alerts_total
from app.models.alert import Alert
from app.models.patient import Patient
from app.models.reading import Reading
from app.models.task import Task
from app.repositories.alert_repo import AlertRepository

logger = logging.getLogger("wmax.workers.escalation")

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
            Task.status.in_(["created", "sent", "seen"]),
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
            Task.status.in_(["created", "sent", "seen"]),
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
    """Scans all active patients to ensure that missing readings (>=45 min) raise no_data alerts."""
    now = datetime.now(timezone.utc)
    stmt_patients = select(Patient)
    res_p = await session.execute(stmt_patients)
    patients = res_p.scalars().all()

    alert_repo = AlertRepository(session)

    for patient in patients:
        stmt_reading = (
            select(Reading)
            .where(Reading.patient_id == patient.id)
            .order_by(Reading.ts.desc())
            .limit(1)
        )
        res_r = await session.execute(stmt_reading)
        latest_reading = res_r.scalar_one_or_none()

        last_reading_ts = latest_reading.ts if latest_reading else None

        if timewin.is_no_data(last_reading_ts, now):
            # Check latest alert to avoid duplicate alerts within 15 minutes
            latest_alert = await alert_repo.get_latest(patient.id)
            if not latest_alert or (now - latest_alert.ts) > timedelta(minutes=15) or latest_alert.level != "no_data":
                logger.info(
                    "Patient %s has been silent since %s. Logging no_data alert.",
                    patient.id,
                    last_reading_ts,
                )
                await alert_repo.insert_idempotent(
                    patient_id=patient.id,
                    ts=now,
                    result=AlertResult(
                        level="no_data",
                        composite_score=0.0,
                        triggered_params={},
                        reason="silence_no_data",
                    ),
                )
                alerts_total.labels(level="no_data").inc()


async def run_escalation_worker(interval_seconds: int = 60) -> None:
    """Periodic worker routine for reminders, escalations, and silence detection."""
    logger.info("Escalation and silence worker started (interval=%ds).", interval_seconds)
    while True:
        try:
            async with get_db_context() as session:
                await check_task_escalations(session)
                await check_patient_silence(session)
        except asyncio.CancelledError:
            logger.info("Escalation worker received cancellation. Shutting down gracefully.")
            break
        except Exception as e:
            logger.exception("Error in escalation worker cycle: %s", e)

        await asyncio.sleep(interval_seconds)
