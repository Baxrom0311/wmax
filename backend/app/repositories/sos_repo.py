from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.models.sos import SosEvent, SosNotification


class SosRepository:
    """Repository handling database operations for SOS events and notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, sos_id: uuid.UUID) -> SosEvent | None:
        return await self.session.get(SosEvent, sos_id)

    async def create_event(
        self,
        patient_id: uuid.UUID,
        source: str,
        address_snapshot: dict[str, Any],
        clinical_snapshot: dict[str, Any],
        vitals_snapshot: dict[str, Any] | None = None,
        device_lat: float | None = None,
        device_lon: float | None = None,
        device_accuracy_m: float | None = None,
    ) -> SosEvent:
        event = SosEvent(
            patient_id=patient_id,
            source=source,
            status="raised",
            address_snapshot=address_snapshot,
            clinical_snapshot=clinical_snapshot,
            vitals_snapshot=vitals_snapshot,
            device_lat=device_lat,
            device_lon=device_lon,
            device_accuracy_m=device_accuracy_m,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_active(self) -> list[SosEvent]:
        stmt = (
            select(SosEvent)
            .where(SosEvent.status.in_(("raised", "acknowledged", "dispatched")))
            .order_by(desc(SosEvent.raised_at))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_by_patient(self, patient_id: uuid.UUID, limit: int = 50) -> list[SosEvent]:
        stmt = (
            select(SosEvent)
            .where(SosEvent.patient_id == patient_id)
            .order_by(desc(SosEvent.raised_at))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def count_recent_events(self, patient_id: uuid.UUID, since: datetime) -> int:
        stmt = (
            select(func.count(SosEvent.id))
            .where(SosEvent.patient_id == patient_id)
            .where(SosEvent.raised_at >= since)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one() or 0

    async def add_notification(
        self,
        sos_id: uuid.UUID,
        recipient_kind: str,
        recipient_ref: str,
        channel: str,
        delivered: bool = False,
        error: str | None = None,
    ) -> SosNotification:
        notification = SosNotification(
            sos_id=sos_id,
            recipient_kind=recipient_kind,
            recipient_ref=recipient_ref,
            channel=channel,
            delivered=delivered,
            error=error,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification
