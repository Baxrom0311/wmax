from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.models.patient import Patient
from app.models.sos import SosEvent
from app.repositories.sos_repo import SosRepository
from app.services.emergency.dispatcher import EmergencyDispatcher, ManualDispatch
from app.services.patient_context import PatientContextBuilder

logger = logging.getLogger("wmax.sos.service")


class SosService:
    """Core domain service orchestrating SOS lifecycles, snapshots, and emergency dispatch."""

    def __init__(
        self,
        session: AsyncSession,
        dispatcher: EmergencyDispatcher | None = None,
    ) -> None:
        self.session = session
        self.sos_repo = SosRepository(session)
        self.context_builder = PatientContextBuilder(session)
        self.dispatcher = dispatcher or ManualDispatch()

    async def raise_sos(
        self,
        patient_id: uuid.UUID,
        source: str = "watch_button",
        device_lat: float | None = None,
        device_lon: float | None = None,
        device_accuracy_m: float | None = None,
    ) -> SosEvent:
        context = await self.context_builder.build(patient_id)
        if not context:
            raise NotFoundException("Bemor topilmadi")

        # Snapshot address
        if context.primary_address:
            address_snap = context.primary_address.model_dump()
        else:
            patient = await self.session.get(Patient, patient_id)
            district = patient.district if patient else "Noma'lum"
            address_snap = {
                "region": "Xorazm",
                "district": district,
                "landmark": "Boshlang'ich manzil kiritilmagan",
            }

        # Snapshot clinical profile
        clinical_snap = {
            "blood_group": context.blood_group,
            "rh": context.rh,
            "allergies": [a.model_dump() for a in context.allergies],
            "active_medications": [
                m.model_dump() for m in context.medications if m.stopped_at is None
            ],
            "conditions": [c.model_dump() for c in context.conditions if c.is_active],
        }

        # Create persistent event
        event = await self.sos_repo.create_event(
            patient_id=patient_id,
            source=source,
            address_snapshot=address_snap,
            clinical_snapshot=clinical_snap,
            vitals_snapshot=context.recent_vitals or None,
            device_lat=device_lat,
            device_lon=device_lon,
            device_accuracy_m=device_accuracy_m,
        )

        # Trigger emergency dispatcher
        try:
            await self.dispatcher.dispatch(event, context)
        except Exception as e:
            logger.error(f"Emergency dispatch execution failed: {e}", exc_info=True)

        # Queue notifications for emergency contacts
        for contact in context.emergency_contacts:
            recipient_ref = str(contact.telegram_chat_id or contact.phone)
            channel = "telegram" if contact.telegram_chat_id else "sms"
            await self.sos_repo.add_notification(
                sos_id=event.id,
                recipient_kind="relative",
                recipient_ref=recipient_ref,
                channel=channel,
                delivered=False,
            )

        logger.warning(
            f"🚨 SOS RAISED for Patient {context.full_name} ({patient_id}), "
            f"event={event.id}, source={source}"
        )
        return event

    async def cancel_sos(
        self,
        sos_id: uuid.UUID,
        patient_id: uuid.UUID,
        max_cancel_seconds: int = 60,
    ) -> SosEvent:
        event = await self.sos_repo.get_by_id(sos_id)
        if not event:
            raise NotFoundException("SOS hodisasi topilmadi")

        if event.patient_id != patient_id:
            raise ForbiddenException("Faqat o'z SOS signalini bekor qilish mumkin")

        if event.status != "raised":
            raise ValidationException("Faqat yangi ko'tarilgan SOS signalini bekor qilish mumkin")

        now = datetime.now(timezone.utc)
        elapsed = (now - event.raised_at).total_seconds()
        if elapsed > max_cancel_seconds:
            raise ValidationException("Bekor qilish muddati o'tib ketgan (maksimal 60 soniya)")

        event.status = "cancelled"
        event.cancelled_at = now
        await self.session.flush()
        logger.info(f"SOS {sos_id} was successfully cancelled by patient within {int(elapsed)}s")
        return event

    async def acknowledge_sos(
        self,
        sos_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> SosEvent:
        event = await self.sos_repo.get_by_id(sos_id)
        if not event:
            raise NotFoundException("SOS hodisasi topilmadi")

        event.status = "acknowledged"
        event.acknowledged_at = datetime.now(timezone.utc)
        event.acknowledged_by = user_id
        await self.session.flush()
        return event

    async def dispatch_sos(
        self,
        sos_id: uuid.UUID,
        dispatch_method: str = "manual_call_103",
        dispatch_ref: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> SosEvent:
        event = await self.sos_repo.get_by_id(sos_id)
        if not event:
            raise NotFoundException("SOS hodisasi topilmadi")

        event.status = "dispatched"
        event.dispatched_at = datetime.now(timezone.utc)
        event.dispatch_method = dispatch_method
        event.dispatch_ref = dispatch_ref
        if user_id:
            event.acknowledged_by = event.acknowledged_by or user_id
        await self.session.flush()
        return event

    async def resolve_sos(
        self,
        sos_id: uuid.UUID,
        resolution_note: str,
        user_id: uuid.UUID,
        status: str = "resolved",
    ) -> SosEvent:
        event = await self.sos_repo.get_by_id(sos_id)
        if not event:
            raise NotFoundException("SOS hodisasi topilmadi")

        event.status = status  # type: ignore[assignment]
        event.resolved_at = datetime.now(timezone.utc)
        event.resolved_by = user_id
        event.resolution_note = resolution_note
        await self.session.flush()
        return event

    async def get_active_sos(self) -> list[dict[str, Any]]:
        events = await self.sos_repo.list_active()
        results: list[dict[str, Any]] = []
        for ev in events:
            pat = await self.session.get(Patient, ev.patient_id)
            d = {
                "id": ev.id,
                "patient_id": ev.patient_id,
                "patient_name": pat.full_name if pat else "Noma'lum bemor",
                "source": ev.source,
                "status": ev.status,
                "raised_at": ev.raised_at,
                "address_snapshot": ev.address_snapshot,
                "clinical_snapshot": ev.clinical_snapshot,
                "vitals_snapshot": ev.vitals_snapshot,
                "device_lat": ev.device_lat,
                "device_lon": ev.device_lon,
                "device_accuracy_m": ev.device_accuracy_m,
                "acknowledged_at": ev.acknowledged_at,
                "acknowledged_by": ev.acknowledged_by,
                "dispatched_at": ev.dispatched_at,
                "dispatch_method": ev.dispatch_method,
                "dispatch_ref": ev.dispatch_ref,
                "resolved_at": ev.resolved_at,
                "resolved_by": ev.resolved_by,
                "resolution_note": ev.resolution_note,
                "cancelled_at": ev.cancelled_at,
                "created_at": ev.created_at,
            }
            results.append(d)
        return results

    async def get_patient_sos_history(self, patient_id: uuid.UUID) -> list[SosEvent]:
        return await self.sos_repo.list_by_patient(patient_id)
