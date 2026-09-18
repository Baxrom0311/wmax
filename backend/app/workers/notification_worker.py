from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_context
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.user import User

logger = logging.getLogger("nazorat.workers.notification")

NOTIFICATION_COOLDOWN_HOURS = 6


async def process_alert_notifications(session: AsyncSession) -> None:
    """Dispatches notifications for acute alerts with 6-hour cooldown per patient."""
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(minutes=10)

    # Find alerts in the last 10 minutes that are amber or red
    stmt_alerts = (
        select(Alert)
        .where(
            Alert.ts >= recent_cutoff,
            Alert.level.in_(["amber", "red"]),
        )
        .order_by(Alert.ts.desc())
    )
    res_alerts = await session.execute(stmt_alerts)
    recent_alerts = res_alerts.scalars().all()

    for alert in recent_alerts:
        # Check cooldown: has a notification been sent for this patient in the last 6 hours?
        cooldown_cutoff = now - timedelta(hours=NOTIFICATION_COOLDOWN_HOURS)
        stmt_notif = (
            select(Notification)
            .where(
                Notification.patient_id == alert.patient_id,
                Notification.sent_at >= cooldown_cutoff,
            )
            .limit(1)
        )
        res_notif = await session.execute(stmt_notif)
        last_sent = res_notif.scalar_one_or_none()

        if last_sent:
            logger.debug(
                "Skipping notification for patient %s due to 6h cooldown (last sent at %s)",
                alert.patient_id,
                last_sent.sent_at.isoformat(),
            )
            continue

        # Fetch patient doctor details
        stmt_p = select(Patient).where(Patient.id == alert.patient_id)
        res_p = await session.execute(stmt_p)
        patient = res_p.scalar_one_or_none()

        recipient = "admin"
        if patient and patient.doctor_id:
            stmt_doc = select(User).where(User.id == patient.doctor_id)
            res_doc = await session.execute(stmt_doc)
            doc = res_doc.scalar_one_or_none()
            if doc:
                recipient = doc.phone

        # Record notification
        notif = Notification(
            patient_id=alert.patient_id,
            channel="telegram",
            recipient=recipient,
            level=alert.level,
            sent_at=now,
        )
        session.add(notif)
        await session.commit()

        logger.info(
            "NOTIFICATION SENT: Dispatched [%s] alert for patient %s to %s (composite_score=%.2f)",
            alert.level,
            alert.patient_id,
            recipient,
            alert.composite_score,
        )


async def run_notification_worker(interval_seconds: int = 60) -> None:
    """Periodic worker routine for alert notifications."""
    logger.info("Notification worker started (interval=%ds).", interval_seconds)
    while True:
        try:
            async with get_db_context() as session:
                await process_alert_notifications(session)
        except asyncio.CancelledError:
            logger.info("Notification worker received cancellation. Shutting down gracefully.")
            break
        except Exception as e:
            logger.exception("Error in notification worker cycle: %s", e)

        await asyncio.sleep(interval_seconds)
