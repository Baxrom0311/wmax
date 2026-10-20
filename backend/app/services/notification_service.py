"""Durable, per-recipient delivery of red/amber alerts and SOS events.

Queueing happens in the same transaction that persists the alert or SOS, so a
crash can never lose the obligation to notify. Each required recipient gets
its own `notifications` row with its own retry state; one person's success
never closes another person's delivery (review finding 9).

Channel chain (IDEOLOGY I2), with the channels that exist today:
  Telegram → SMS (Eskiz). Urgent rows (red, SOS) that reached Telegram wait
  ACK_TIMEOUT for an acknowledgement and are then escalated to SMS once.
Every attempt is logged in `notification_attempts`. Delivery is at-least-once:
a crash after provider acceptance but before commit may duplicate a message;
it never silently drops one. Recipients are re-authorized before each attempt,
so consent revocation, removal from a clinic and death stop delivery (J2).
"""
from __future__ import annotations

import html
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import literal, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clinical_scope import clinician_patient_ids
from app.models import (
    Account,
    AccountIdentity,
    Alert,
    Notification,
    NotificationAttempt,
    Patient,
    PatientAccess,
    PatientMembership,
    SosEvent,
    Task,
    TenantMember,
)
from app.services.monitoring_policy import clinical_consent, family_consent
from app.services.sms import ESKIZ_DELIVERED, ESKIZ_FAILED, EskizSmsProvider

logger = logging.getLogger(__name__)

STAFF_NOTIFY_ROLES = ("doctor", "head_doctor", "nurse", "dispatcher")
ACK_TIMEOUT = timedelta(minutes=3)
SMS_STATUS_POLL = timedelta(seconds=60)
MAX_ATTEMPTS = 12
TELEGRAM_TRIES = 2
ACTIVE_SOS = ("raised", "acknowledged", "dispatched")
COOLDOWN = {"red": timedelta(minutes=15), "amber": timedelta(hours=6), "no_data": timedelta(hours=6)}
COOLDOWN_LEVELS = {"red": ("red",), "amber": ("amber", "red"), "no_data": ("no_data",)}

TelegramSender = Callable[[str, str, dict | None], Awaitable[bool]]


# ── recipients ───────────────────────────────────────────────────────────────

async def staff_recipients(session: AsyncSession, patient_id: Any) -> list[Account]:
    """Clinical staff responsible for this patient now: consented care clinic,
    active membership, and the patient inside their territory scope (B6)."""
    rows = await session.execute(
        select(Account)
        .join(TenantMember, TenantMember.account_id == Account.id)
        .join(PatientMembership, PatientMembership.tenant_id == TenantMember.tenant_id)
        .where(
            PatientMembership.patient_id == patient_id,
            PatientMembership.kind == "care",
            PatientMembership.revoked_at.is_(None),
            clinical_consent(patient_id, PatientMembership.tenant_id),
            TenantMember.left_at.is_(None),
            TenantMember.role.in_(STAFF_NOTIFY_ROLES),
            Account.is_active.is_(True),
            literal(patient_id, PGUUID(as_uuid=True)).in_(
                clinician_patient_ids(TenantMember.account_id, TenantMember.tenant_id)
            ),
        )
        .distinct()
    )
    return list(rows.scalars().all())


async def family_recipients(session: AsyncSession, patient_id: Any) -> list[Account]:
    rows = await session.execute(
        select(Account)
        .join(PatientAccess, PatientAccess.account_id == Account.id)
        .where(
            PatientAccess.patient_id == patient_id,
            family_consent(patient_id, Account.id),
            Account.is_active.is_(True),
        )
        .distinct()
    )
    return list(rows.scalars().all())


# ── messages (D1: report what was measured, no diagnosis, no false promises) ──

def _name(patient: Patient) -> str:
    return html.escape(patient.full_name or "Bemor")


def sos_message(patient: Patient, *, staff: bool) -> str:
    if staff:
        return (
            f"🚨 WMAX SOS: {_name(patient)} favqulodda yordam tugmasini bosdi. "
            "Dispetcher panelida tasdiqlang. 103 avtomatik chaqirilmaydi."
        )
    return (
        f"🚨 WMAX SOS: {_name(patient)} favqulodda yordam tugmasini bosdi. "
        "Bemor bilan darhol bog'laning; zarur bo'lsa 103 ga o'zingiz qo'ng'iroq qiling."
    )


def alert_message(patient: Patient, alert: Alert, *, staff: bool) -> str:
    if alert.level == "red":
        if staff:
            reason = html.escape(alert.reason or "")
            return (
                f"🔴 WMAX qizil signal: {_name(patient)}. Ko'rsatkichlar shaxsiy normadan "
                f"sezilarli farq qilmoqda ({reason}). Panelda bemor kartasini oching."
            )
        return (
            f"🔴 WMAX: {_name(patient)} ko'rsatkichlari shaxsiy normadan sezilarli farq qilmoqda. "
            "Bemor bilan bog'laning; ahvoli og'ir bo'lsa 103 ga qo'ng'iroq qiling."
        )
    if alert.level == "no_data":
        # J1: silence is a device/wear question, never a statement about health.
        return (
            f"⚪ WMAX: {_name(patient)} soatidan ma'lumot kelmayapti. "
            "Soat taqilganini, zaryadini va telefon ulanishini tekshiring."
        )
    return f"🟡 WMAX: {_name(patient)} ko'rsatkichlarida o'zgarish kuzatildi. Bemor bilan bog'lanib ahvolini so'rang."


def _plain(text: str) -> str:
    return html.unescape(text)


# ── queueing ─────────────────────────────────────────────────────────────────

async def _queue_rows(
    session: AsyncSession,
    *,
    patient: Patient,
    rows: list[tuple[Account, str]],
    level: str,
    urgent: bool,
    alert_id: int | None = None,
    sos_event_id: Any = None,
) -> int:
    key = "sos_event_id" if sos_event_id is not None else "alert_id"
    value = sos_event_id if sos_event_id is not None else alert_id
    column = getattr(Notification, key)
    for account, message in rows:
        await session.execute(
            insert(Notification)
            .values(
                patient_id=patient.id, recipient_account_id=account.id, message=message,
                level=level, urgent=urgent, **{key: value},
            )
            .on_conflict_do_nothing(
                index_elements=[key, "recipient_account_id"],
                index_where=column.is_not(None) & Notification.recipient_account_id.is_not(None),
            )
        )
    if not rows:
        # D3 cannot be met: keep a durable, operator-visible record instead of
        # pretending something was sent.
        logger.error("No authorized recipient for %s %s on patient %s", key, value, patient.id)
        session.add(Notification(
            patient_id=patient.id, level=level, urgent=urgent, delivery_status="no_recipient",
            message=None, **{key: value},
        ))
    await session.flush()
    return len(rows)


async def queue_sos_notifications(session: AsyncSession, event: SosEvent, patient: Patient) -> int:
    staff = await staff_recipients(session, patient.id)
    family = [a for a in await family_recipients(session, patient.id) if a.id not in {s.id for s in staff}]
    rows = [(a, sos_message(patient, staff=True)) for a in staff]
    rows += [(a, sos_message(patient, staff=False)) for a in family]
    return await _queue_rows(session, patient=patient, rows=rows, level="red", urgent=True, sos_event_id=event.id)


async def queue_alert_notifications(session: AsyncSession, alert: Alert, patient: Patient) -> int:
    """Red: responsible staff + family. Amber and no_data: family only (staff
    get a task instead). Never paywalled (D4)."""
    if alert.level not in COOLDOWN or patient.deceased_at is not None:
        return 0
    staff = await staff_recipients(session, patient.id) if alert.level == "red" else []
    staff_ids = {a.id for a in staff}
    family = [a for a in await family_recipients(session, patient.id) if a.id not in staff_ids]
    levels = COOLDOWN_LEVELS[alert.level]
    cutoff = datetime.now(timezone.utc) - COOLDOWN[alert.level]
    recent = set((await session.execute(
        select(Notification.recipient_account_id).where(
            Notification.patient_id == patient.id,
            Notification.level.in_(levels),
            Notification.created_at >= cutoff,
            Notification.alert_id.is_not(None),
        )
    )).scalars().all())
    rows = [(a, alert_message(patient, alert, staff=True)) for a in staff if a.id not in recent]
    rows += [(a, alert_message(patient, alert, staff=False)) for a in family if a.id not in recent]
    if not rows and (staff or family or alert.level != "red"):
        # Everyone was told within the cooldown, or a non-red signal has no
        # caregiver to inform (staff act on it through the routed task).
        return 0
    return await _queue_rows(
        session, patient=patient, rows=rows, level=alert.level, urgent=alert.level == "red", alert_id=alert.id,
    )


# ── delivery ─────────────────────────────────────────────────────────────────

async def _handled(session: AsyncSession, notification: Notification) -> bool:
    """Someone responsible already took over: the escalation chain can stop."""
    if notification.sos_event_id is not None:
        sos = await session.get(SosEvent, notification.sos_event_id)
        return sos is not None and sos.status != "raised"
    if notification.alert_id is not None:
        taken = await session.execute(
            select(Task.id).where(
                Task.alert_id == notification.alert_id,
                Task.status.in_(("acknowledged", "done")),
            ).limit(1)
        )
        return taken.scalar_one_or_none() is not None
    return False


async def _still_authorized(session: AsyncSession, notification: Notification) -> tuple[Account | None, bool]:
    patient_id = notification.patient_id
    for account in await staff_recipients(session, patient_id):
        if account.id == notification.recipient_account_id:
            return account, True
    for account in await family_recipients(session, patient_id):
        if account.id == notification.recipient_account_id:
            return account, False
    return None, False


def _provider_state(attempt: NotificationAttempt) -> str:
    return (attempt.error or "").removeprefix("provider_status:")


def _schedule_retry(notification: Notification, now: datetime) -> None:
    if notification.attempts >= MAX_ATTEMPTS:
        notification.delivery_status = "failed"
        logger.error("Notification %s failed after %s attempts", notification.id, notification.attempts)
        return
    notification.delivery_status = "pending"
    notification.next_attempt_at = now + timedelta(seconds=min(300, 30 * 2 ** max(0, notification.attempts - 1)))


async def deliver_notification(
    session: AsyncSession,
    notification: Notification,
    *,
    telegram_sender: TelegramSender,
    sms_provider: EskizSmsProvider | None = None,
    now: datetime | None = None,
) -> None:
    """Advance one notification by one step. The caller holds its row lock."""
    now = now or datetime.now(timezone.utc)
    patient = await session.get(Patient, notification.patient_id)
    if patient is None or patient.deceased_at is not None:
        notification.delivery_status = "cancelled"
        return
    if notification.acknowledged_at is not None:
        notification.delivery_status = "acknowledged"
        return
    if notification.sos_event_id is not None:
        sos = await session.get(SosEvent, notification.sos_event_id)
        if sos is None or sos.status in {"cancelled", "false_alarm"}:
            notification.delivery_status = "cancelled"
            return

    account, is_staff = await _still_authorized(session, notification)
    if account is None:
        notification.delivery_status = "cancelled"
        return

    attempts = list((await session.execute(
        select(NotificationAttempt)
        .where(NotificationAttempt.notification_id == notification.id)
        .order_by(NotificationAttempt.id.asc())
    )).scalars().all())
    telegram_ok = any(a.channel == "telegram" and a.delivered for a in attempts)
    telegram_failures = sum(1 for a in attempts if a.channel == "telegram" and not a.delivered)
    sms = [a for a in attempts if a.channel == "sms"]
    last_sms = sms[-1] if sms else None
    awaiting_dlr = bool(
        last_sms is not None and last_sms.provider_ref and not last_sms.delivered
        and _provider_state(last_sms) not in ESKIZ_FAILED
    )

    if notification.delivery_status == "awaiting_ack":
        if await _handled(session, notification) or last_sms is not None:
            notification.delivery_status = "delivered"
            return
        channel = "sms"  # I2: urgent and unacknowledged after Telegram
    elif awaiting_dlr:
        channel = "sms_status"
    else:
        chat = (await session.execute(
            select(AccountIdentity.external_id).where(
                AccountIdentity.account_id == account.id,
                AccountIdentity.provider == "telegram",
                AccountIdentity.verified_at.is_not(None),
            ).limit(1)
        )).scalar_one_or_none()
        channel = "telegram" if chat and not telegram_ok and telegram_failures < TELEGRAM_TRIES else "sms"

    attempt = NotificationAttempt(
        notification_id=notification.id,
        channel="telegram" if channel == "telegram" else "sms",
        attempted_at=now,
    )
    provider = sms_provider or EskizSmsProvider()
    try:
        if channel == "telegram":
            markup = None
            if notification.urgent:
                markup = {"inline_keyboard": [[{"text": "✅ Qabul qildim", "callback_data": f"ntf_ack:{notification.id}"}]]}
            attempt.delivered = bool(await telegram_sender(chat, notification.message or "", markup))
            attempt.error = None if attempt.delivered else "telegram_not_accepted"
        elif channel == "sms_status":
            attempt.provider_ref = last_sms.provider_ref
            state = await provider.delivery_status(last_sms.provider_ref)
            attempt.delivered = state == ESKIZ_DELIVERED
            attempt.error = None if attempt.delivered else f"provider_status:{state}"
        else:
            phone_trusted = is_staff or account.phone_verified_at is not None
            if not provider.configured() or not account.phone or not phone_trusted:
                attempt.delivered = False
                attempt.error = "sms_unavailable"
            else:
                attempt.provider_ref = await provider.submit(phone=account.phone, message=_plain(notification.message or ""))
                attempt.delivered = False
                attempt.error = "provider_accepted"
    except Exception as exc:  # provider/network errors are retried, never echoed
        attempt.delivered = False
        attempt.error = type(exc).__name__
    session.add(attempt)
    notification.attempts += 1

    if attempt.delivered:
        if channel == "telegram" and notification.urgent and not await _handled(session, notification):
            notification.delivery_status = "awaiting_ack"
            notification.next_attempt_at = now + ACK_TIMEOUT
        else:
            notification.delivery_status = "delivered"
        return
    if attempt.error == "provider_accepted" or (
        channel == "sms_status" and _provider_state(attempt) not in ESKIZ_FAILED
    ):
        notification.delivery_status = "pending"
        notification.next_attempt_at = now + SMS_STATUS_POLL
        if notification.attempts >= MAX_ATTEMPTS:
            notification.delivery_status = "delivered" if telegram_ok else "failed"
        return
    if telegram_ok and channel != "telegram":
        # SMS escalation failed but Telegram did reach the person.
        notification.delivery_status = "delivered"
        return
    _schedule_retry(notification, now)


async def deliver_due(
    session: AsyncSession,
    *,
    telegram_sender: TelegramSender,
    sms_provider: EskizSmsProvider | None = None,
    limit: int = 50,
) -> int:
    """Process due notifications one row lock and one commit at a time."""
    processed = 0
    for _ in range(limit):
        now = datetime.now(timezone.utc)
        notification = (await session.execute(
            select(Notification)
            .where(
                Notification.delivery_status.in_(("pending", "awaiting_ack")),
                Notification.next_attempt_at <= now,
            )
            .order_by(Notification.urgent.desc(), Notification.next_attempt_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )).scalar_one_or_none()
        if notification is None:
            break
        await deliver_notification(
            session, notification, telegram_sender=telegram_sender, sms_provider=sms_provider, now=now,
        )
        await session.commit()
        processed += 1
    return processed


async def acknowledge_by_telegram(session: AsyncSession, notification_id: int, chat_id: str) -> bool:
    """ACK from the inline button; only the addressed person can acknowledge."""
    notification = await session.get(Notification, notification_id)
    if notification is None or notification.recipient_account_id is None:
        return False
    owner = (await session.execute(
        select(AccountIdentity.id).where(
            AccountIdentity.account_id == notification.recipient_account_id,
            AccountIdentity.provider == "telegram",
            AccountIdentity.external_id == str(chat_id),
            AccountIdentity.verified_at.is_not(None),
        ).limit(1)
    )).scalar_one_or_none()
    if owner is None:
        return False
    if notification.acknowledged_at is None:
        notification.acknowledged_at = datetime.now(timezone.utc)
    notification.delivery_status = "acknowledged"
    return True


async def cancel_patient_notifications(session: AsyncSession, patient_id: Any) -> None:
    """J2/B5: stop every pending delivery for a patient from one place."""
    rows = (await session.execute(
        select(Notification).where(
            Notification.patient_id == patient_id,
            Notification.delivery_status.in_(("pending", "awaiting_ack")),
        )
    )).scalars().all()
    for notification in rows:
        notification.delivery_status = "cancelled"
