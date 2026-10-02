from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician
from app.core.db import get_session
from app.core.realtime import realtime_hub, send_websocket_events
from app.core.security import decode_token
from app.models import RealtimeEventOutbox
from app.schemas.common import CLINICIAN_ROLES

router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])


def _uuid_set(raw: object) -> set[str]:
    if not isinstance(raw, list):
        return set()
    values: set[str] = set()
    for item in raw:
        try:
            values.add(str(uuid.UUID(str(item))))
        except (TypeError, ValueError):
            continue
    return values


def _payload_visible(payload: dict[str, Any], *, role: str, tenant_ids: set[str]) -> bool:
    if role == "admin":
        return True
    tenant_id = payload.get("tenant_id")
    if tenant_id and str(tenant_id) in tenant_ids:
        return True
    payload_tenant_ids = payload.get("tenant_ids")
    if isinstance(payload_tenant_ids, list) and tenant_ids.intersection(str(item) for item in payload_tenant_ids):
        return True
    return "patient_id" not in payload


@router.get("/status", summary="Realtime transport status")
async def realtime_status() -> dict:
    return realtime_hub.stats()


@router.get("/events", summary="Replay persisted realtime events after reconnect")
async def list_realtime_events(
    topic: str | None = Query(None, description="Optional exact topic filter"),
    after_id: int = Query(0, ge=0, description="Return events with id greater than this"),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    stmt = (
        select(RealtimeEventOutbox)
        .where(RealtimeEventOutbox.id > after_id)
        .order_by(RealtimeEventOutbox.id.asc())
        .limit(limit)
    )
    if topic:
        stmt = stmt.where(RealtimeEventOutbox.topic == topic)
    rows = (await session.execute(stmt)).scalars().all()
    tenant_ids = {str(item) for item in current_user.tenant_ids}
    return [
        {
            "id": row.id,
            "topic": row.topic,
            "payload": row.payload,
            "created_at": row.created_at.isoformat(),
            "published_at": row.published_at.isoformat() if row.published_at else None,
        }
        for row in rows
        if _payload_visible(row.payload, role=current_user.role, tenant_ids=tenant_ids)
    ]


@router.websocket("/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    topic = websocket.query_params.get("topic", "*")
    try:
        payload = decode_token(token or "")
        role = payload.get("role")
        if payload.get("type") != "access" or role not in CLINICIAN_ROLES:
            await websocket.close(code=1008)
            return
        tenant_ids = _uuid_set(payload.get("tenant_ids"))
    except Exception:
        await websocket.close(code=1008)
        return

    try:
        await send_websocket_events(
            websocket,
            topic,
            event_filter=lambda event: _payload_visible(
                event.payload,
                role=str(role),
                tenant_ids=tenant_ids,
            ),
        )
    except WebSocketDisconnect:
        return
