from __future__ import annotations

import logging
from abc import ABC, abstractmethod

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
    """Explicitly unavailable placeholder until a real duty workflow is wired."""

    async def dispatch(self, event: SosEvent, context: PatientContext) -> DispatchResult:
        logger.error("No emergency dispatch provider configured for SOS %s", event.id)
        return DispatchResult(
            accepted=False,
            method="manual_call_103",
            message="Navbatchi yoki 103 ga avtomatik xabar yuborilmadi. Mahalliy tez yordam raqamiga qo'ng'iroq qiling.",
        )


class Service103Adapter(EmergencyDispatcher):
    """Future adapter for direct automated National 103 Ambulance REST API integration."""

    async def dispatch(self, event: SosEvent, context: PatientContext) -> DispatchResult:
        logger.error("103 API is not configured")
        return await ManualDispatch().dispatch(event, context)
