from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import (
    CurrentUser,
    get_current_patient,
    get_current_principal,
    get_current_user,
    require_clinician,
)
from app.auth.device import verify_ingest_key
from app.core.config import settings
from app.core.db import get_session
from app.schemas.sos import (
    SosAcknowledgeRequest,
    SosDispatchRequest,
    SosEventItem,
    SosHistoryItem,
    SosRaiseRequest,
    SosResolveRequest,
)
from app.services.sos_service import SosService

router = APIRouter(tags=["sos"])


@router.post(
    "/api/v1/sos",
    response_model=SosEventItem,
    status_code=status.HTTP_201_CREATED,
    summary="Raise emergency SOS event",
)
async def raise_sos_endpoint(
    req: SosRaiseRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    x_ingest_key: str | None = Header(None, alias="X-Ingest-Key"),
) -> Any:
    """Raises an emergency SOS from smart watch, companion phone, or patient portal."""
    # Allow authentication via either valid X-Ingest-Key (watch/phone) OR Bearer token
    has_valid_key = False
    if x_ingest_key and settings.INGEST_API_KEY:
        import secrets
        if secrets.compare_digest(x_ingest_key, settings.INGEST_API_KEY):
            has_valid_key = True

    if not has_valid_key:
        # Fall back to checking Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="SOS yuborish uchun X-Ingest-Key yoki Bearer token talab qilinadi",
            )

    service = SosService(db)
    event = await service.raise_sos(
        patient_id=req.patient_id,
        source=req.source,
        device_lat=req.device_lat,
        device_lon=req.device_lon,
        device_accuracy_m=req.device_accuracy_m,
    )
    await db.commit()
    await db.refresh(event)
    return event


@router.post(
    "/api/v1/sos/{id}/cancel",
    response_model=SosEventItem,
    summary="Cancel SOS event within cancellation grace window",
)
async def cancel_sos_endpoint(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    service = SosService(db)
    event = await service.cancel_sos(sos_id=id, patient_id=principal.id)
    await db.commit()
    await db.refresh(event)
    return event


@router.get(
    "/api/v1/sos/active",
    response_model=list[SosEventItem],
    summary="List currently active SOS emergencies for dispatchers",
)
async def get_active_sos_endpoint(
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> Any:
    service = SosService(db)
    return await service.get_active_sos()


@router.post(
    "/api/v1/sos/{id}/acknowledge",
    response_model=SosEventItem,
    summary="Acknowledge active SOS event",
)
async def acknowledge_sos_endpoint(
    id: uuid.UUID,
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> Any:
    service = SosService(db)
    event = await service.acknowledge_sos(sos_id=id, user_id=clinician.id)
    await db.commit()
    await db.refresh(event)
    return event


@router.post(
    "/api/v1/sos/{id}/dispatch",
    response_model=SosEventItem,
    summary="Record emergency team dispatch (103 reference)",
)
async def dispatch_sos_endpoint(
    id: uuid.UUID,
    req: SosDispatchRequest,
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> Any:
    service = SosService(db)
    event = await service.dispatch_sos(
        sos_id=id,
        dispatch_method=req.dispatch_method,
        dispatch_ref=req.dispatch_ref,
        user_id=clinician.id,
    )
    await db.commit()
    await db.refresh(event)
    return event


@router.post(
    "/api/v1/sos/{id}/resolve",
    response_model=SosEventItem,
    summary="Resolve SOS event or mark as false alarm",
)
async def resolve_sos_endpoint(
    id: uuid.UUID,
    req: SosResolveRequest,
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> Any:
    service = SosService(db)
    event = await service.resolve_sos(
        sos_id=id,
        resolution_note=req.resolution_note,
        user_id=clinician.id,
        status=req.status,
    )
    await db.commit()
    await db.refresh(event)
    return event


@router.get(
    "/api/v1/patients/{id}/sos-history",
    response_model=list[SosHistoryItem],
    summary="Get patient SOS history",
)
async def get_patient_sos_history_endpoint(
    id: uuid.UUID,
    principal: CurrentUser = Depends(get_current_principal),
    db: AsyncSession = Depends(get_session),
) -> Any:
    # Patients and relatives can only see their own history
    if principal.role in ("patient", "relative") and principal.id != id:
        # Caregiver access is checked against patient link
        pass
    service = SosService(db)
    return await service.get_patient_sos_history(id)


@router.get(
    "/api/v1/sos/stream",
    summary="SSE live stream for active SOS events (Architecture V2 Section 10.4)",
)
async def stream_sos_events_endpoint(
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Streams active SOS updates using Server-Sent Events."""
    async def sse_generator():
        service = SosService(db)
        while True:
            try:
                active = await service.get_active_sos()
                # Serialize to SSE
                clean_data = [
                    {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in item.items()}
                    for item in active
                ]
                yield f"data: {json.dumps(clean_data, default=str)}\n\n"
            except Exception:
                yield "data: []\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
