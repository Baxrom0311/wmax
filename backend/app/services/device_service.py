from __future__ import annotations

import uuid
import inspect
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from collections.abc import Sequence
from typing import Any, Literal

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.baseline import Baseline
from app.auth.device import create_device_token
from app.models.device import Device, DeviceCredential, DeviceEnrollmentCode
from app.models.device_assignment import DeviceAssignment
from app.models import PatientMembership
from app.models.patient import Patient


class DeviceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _serial(self, device: Device) -> str | None:
        return device.serial

    def _model(self, device: Device) -> str | None:
        return device.model

    async def list_devices(
        self,
        tenant_id: uuid.UUID | None = None,
        tenant_ids: Sequence[uuid.UUID] | None = None,
        status: str | None = None,
        tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lists devices filtered by tenant, status or hardware tier."""
        stmt = select(Device)
        filters = []
        if tenant_id:
            filters.append(Device.owner_tenant_id == tenant_id)
        elif tenant_ids is not None:
            filters.append(Device.owner_tenant_id.in_(list(tenant_ids)))
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
                "serial": self._serial(d),
                "serial_number": self._serial(d),
                "model": self._model(d),
                "model_name": self._model(d),
                "tier": d.tier,
                "status": d.status,
                "ownership": d.ownership,
                "battery_health_pct": d.battery_health_pct,
                "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                "last_sync_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
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
            serial=serial_number,
            model=model_name,
            tier=tier,
            ownership=ownership,
            owner_tenant_id=tenant_id,
            battery_health_pct=battery_health_pct,
            status="in_stock",
        )
        added = self.session.add(device)
        if inspect.isawaitable(added):
            await added
        await self.session.flush()
        return device

    async def create_enrollment(
        self,
        device_id: uuid.UUID,
        ttl_minutes: int = 10,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> dict[str, Any]:
        device_result = await self.session.execute(
            select(Device).where(Device.id == device_id).with_for_update()
        )
        device = device_result.scalar_one_or_none()
        if not device:
            raise ValueError("Qurilma topilmadi")
        self._assert_device_scope(device, tenant_ids)

        code = f"{secrets.randbelow(1_000_000):06d}"
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(DeviceEnrollmentCode)
            .where(
                DeviceEnrollmentCode.device_id == device.id,
                DeviceEnrollmentCode.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )

        enrollment = DeviceEnrollmentCode(
            device_id=device.id,
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            expires_at=now + timedelta(minutes=ttl_minutes),
        )
        added = self.session.add(enrollment)
        if inspect.isawaitable(added):
            await added
        await self.session.flush()

        return {
            "device_id": str(device.id),
            "enrollment_id": str(enrollment.id),
            "code": code,
            "expires_at": enrollment.expires_at.isoformat(),
        }

    async def claim_enrollment(
        self,
        device_id: uuid.UUID,
        code: str,
    ) -> dict[str, str] | None:
        now = datetime.now(timezone.utc)
        device_result = await self.session.execute(
            select(Device).where(Device.id == device_id).with_for_update()
        )
        if device_result.scalar_one_or_none() is None:
            return None
        enrollment_result = await self.session.execute(
            select(DeviceEnrollmentCode)
            .where(
                DeviceEnrollmentCode.device_id == device_id,
                DeviceEnrollmentCode.consumed_at.is_(None),
                DeviceEnrollmentCode.expires_at > now,
                DeviceEnrollmentCode.attempts < 5,
            )
            .order_by(DeviceEnrollmentCode.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        enrollment = enrollment_result.scalar_one_or_none()
        if enrollment is None:
            return None

        enrollment.attempts += 1
        supplied_hash = hashlib.sha256(code.strip().encode()).hexdigest()
        if not secrets.compare_digest(enrollment.code_hash, supplied_hash):
            await self.session.flush()
            return None

        enrollment.consumed_at = now
        await self.session.execute(
            update(DeviceCredential)
            .where(
                DeviceCredential.device_id == device_id,
                DeviceCredential.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        raw_secret = secrets.token_urlsafe(32)
        credential = DeviceCredential(
            device_id=device_id,
            secret_hash=hashlib.sha256(raw_secret.encode()).hexdigest(),
        )
        self.session.add(credential)
        await self.session.flush()
        return {
            "device_id": str(device_id),
            "device_token": create_device_token(
                device_id,
                credential.id,
                credential_secret=raw_secret,
            ),
        }

    async def assign_device_to_patient(
        self,
        device_id: uuid.UUID,
        patient_id: uuid.UUID,
        assigned_by: uuid.UUID | None = None,
        deposit_uzs: int = 500_000,
        rental_uzs_month: int = 180_000,
        due_back_at: datetime | None = None,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> dict[str, Any]:
        """Assigns an in_stock device to a patient.
        
        Per Section 5.2 of BUSINESS_MODEL.md:
        If patient changes device, existing baseline is invalidated and patient
        phase resets to 'calib' so new sensor characteristics don't cause false alerts.
        """
        device = (
            await self.session.execute(
                select(Device).where(Device.id == device_id).with_for_update()
            )
        ).scalar_one_or_none()
        if not device:
            raise ValueError("Qurilma topilmadi")
        self._assert_device_scope(device, tenant_ids)
        if device.status not in ("in_stock", "returning"):
            raise ValueError(f"Qurilma hozir bo'sh emas (holati: {device.status})")

        patient = (
            await self.session.execute(
                select(Patient).where(Patient.id == patient_id).with_for_update()
            )
        ).scalar_one_or_none()
        if not patient:
            raise ValueError("Bemor topilmadi")
        if patient.deceased_at is not None:
            raise ValueError("Vafot etgan bemorga qurilma biriktirib bo'lmaydi")
        if device.owner_tenant_id is not None:
            await self._assert_patient_in_tenant(patient.id, device.owner_tenant_id)
            if tenant_ids is not None and device.owner_tenant_id not in set(tenant_ids):
                raise ValueError("Qurilma klinikangizga tegishli emas")
        elif tenant_ids is not None:
            await self._assert_patient_in_any_tenant(patient.id, tenant_ids)

        # Baseline reset check if changing hardware
        serial = self._serial(device)
        if patient.device_id and patient.device_id != serial:
            # Device changed: invalidate previous baseline and switch phase to 'calib'
            patient.phase = "calib"
            patient.phase_since = datetime.now(timezone.utc)
            patient.baseline_approved_by = None
            patient.baseline_approved_at = None

        patient.device_id = serial

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
        added = self.session.add(assignment)
        if inspect.isawaitable(added):
            await added

        device.status = "assigned"
        await self.session.flush()

        return {
            "assignment_id": str(assignment.id),
            "device_id": str(device.id),
            "patient_id": str(patient.id),
            "serial_number": serial,
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
        refund_deposit: bool = False,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> dict[str, Any]:
        """Processes return of a rented device, inspection, and deposit refund."""
        if refund_deposit:
            raise ValueError("Depozit qaytarish provayderi ulanmagan; qaytarish alohida bajarilishi kerak")
        device = (
            await self.session.execute(
                select(Device).where(Device.id == device_id).with_for_update()
            )
        ).scalar_one_or_none()
        if not device:
            raise ValueError("Qurilma topilmadi")
        self._assert_device_scope(device, tenant_ids)
        if device.status != "assigned":
            raise ValueError("Faqat biriktirilgan qurilmani qaytarish mumkin")

        # Find active assignment
        stmt = (
            select(DeviceAssignment)
            .where(
                and_(
                    DeviceAssignment.device_id == device_id,
                    DeviceAssignment.released_at.is_(None),
                )
            )
            .order_by(DeviceAssignment.assigned_at.desc())
            .limit(1)
            .with_for_update()
        )
        res = await self.session.execute(stmt)
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise ValueError("Faol qurilma biriktirishi topilmadi")

        now = datetime.now(timezone.utc)
        if assignment:
            assignment.released_at = now
            assignment.return_notes = return_notes
            # The application has no payment processor/refund adapter. Do not
            # record a refund as completed based on a request flag.
            assignment.deposit_refunded = False

        if battery_health_pct is not None:
            device.battery_health_pct = battery_health_pct

        # If battery degraded < 80%, retire the device
        if device.battery_health_pct is not None and device.battery_health_pct < 80:
            device.status = "retired"
        else:
            device.status = "in_stock"

        await self.session.flush()

        return {
            "device_id": str(device.id),
            "serial_number": self._serial(device),
            "status": device.status,
            "battery_health_pct": device.battery_health_pct,
            "returned_at": now.isoformat(),
            "deposit_refunded": False,
        }

    async def revoke_credential(
        self,
        device_id: uuid.UUID,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> dict[str, Any]:
        device = await self.session.get(Device, device_id)
        if not device:
            raise ValueError("Qurilma topilmadi")
        self._assert_device_scope(device, tenant_ids)
        stmt = select(DeviceCredential).where(
            DeviceCredential.device_id == device_id,
            DeviceCredential.revoked_at.is_(None),
        )
        res = await self.session.execute(stmt)
        credential = res.scalar_one_or_none()
        if not credential:
            raise ValueError("Qurilma credential topilmadi")
        credential.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        return {"device_id": str(device_id), "revoked_at": credential.revoked_at.isoformat()}

    async def get_health(
        self,
        device_id: uuid.UUID,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> dict[str, Any]:
        device = await self.session.get(Device, device_id)
        if not device:
            raise ValueError("Qurilma topilmadi")
        self._assert_device_scope(device, tenant_ids)
        return {
            "device_id": str(device.id),
            "status": device.status,
            "battery_health_pct": device.battery_health_pct,
            "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
            "bound_phone_node_id": device.bound_phone_node_id,
        }

    def _assert_device_scope(
        self,
        device: Device,
        tenant_ids: Sequence[uuid.UUID] | None,
    ) -> None:
        if tenant_ids is None:
            return
        if device.owner_tenant_id not in set(tenant_ids):
            raise ValueError("Bu qurilma klinikangizga tegishli emas")

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

    async def _assert_patient_in_any_tenant(
        self,
        patient_id: uuid.UUID,
        tenant_ids: Sequence[uuid.UUID],
    ) -> None:
        if not tenant_ids:
            raise ValueError("Bemor uchun klinik scope topilmadi")
        membership = (
            await self.session.execute(
                select(PatientMembership.id).where(
                    PatientMembership.patient_id == patient_id,
                    PatientMembership.tenant_id.in_(list(tenant_ids)),
                    PatientMembership.revoked_at.is_(None),
                ).limit(1)
            )
        ).scalar_one_or_none()
        if membership is None:
            raise ValueError("Bemor qurilma klinikangizga biriktirilmagan")
