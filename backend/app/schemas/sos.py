from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SosRaiseRequest(BaseModel):
    patient_id: uuid.UUID
    source: Literal["watch_button", "phone_app", "relative_portal", "auto_critical"] = "watch_button"
    device_lat: float | None = None
    device_lon: float | None = None
    device_accuracy_m: float | None = None


class SosAcknowledgeRequest(BaseModel):
    pass


class SosDispatchRequest(BaseModel):
    dispatch_method: str = "manual_call_103"
    dispatch_ref: str | None = None


class SosResolveRequest(BaseModel):
    resolution_note: str
    status: Literal["resolved", "false_alarm"] = "resolved"


class SosEventItem(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str | None = None
    source: str
    status: str
    raised_at: datetime
    address_snapshot: dict[str, Any]
    clinical_snapshot: dict[str, Any]
    vitals_snapshot: dict[str, Any] | None = None
    device_lat: float | None = None
    device_lon: float | None = None
    device_accuracy_m: float | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: uuid.UUID | None = None
    dispatched_at: datetime | None = None
    dispatch_method: str | None = None
    dispatch_ref: str | None = None
    resolved_at: datetime | None = None
    resolved_by: uuid.UUID | None = None
    resolution_note: str | None = None
    cancelled_at: datetime | None = None
    created_at: datetime


class SosHistoryItem(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    source: str
    status: str
    raised_at: datetime
    resolved_at: datetime | None = None
    cancelled_at: datetime | None = None
    resolution_note: str | None = None
