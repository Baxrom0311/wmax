from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import (
    CurrentUser,
    get_current_principal,
    require_clinician,
)
from app.auth.scope import assert_patient_access
from app.core.db import get_session
from app.core.security import decode_token
from app.schemas.common import CLINICIAN_ROLES
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


def _uuid_list(raw: object) -> list[uuid.UUID]:
    if not isinstance(raw, list):
        return []
    values: list[uuid.UUID] = []
    for item in raw:
        try:
            values.append(uuid.UUID(str(item)))
        except (TypeError, ValueError):
            continue
    return values


def _tenant_scope(clinician: CurrentUser) -> list[uuid.UUID] | None:
    return clinician.tenant_ids


def _principal_from_authorization(auth_header: str | None) -> CurrentUser:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SOS yuborish uchun X-Ingest-Key yoki Bearer token talab qilinadi",
        )
    try:
        payload = decode_token(auth_header.split(" ", 1)[1].strip())
        if payload.get("type") != "access":
            raise ValueError("not an access token")
        role = payload.get("role")
        if role not in CLINICIAN_ROLES and role not in {"relative", "patient"}:
            raise ValueError("unsupported role")
        return CurrentUser(
            id=uuid.UUID(str(payload["sub"])),
            full_name=payload.get("full_name", "Noma'lum"),
            role=role,
            district=payload.get("district"),
            phone=payload.get("phone"),
            tenant_ids=_uuid_list(payload.get("tenant_ids")),
            patient_ids=_uuid_list(payload.get("patient_ids")),
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati o'tgan",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err


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
) -> Any:
    """Raises an emergency SOS from smart watch, companion phone, or patient portal."""
    # A shared ingest key proves the app installation, not which patient the
    # caller may act for. SOS requires a user token with patient-level scope.
    principal = _principal_from_authorization(request.headers.get("Authorization"))
    await assert_patient_access(db, principal, req.patient_id)

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
    return await service.get_active_sos(tenant_ids=_tenant_scope(clinician))


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
    event = await service.acknowledge_sos(
        sos_id=id,
        user_id=clinician.id,
        tenant_ids=_tenant_scope(clinician),
    )
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
        tenant_ids=_tenant_scope(clinician),
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
        tenant_ids=_tenant_scope(clinician),
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
    await assert_patient_access(db, principal, id)
    service = SosService(db)
    return await service.get_patient_sos_history(id)


from app.core.db import get_db_context


@router.get(
    "/api/v1/sos/stream",
    summary="SSE live stream for active SOS events (Architecture V2 Section 10.4)",
)
async def stream_sos_events_endpoint(
    clinician: CurrentUser = Depends(require_clinician),
) -> StreamingResponse:
    """Streams active SOS updates using Server-Sent Events."""
    async def sse_generator():
        while True:
            try:
                async with get_db_context() as session:
                    service = SosService(session)
                    active = await service.get_active_sos(tenant_ids=_tenant_scope(clinician))
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
