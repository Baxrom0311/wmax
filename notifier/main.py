"""WMAX notifier: turns clinical state changes into Telegram messages.

Division of labour with the API's background workers:
  * `app.workers.escalation_worker` owns the **state machine** — it stamps
    `reminded_at`, `escalated_at`, flips tasks to `overdue`, and writes
    `no_data` alerts.
  * this service owns **delivery** — it reads those state changes and messages
    caregivers and duty staff, then records the send in `notifications`.

Keeping writes in one place avoids two processes racing on the same rows.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import exists, select

from app.core.db import get_db_context
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.task import Task
from app.models.user import User
from app.models.schema import (
    Account,
    AccountIdentity,
    NotificationAttempt,
    PatientAccess,
    PatientConsent,
    PatientMembership,
    TenantMember,
)

from .admin_store import get_all_admins
from .state import already_sent, mark_sent
from .telegram import (
    format_active_call_reminder,
    format_doctor_alert,
    format_no_data_alert,
    format_overdue_escalation,
    format_relative_alert,
    poll_telegram_messages,
    send_telegram_message,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("wmax.notifier")

ALERT_COOLDOWN_HOURS = int(os.getenv("ALERT_COOLDOWN_HOURS", "6"))
NO_DATA_MINUTES = int(os.getenv("NO_DATA_MINUTES", "45"))

def _admin_chat_ids() -> list[int]:
    """Telegram chat ids of registered duty staff (super admin included)."""
    return [int(admin["id"]) for admin in get_all_admins() if admin.get("id")]


async def _staff_chat_ids(session, patient_id) -> list[str]:
    """Resolve currently active clinical staff assigned to this patient's clinic."""
    stmt = (
        select(AccountIdentity.external_id)
        .join(TenantMember, TenantMember.account_id == AccountIdentity.account_id)
        .join(PatientMembership, PatientMembership.tenant_id == TenantMember.tenant_id)
        .where(
            PatientMembership.patient_id == patient_id,
            PatientMembership.revoked_at.is_(None),
            TenantMember.left_at.is_(None),
            TenantMember.role.in_(["doctor", "head_doctor", "nurse", "dispatcher"]),
            AccountIdentity.provider == "telegram",
            AccountIdentity.verified_at.is_not(None),
        )
        .distinct()
    )
    return list((await session.execute(stmt)).scalars().all())


async def _relative_chat_ids(session, patient_id) -> list[str]:
    """Resolve only accepted caregivers with active, patient-approved consent."""
    stmt = (
        select(AccountIdentity.external_id)
        .join(PatientAccess, PatientAccess.account_id == AccountIdentity.account_id)
        .join(PatientConsent, PatientConsent.patient_id == PatientAccess.patient_id)
        .where(
            PatientAccess.patient_id == patient_id,
            PatientAccess.accepted_at.is_not(None),
            PatientAccess.revoked_at.is_(None),
            PatientConsent.target_account_id == PatientAccess.account_id,
            PatientConsent.scope == "family_access",
            PatientConsent.granted.is_(True),
            PatientConsent.revoked_at.is_(None),
            AccountIdentity.provider == "telegram",
            AccountIdentity.verified_at.is_not(None),
        )
        .distinct()
    )
    return list((await session.execute(stmt)).scalars().all())


async def _broadcast_to_staff(session, patient_id, text: str) -> bool:
    """Sends only to verified Telegram identities in the patient's active clinic."""
    chat_ids = await _staff_chat_ids(session, patient_id)
    if not chat_ids:
        logger.warning("No authorized Telegram staff recipient for patient %s", patient_id)
        return False

    results = await asyncio.gather(
        *(send_telegram_message(chat_id, text) for chat_id in chat_ids)
    )
    return any(results)


async def check_task_escalations() -> None:
    """Job 1: messages staff about 20h active-call reminders and 24h overdue tasks."""
    async with get_db_context() as session:
        stmt = (
            select(Task, Patient)
            .join(Patient, Task.patient_id == Patient.id)
            .where(
                (Task.reminded_at.is_not(None) & Task.reminder_notified_at.is_(None))
                | (Task.escalated_at.is_not(None) & Task.escalation_notified_at.is_(None)),
                Patient.deceased_at.is_(None),
            )
        )
        rows = (await session.execute(stmt)).all()

        for task, patient in rows:
            if task.escalated_at and task.escalation_notified_at is None:
                key = f"task_overdue:{task.id}"
                if not already_sent(key):
                    doctor_name = None
                    assignee_id = getattr(task, "assignee_account_id", None) or getattr(task, "doctor_id", None)
                    if assignee_id:
                        doctor = await session.get(Account, assignee_id) or await session.get(User, assignee_id)
                        doctor_name = doctor.full_name if doctor else None

                    text = format_overdue_escalation(
                        patient_name=patient.full_name,
                        doctor_name=doctor_name,
                        district=patient.district,
                    )
                    if await _broadcast_to_staff(session, patient.id, text):
                        task.escalation_notified_at = datetime.now(timezone.utc)
                        mark_sent(key, task.escalated_at.isoformat())
                        logger.warning(
                            "Escalation delivered for overdue task %s (patient %s).",
                            task.id,
                            patient.id,
                        )
                continue

            if task.reminded_at and task.reminder_notified_at is None:
                key = f"task_reminder:{task.id}"
                if already_sent(key):
                    continue

                hours_left = max(
                    0,
                    int((task.due_at - datetime.now(timezone.utc)).total_seconds() // 3600),
                )
                text = format_active_call_reminder(
                    patient_name=patient.full_name, due_in_hours=hours_left
                )
                if await _broadcast_to_staff(session, patient.id, text):
                    task.reminder_notified_at = datetime.now(timezone.utc)
                    mark_sent(key, task.reminded_at.isoformat())
                    logger.info(
                        "Reminder delivered for task %s (patient %s, %sh left).",
                        task.id,
                        patient.id,
                        hours_left,
                    )


async def check_alert_signals() -> None:
    """Job 2: messages caregivers and staff about fresh amber/red alerts."""
    now = datetime.now(timezone.utc)
    cooldown_cutoff = now - timedelta(hours=ALERT_COOLDOWN_HOURS)

    async with get_db_context() as session:
        stmt = (
            select(Alert, Patient)
            .join(Patient, Alert.patient_id == Patient.id)
            .where(
                Alert.level.in_(["amber", "red"]),
                Patient.deceased_at.is_(None),
                ~exists().where(Notification.alert_id == Alert.id),
            )
            .order_by(Alert.ts.desc())
        )
        rows = (await session.execute(stmt)).all()

        for alert, patient in rows:
            key = f"alert:{alert.id}"
            if already_sent(key):
                continue

            # Per-patient cooldown:
            # Severity escalation: Amber alert must NEVER suppress a subsequent RED alert.
            # RED alerts use a 15-minute cooldown; Amber alerts use ALERT_COOLDOWN_HOURS.
            effective_cutoff = (
                now - timedelta(minutes=15)
                if alert.level == "red"
                else cooldown_cutoff
            )
            stmt_cooldown = (
                select(Notification)
                .where(
                    Notification.patient_id == patient.id,
                    Notification.created_at >= effective_cutoff,
                )
            )
            if alert.level == "red":
                # For red alerts, only suppress if another RED notification was sent recently
                stmt_cooldown = stmt_cooldown.where(Notification.level == "red")

            recent_notification = (
                await session.execute(stmt_cooldown.limit(1))
            ).scalar_one_or_none()
            if recent_notification:
                mark_sent(key, alert.ts.isoformat())
                logger.debug(
                    "Alert %s suppressed by cooldown for patient %s.",
                    alert.id,
                    patient.id,
                )
                continue

            delivered_to: list[str] = []

            # Caregivers: plain language, no diagnosis, link to their portal.
            relative_chat_ids = await _relative_chat_ids(session, patient.id)
            for chat_id in relative_chat_ids:
                sent = await send_telegram_message(
                    chat_id,
                    format_relative_alert(
                        patient_name=patient.full_name,
                        access_token="",
                        level=alert.level,
                    ),
                )
                if sent:
                    delivered_to.append(str(chat_id))

            # Duty staff: full clinical context, red alerts only.
            if alert.level == "red":
                staff_text = format_doctor_alert(
                    patient_name=patient.full_name,
                    age=patient.age,
                    district=patient.district,
                    diagnosis=patient.diagnosis,
                    reason=alert.reason or "",
                    triggered_params=alert.triggered_params or {},
                    patient_id=str(patient.id),
                )
                if await _broadcast_to_staff(session, patient.id, staff_text):
                    delivered_to.append("staff")

            if not delivered_to:
                logger.warning(
                    "No reachable recipient for %s alert on patient %s.",
                    alert.level,
                    patient.id,
                )
                continue

            notif = Notification(
                patient_id=patient.id,
                alert_id=getattr(alert, "id", None),
                level=alert.level,
                urgent=(alert.level == "red"),
            )
            session.add(notif)
            await session.flush()
            session.add(
                NotificationAttempt(
                    notification_id=notif.id,
                    channel="telegram",
                    delivered=True,
                )
            )
            await session.commit()
            mark_sent(key, alert.ts.isoformat())
            logger.info(
                "Delivered %s alert for patient %s to %s.",
                alert.level,
                patient.id,
                delivered_to,
            )


async def check_no_data() -> None:
    """Job 3: tells caregivers when a watch has gone silent."""
    async with get_db_context() as session:
        stmt = (
            select(Alert, Patient)
            .join(Patient, Alert.patient_id == Patient.id)
            .where(
                Alert.level == "no_data",
                Patient.deceased_at.is_(None),
                ~exists().where(Notification.alert_id == Alert.id),
            )
            .order_by(Alert.ts.desc())
        )
        rows = (await session.execute(stmt)).all()

        for alert, patient in rows:
            key = f"no_data:{alert.id}"
            if already_sent(key):
                continue

            delivered = False
            for chat_id in await _relative_chat_ids(session, patient.id):
                if await send_telegram_message(
                    chat_id,
                    format_no_data_alert(
                        patient_name=patient.full_name,
                        access_token="",
                    ),
                ):
                    delivered = True

            if delivered:
                mark_sent(key, alert.ts.isoformat())
                logger.info(
                    "No-data notice delivered for patient %s (silent since %s).",
                    patient.id,
                    alert.ts.isoformat(),
                )


async def _run_job(name: str, job) -> None:
    """Runs a scheduled job, logging failures instead of killing the scheduler."""
    try:
        await job()
    except Exception:
        logger.exception("Notifier job %s failed", name)


async def main() -> None:
    logger.info("WMAX Notifier service starting...")
    logger.info("Config: COOLDOWN=%sh, NO_DATA=%smin", ALERT_COOLDOWN_HOURS, NO_DATA_MINUTES)

    admins = _admin_chat_ids()
    if admins:
        await send_telegram_message(
            chat_id=admins[0],
            text="<b>WMAX Notifier</b> servisi muvaffaqiyatli ishga tushdi.",
        )
    else:
        logger.warning("No Telegram admins registered — skipping startup ping.")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _run_job, "interval", minutes=5, args=["task_escalations", check_task_escalations]
    )
    scheduler.add_job(
        _run_job, "interval", minutes=1, args=["alert_signals", check_alert_signals]
    )
    scheduler.add_job(_run_job, "interval", minutes=15, args=["no_data", check_no_data])

    scheduler.start()
    logger.info("Scheduler started with 3 background monitoring jobs.")

    polling_task = asyncio.create_task(poll_telegram_messages())

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Notifier service stopping...")
    finally:
        polling_task.cancel()
        scheduler.shutdown()
        logger.info("Notifier service stopped.")


if __name__ == "__main__":
    asyncio.run(main())
