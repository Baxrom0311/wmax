from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.models.sos import SosEvent
from app.services.patient_context import PatientContext

# Python 3.11 f-string ifodasi ichida backslash qabul qilmaydi (PEP 701 faqat 3.12+).
UNKNOWN = "Noma'lum"


logger = logging.getLogger("wmax.emergency.dispatcher")


class DispatchResult(BaseModel):
    accepted: bool
    method: str
    reference: str | None = None
    message: str


class EmergencyDispatcher(ABC):
    """Abstract interface for emergency medical dispatch (Architecture V2 Section 6.3)."""

    @abstractmethod
    async def dispatch(self, event: SosEvent, context: PatientContext) -> DispatchResult:
        """Dispatches an emergency team or alerts human on-duty dispatcher."""
        ...


class ManualDispatch(EmergencyDispatcher):
    """Dispatcher displaying complete card to on-duty staff for human 103 dialing."""

    async def dispatch(self, event: SosEvent, context: PatientContext) -> DispatchResult:
        logger.info(
            f"Manual dispatch invoked for SOS {event.id} (Patient {event.patient_id}): "
            f"address={event.address_snapshot.get('street', UNKNOWN)}, "
            f"landmark={event.address_snapshot.get('landmark', UNKNOWN)}"
        )
        return DispatchResult(
            accepted=True,
            method="manual_call_103",
            message="Navbatchi xabardor qilindi — 103 ga qo'ng'iroq kutilmoqda",
        )


class Service103Adapter(EmergencyDispatcher):
    """Future adapter for direct automated National 103 Ambulance REST API integration."""

    async def dispatch(self, event: SosEvent, context: PatientContext) -> DispatchResult:
        logger.warning("103 API is not yet plugged in, falling back to manual dispatch")
        raise NotImplementedError("103 integratsiyasi hali ulanmagan")
