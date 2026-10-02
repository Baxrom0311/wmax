from __future__ import annotations

import uuid
import inspect
from datetime import datetime, timedelta, timezone
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.attribution import orphan_candidates
from app.domain.types import AssignmentWindow
from app.models import Device, PatientMembership
from app.models.device_assignment import DeviceAssignment
from app.models.patient import Patient
from app.models.reading import OrphanReading, Reading


class OrphanReadingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_unresolved(
        self,
        device_id: uuid.UUID | None = None,
        limit: int = 100,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(OrphanReading).join(Device, Device.id == OrphanReading.device_id).where(OrphanReading.resolved_at.is_(None))
        if device_id is not None:
            stmt = stmt.where(OrphanReading.device_id == device_id)
        if tenant_ids is not None:
            stmt = stmt.where(Device.owner_tenant_id.in_(list(tenant_ids)))
        stmt = stmt.order_by(OrphanReading.window_start.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return [self._orphan_dict(item) for item in res.scalars().all()]

    async def candidates(
        self,
        orphan_id: int,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> list[dict[str, Any]]:
        orphan = await self.session.get(OrphanReading, orphan_id)
        if not orphan:
            return []
        await self._assert_orphan_scope(orphan, tenant_ids)
        start = orphan.window_start - timedelta(hours=12)
        end = orphan.window_start + timedelta(hours=12)
        stmt = select(DeviceAssignment).where(
            DeviceAssignment.device_id == orphan.device_id,
            DeviceAssignment.assigned_at < end,
            ((DeviceAssignment.released_at.is_(None)) | (DeviceAssignment.released_at > start)),
        )
        res = await self.session.execute(stmt)
        windows = tuple(
            AssignmentWindow(
                device_id=str(item.device_id),
                patient_id=item.patient_id,
                assigned_at=item.assigned_at,
                released_at=item.released_at,
            )
            for item in res.scalars().all()
        )
        patient_ids = orphan_candidates(str(orphan.device_id), (start, end), windows)
        if not patient_ids:
            return []
        patients = await self.session.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        by_id = {patient.id: patient for patient in patients.scalars().all()}
        return [
            {
                "patient_id": str(patient_id),
                "full_name": by_id[patient_id].full_name if patient_id in by_id else None,
            }
            for patient_id in patient_ids
        ]

    async def resolve(
        self,
        orphan_id: int,
        patient_id: uuid.UUID,
        resolved_by: uuid.UUID,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> dict[str, Any] | None:
        orphan = await self.session.get(OrphanReading, orphan_id)
        if not orphan or orphan.resolved_at is not None:
            return None
        device = await self._assert_orphan_scope(orphan, tenant_ids)
        owner_tenant_id = getattr(device, "owner_tenant_id", None)
        if owner_tenant_id is not None:
            await self._assert_patient_in_tenant(patient_id, owner_tenant_id)
        payload = orphan.payload or {}
        reading = Reading(
            patient_id=patient_id,
            device_id=orphan.device_id,
            window_start=orphan.window_start,
            window_end=self._parse_dt(payload.get("window_end")) or orphan.window_start + timedelta(minutes=5),
            hr_mean=payload.get("hr_mean"),
            hr_min=payload.get("hr_min"),
            hr_max=payload.get("hr_max"),
            rmssd=payload.get("rmssd"),
            sdnn=payload.get("sdnn"),
            spo2=payload.get("spo2"),
            skin_temp=payload.get("skin_temp"),
            steps=payload.get("steps"),
            rr_est=payload.get("rr_est"),
            sleep_frag=payload.get("sleep_frag"),
            worn=payload.get("worn", True),
            worn_pct=payload.get("worn_pct"),
            samples_n=payload.get("samples_n", 0),
            battery=payload.get("battery"),
            attributed_by="nurse",
        )
        added = self.session.add(reading)
        if inspect.isawaitable(added):
            await added
        orphan.resolved_at = datetime.now(timezone.utc)
        orphan.resolved_by = resolved_by
        orphan.resolved_to_patient_id = patient_id
        await self.session.flush()
        return self._orphan_dict(orphan)

    async def discard(
        self,
        orphan_id: int,
        resolved_by: uuid.UUID,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> dict[str, Any] | None:
        orphan = await self.session.get(OrphanReading, orphan_id)
        if not orphan or orphan.resolved_at is not None:
            return None
        await self._assert_orphan_scope(orphan, tenant_ids)
        orphan.resolved_at = datetime.now(timezone.utc)
        orphan.resolved_by = resolved_by
        await self.session.flush()
        return self._orphan_dict(orphan)

    def _orphan_dict(self, orphan: OrphanReading) -> dict[str, Any]:
        return {
            "id": orphan.id,
            "device_id": str(orphan.device_id),
            "window_start": orphan.window_start.isoformat(),
            "payload": orphan.payload,
            "received_at": orphan.received_at.isoformat() if orphan.received_at else None,
            "resolved_at": orphan.resolved_at.isoformat() if orphan.resolved_at else None,
            "resolved_to_patient_id": str(orphan.resolved_to_patient_id) if orphan.resolved_to_patient_id else None,
        }

    def _parse_dt(self, value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    async def _assert_orphan_scope(
        self,
        orphan: OrphanReading,
        tenant_ids: Sequence[uuid.UUID] | None,
    ) -> Device:
        device = await self.session.get(Device, orphan.device_id)
        if not device:
            raise ValueError("Qurilma topilmadi")
        if tenant_ids is not None and getattr(device, "owner_tenant_id", None) not in set(tenant_ids):
            raise ValueError("Bu yetim o'lchov klinikangizga tegishli emas")
        return device

    async def _assert_patient_in_tenant(
        self,
        patient_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        membership = (
            await self.session.execute(
                select(PatientMembership).where(
                    PatientMembership.patient_id == patient_id,
                    PatientMembership.tenant_id == tenant_id,
                    PatientMembership.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if not membership:
            raise ValueError("Bemor bu qurilma klinikasiga biriktirilmagan")
