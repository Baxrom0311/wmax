from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.models import PatientAddress, PatientMembership
from app.models.patient import Patient
from app.models.sos import SosEvent
from app.repositories.sos_repo import SosRepository
from app.services.emergency.dispatcher import EmergencyDispatcher, ManualDispatch
from app.services.live_event_service import LiveEventService
from app.services.patient_context import PatientContextBuilder
from app.services.notification_service import queue_sos_notifications

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
        patient_record = await self.session.get(Patient, patient_id)
        if not patient_record or patient_record.deceased_at is not None:
            raise NotFoundException("Faol bemor profili topilmadi")
        # The snapshot helps responders but must never block the SOS itself:
        # it is built inside a savepoint and degrades to the stored address.
        context = None
        try:
            async with self.session.begin_nested():
                context = await self.context_builder.build(patient_id)
        except Exception:
            logger.exception("SOS snapshot enrichment failed for patient %s; using minimal snapshot", patient_id)

        # Snapshot address
        if context is not None and context.primary_address:
            address_snap = context.primary_address.model_dump(mode="json")
        else:
            address = (await self.session.execute(
                select(PatientAddress).where(
                    PatientAddress.patient_id == patient_id, PatientAddress.is_primary.is_(True),
                )
            )).scalar_one_or_none()
            address_snap = {
                "region": address.region if address else None,
                "district": address.district if address else patient_record.district,
                "mahalla": address.mahalla if address else None,
                "street": address.street if address else None,
                "house": address.house if address else None,
                "landmark": address.landmark if address else "Boshlang'ich manzil kiritilmagan",
            }

        # Snapshot clinical profile
        clinical_snap = {} if context is None else {
            "blood_group": context.blood_group,
            "rh": context.rh,
            "allergies": [a.model_dump(mode="json") for a in context.allergies],
            "active_medications": [
                m.model_dump(mode="json") for m in context.medications if m.stopped_at is None
            ],
            "conditions": [c.model_dump(mode="json") for c in context.conditions if c.is_active],
        }

        # Create persistent event
        event = await self.sos_repo.create_event(
            patient_id=patient_id,
            source=source,
            address_snapshot=address_snap,
            clinical_snapshot=clinical_snap,
            vitals_snapshot=(context.recent_vitals or None) if context is not None else None,
            device_lat=device_lat,
            device_lon=device_lon,
            device_accuracy_m=device_accuracy_m,
        )

        # Trigger emergency dispatcher
        try:
            if context is None:
                raise RuntimeError("no dispatcher context")
            dispatch_result = await self.dispatcher.dispatch(event, context)
            if not dispatch_result.accepted:
                event.dispatch_method = "unavailable"
                event.dispatch_ref = "not_dispatched"
        except Exception as e:
            logger.error(f"Emergency dispatch execution failed: {e}", exc_info=True)
            event.dispatch_method = "unavailable"
            event.dispatch_ref = "dispatch_error"

        # Durable per-recipient delivery in the same transaction as the SOS
        # itself; the notifier worker sends, retries and escalates (I2).
        await queue_sos_notifications(self.session, event, patient_record)

        logger.warning("SOS raised for patient %s, event=%s, source=%s", patient_id, event.id, source)
        await LiveEventService(self.session).publish_sos(event, action="raised")
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
        await LiveEventService(self.session).publish_sos(event, action="cancelled")
        return event

    async def acknowledge_sos(
        self,
        sos_id: uuid.UUID,
        user_id: uuid.UUID,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> SosEvent:
        event = await self.sos_repo.get_by_id(sos_id)
        if not event:
            raise NotFoundException("SOS hodisasi topilmadi")
        await self._assert_event_scope(event, tenant_ids)

        event.status = "acknowledged"
        event.acknowledged_at = datetime.now(timezone.utc)
        event.acknowledged_by = user_id
        await self.session.flush()
        await LiveEventService(self.session).publish_sos(event, action="acknowledged")
        return event

    async def dispatch_sos(
        self,
        sos_id: uuid.UUID,
        dispatch_method: str = "manual_call_103",
        dispatch_ref: str | None = None,
        user_id: uuid.UUID | None = None,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> SosEvent:
        event = await self.sos_repo.get_by_id(sos_id)
        if not event:
            raise NotFoundException("SOS hodisasi topilmadi")
        await self._assert_event_scope(event, tenant_ids)

        event.status = "dispatched"
        event.dispatched_at = datetime.now(timezone.utc)
        event.dispatch_method = dispatch_method
        event.dispatch_ref = dispatch_ref
        if user_id:
            event.acknowledged_by = event.acknowledged_by or user_id
        await self.session.flush()
        await LiveEventService(self.session).publish_sos(event, action="dispatched")
        return event

    async def resolve_sos(
        self,
        sos_id: uuid.UUID,
        resolution_note: str,
        user_id: uuid.UUID,
        status: str = "resolved",
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> SosEvent:
        event = await self.sos_repo.get_by_id(sos_id)
        if not event:
            raise NotFoundException("SOS hodisasi topilmadi")
        await self._assert_event_scope(event, tenant_ids)

        event.status = status  # type: ignore[assignment]
        event.resolved_at = datetime.now(timezone.utc)
        event.resolved_by = user_id
        event.resolution_note = resolution_note
        await self.session.flush()
        await LiveEventService(self.session).publish_sos(event, action=status)
        return event

    async def get_active_sos(self, tenant_ids: Sequence[uuid.UUID] | None = None) -> list[dict[str, Any]]:
        events = await self.sos_repo.list_active(tenant_ids=tenant_ids)
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

    async def _assert_event_scope(
        self,
        event: SosEvent,
        tenant_ids: Sequence[uuid.UUID] | None,
    ) -> None:
        if tenant_ids is None:
            return
        if not tenant_ids:
            raise ForbiddenException("Bu SOS hodisasi bo'yicha amal bajarish huquqi yo'q")
        membership_id = (
            await self.session.execute(
                select(PatientMembership.id).where(
                    PatientMembership.patient_id == event.patient_id,
                    PatientMembership.tenant_id.in_(list(tenant_ids)),
                    PatientMembership.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if membership_id is None:
            raise ForbiddenException("Bu SOS hodisasi bo'yicha amal bajarish huquqi yo'q")
