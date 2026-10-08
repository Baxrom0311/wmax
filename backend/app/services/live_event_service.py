from __future__ import annotations

import inspect
from typing import Any

from sqlalchemy import select

from app.core.realtime import realtime_hub
from app.models import PatientMembership, RealtimeEventOutbox


class LiveEventService:
    def __init__(self, session: Any | None = None) -> None:
        self.session = session

    async def publish_patient_readings(
        self, patient_id: Any, windows: list[str]
    ) -> int:
        tenant_ids = await self._patient_tenant_ids(patient_id)
        return await self.publish(
            "reading.accepted",
            {
                "patient_id": str(patient_id),
                "tenant_ids": [str(item) for item in tenant_ids],
                "windows": windows,
            },
        )

    async def publish_alert(self, alert: Any) -> int:
        tenant_ids = await self._patient_tenant_ids(alert.patient_id)
        return await self.publish(
            "alert.created",
            {
                "id": getattr(alert, "id", None),
                "patient_id": str(alert.patient_id),
                "tenant_ids": [str(item) for item in tenant_ids],
                "ts": alert.ts.isoformat() if getattr(alert, "ts", None) else None,
                "level": alert.level,
                "composite_score": alert.composite_score,
                "reason": alert.reason,
            },
        )

    async def publish_task(self, task: Any, *, action: str) -> int:
        return await self.publish(
            f"task.{action}",
            {
                "id": task.id,
                "patient_id": str(task.patient_id),
                "tenant_id": str(task.tenant_id) if getattr(task, "tenant_id", None) else None,
                "status": task.status,
                "kind": getattr(task, "kind", getattr(task, "type", None)),
                "assignee_account_id": (
                    str(task.assignee_account_id)
                    if getattr(task, "assignee_account_id", None)
                    else None
                ),
                "due_at": task.due_at.isoformat() if getattr(task, "due_at", None) else None,
            },
        )

    async def publish_sos(self, event: Any, *, action: str) -> int:
        tenant_ids = await self._patient_tenant_ids(event.patient_id)
        return await self.publish(
            f"sos.{action}",
            {
                "id": str(event.id),
                "patient_id": str(event.patient_id),
                "tenant_ids": [str(item) for item in tenant_ids],
                "status": getattr(event, "status", action),
                "source": getattr(event, "source", None),
                "raised_at": self._iso(getattr(event, "raised_at", None)),
                "acknowledged_at": self._iso(getattr(event, "acknowledged_at", None)),
                "dispatched_at": self._iso(getattr(event, "dispatched_at", None)),
                "resolved_at": self._iso(getattr(event, "resolved_at", None)),
                "cancelled_at": self._iso(getattr(event, "cancelled_at", None)),
            },
        )

    async def publish(self, topic: str, payload: dict[str, Any]) -> int:
        event_id: int | None = None
        if self.session is not None:
            event = RealtimeEventOutbox(topic=topic, payload=payload)
            added = self.session.add(event)
            if inspect.isawaitable(added):
                await added
            await self.session.flush()
            event_id = event.id
            return event_id
        return await realtime_hub.publish(topic, payload, event_id=event_id)

    def _iso(self, value: Any) -> str | None:
        return value.isoformat() if value is not None and hasattr(value, "isoformat") else None

    async def _patient_tenant_ids(self, patient_id: Any) -> list[Any]:
        if self.session is None:
            return []
        result = await self.session.execute(
            select(PatientMembership.tenant_id).where(
                PatientMembership.patient_id == patient_id,
                PatientMembership.revoked_at.is_(None),
            )
        )
        scalars = result.scalars()
        if inspect.isawaitable(scalars):
            scalars = await scalars
        rows = scalars.all()
        if inspect.isawaitable(rows):
            rows = await rows
        return list(rows)
