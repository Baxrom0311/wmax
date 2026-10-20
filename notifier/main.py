"""WMAX notifier: turns clinical state changes into Telegram messages.

Division of labour with the API's background workers:
  * `app.workers.escalation_worker` owns the **state machine** — it stamps
    `reminded_at`, `escalated_at`, flips tasks to `overdue`, and writes
    `no_data` alerts.
  * the API queues one durable `notifications` row per required recipient
    when it persists a red/amber/no_data alert or an SOS;
  * this service owns **delivery** — it sends those rows (Telegram → SMS),
    records every attempt, and messages duty staff about task reminders.

Keeping writes in one place avoids two processes racing on the same rows.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select

from app.core.db import get_db_context
from app.models.patient import Patient
from app.models.task import Task
from app.models.user import User
from app.models.schema import Account, AccountIdentity
from app.services.monitoring_policy import clinical_consent
from app.services.notification_service import deliver_due, staff_recipients

from .admin_store import get_all_admins
from .state import already_sent, mark_sent
from .telegram import (
    format_active_call_reminder,
    format_overdue_escalation,
    poll_telegram_messages,
    send_telegram_message,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("wmax.notifier")
# httpx logs full request URLs at INFO, and Telegram URLs embed the bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)


def _admin_chat_ids() -> list[int]:
    """Telegram chat ids of registered duty staff (super admin included)."""
    return [int(admin["id"]) for admin in get_all_admins() if admin.get("id")]


async def _staff_chat_ids(session, patient_id) -> list[str]:
    """Verified Telegram chats of staff currently responsible for this patient
    (consented care clinic and territory scope, IDEOLOGY B6)."""
    staff = await staff_recipients(session, patient_id)
    if not staff:
        return []
    stmt = (
        select(AccountIdentity.external_id)
        .where(
            AccountIdentity.account_id.in_([account.id for account in staff]),
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
                Task.kind == "clinical",
                Task.status.in_(("open", "acknowledged", "overdue")),
                clinical_consent(Task.patient_id, Task.tenant_id),
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


async def _telegram_sender(chat_id: str, text: str, reply_markup: dict | None) -> bool:
    return await send_telegram_message(chat_id, text, reply_markup)


async def deliver_notifications() -> None:
    """Job 2: durable per-recipient delivery of red/amber/no_data alerts and SOS.

    Rows are queued by the API in the same transaction as the alert or SOS;
    this job sends, retries and escalates them (Telegram → SMS) and records
    every attempt. See app.services.notification_service.
    """
    async with get_db_context() as session:
        processed = await deliver_due(session, telegram_sender=_telegram_sender)
        if processed:
            logger.info("Processed %s notification deliveries.", processed)


async def _run_job(name: str, job) -> None:
    """Runs a scheduled job, logging failures instead of killing the scheduler."""
    try:
        await job()
    except Exception:
        logger.exception("Notifier job %s failed", name)


async def main() -> None:
    logger.info("WMAX Notifier service starting...")

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
        _run_job, "interval", seconds=20, args=["deliver_notifications", deliver_notifications],
        max_instances=1, coalesce=True,
    )

    scheduler.start()
    logger.info("Scheduler started with 2 background delivery jobs.")

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
