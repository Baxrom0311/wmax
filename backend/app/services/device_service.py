from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.baseline import Baseline
from app.models.device import Device
from app.models.device_assignment import DeviceAssignment
from app.models.patient import Patient


class DeviceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_devices(
        self,
        tenant_id: uuid.UUID | None = None,
        status: str | None = None,
        tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lists devices filtered by tenant, status or hardware tier."""
        stmt = select(Device)
        filters = []
        if tenant_id:
            filters.append(Device.tenant_id == tenant_id)
        if status:
            filters.append(Device.status == status)
        if tier:
            filters.append(Device.tier == tier)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Device.created_at.desc())
        res = await self.session.execute(stmt)
        devices = res.scalars().all()

        return [
            {
                "id": str(d.id),
                "serial_number": d.serial_number,
                "model_name": d.model_name,
                "tier": d.tier,
                "status": d.status,
                "ownership": d.ownership,
                "battery_health_pct": d.battery_health_pct,
                "last_sync_at": d.last_sync_at.isoformat() if d.last_sync_at else None,
                "created_at": d.created_at.isoformat(),
            }
            for d in devices
        ]

    async def register_device(
        self,
        serial_number: str,
        model_name: str,
        tier: Literal["tier1_wearos", "tier2_wearos_budget", "tier3_ble_band"] = "tier1_wearos",
        tenant_id: uuid.UUID | None = None,
        ownership: str = "owned",
        battery_health_pct: int = 100,
    ) -> Device:
        """Registers a new device into the inventory."""
        device = Device(
            serial_number=serial_number,
            model_name=model_name,
            tier=tier,
            tenant_id=tenant_id,
            ownership=ownership,
            battery_health_pct=battery_health_pct,
            status="in_stock",
        )
        self.session.add(device)
        await self.session.flush()
        return device

    async def assign_device_to_patient(
        self,
        device_id: uuid.UUID,
        patient_id: uuid.UUID,
        assigned_by: uuid.UUID | None = None,
        deposit_uzs: int = 500_000,
        rental_uzs_month: int = 180_000,
        due_back_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Assigns an in_stock device to a patient.
        
        Per Section 5.2 of BUSINESS_MODEL.md:
        If patient changes device, existing baseline is invalidated and patient
        phase resets to 'calib' so new sensor characteristics don't cause false alerts.
        """
        device = await self.session.get(Device, device_id)
        if not device:
            raise ValueError("Qurilma topilmadi")
        if device.status not in ("in_stock", "returning"):
            raise ValueError(f"Qurilma hozir bo'sh emas (holati: {device.status})")

        patient = await self.session.get(Patient, patient_id)
        if not patient:
            raise ValueError("Bemor topilmadi")

        # Baseline reset check if changing hardware
        if patient.device_id and patient.device_id != device.serial_number:
            # Device changed: invalidate previous baseline and switch phase to 'calib'
            patient.phase = "calib"
            patient.phase_since = datetime.now(timezone.utc)
            patient.baseline_approved_by = None
            patient.baseline_approved_at = None

        patient.device_id = device.serial_number

        now = datetime.now(timezone.utc)
        assignment = DeviceAssignment(
            device_id=device.id,
            patient_id=patient.id,
            assigned_by=assigned_by,
            assigned_at=now,
            deposit_uzs=deposit_uzs,
            rental_uzs_month=rental_uzs_month,
            due_back_at=due_back_at,
        )
        self.session.add(assignment)

        device.status = "assigned"
        await self.session.flush()

        return {
            "assignment_id": str(assignment.id),
            "device_id": str(device.id),
            "patient_id": str(patient.id),
            "serial_number": device.serial_number,
            "status": device.status,
            "assigned_at": assignment.assigned_at.isoformat(),
            "deposit_uzs": assignment.deposit_uzs,
            "rental_uzs_month": assignment.rental_uzs_month,
        }

    async def return_device(
        self,
        device_id: uuid.UUID,
        battery_health_pct: int | None = None,
        return_notes: str | None = None,
        refund_deposit: bool = True,
    ) -> dict[str, Any]:
        """Processes return of a rented device, inspection, and deposit refund."""
        device = await self.session.get(Device, device_id)
        if not device:
            raise ValueError("Qurilma topilmadi")

        # Find active assignment
        stmt = (
            select(DeviceAssignment)
            .where(
                and_(
                    DeviceAssignment.device_id == device_id,
                    DeviceAssignment.returned_at.is_(None),
                )
            )
            .order_by(DeviceAssignment.assigned_at.desc())
        )
        res = await self.session.execute(stmt)
        assignment = res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if assignment:
            assignment.returned_at = now
            assignment.return_notes = return_notes
            assignment.deposit_refunded = refund_deposit

        if battery_health_pct is not None:
            device.battery_health_pct = battery_health_pct

        # If battery degraded < 80%, retire the device
        if device.battery_health_pct and device.battery_health_pct < 80:
            device.status = "retired"
        else:
            device.status = "in_stock"

        await self.session.flush()

        return {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "status": device.status,
            "battery_health_pct": device.battery_health_pct,
            "returned_at": now.isoformat(),
            "deposit_refunded": refund_deposit,
        }
