from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import Text, cast, false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clinical_scope import clinician_patient_ids
from app.auth.deps import CurrentUser, _apply_rls_context, _decode_bearer, require_admin, require_clinician
from app.core.db import get_db_context, get_session
from app.core.realtime import realtime_hub
from app.core.security import decode_token
from app.models import RealtimeEventOutbox
from app.schemas.common import CLINICIAN_ROLES

router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])
ALLOWED_TOPICS = {
    "reading.accepted",
    "alert.created",
    "task.created",
    "task.acknowledged",
    "task.done",
    "task.reassigned",
    "sos.raised",
    "sos.cancelled",
    "sos.acknowledged",
    "sos.dispatched",
    "sos.resolved",
}


def _payload_visible(payload: dict[str, Any], *, role: str, tenant_ids: set[str]) -> bool:
    tenant_id = payload.get("tenant_id")
    if tenant_id and str(tenant_id) in tenant_ids:
        return True
    payload_tenant_ids = payload.get("tenant_ids")
    if isinstance(payload_tenant_ids, list) and tenant_ids.intersection(str(item) for item in payload_tenant_ids):
        return True
    return False


@router.get("/status", summary="Realtime transport status")
async def realtime_status(_: CurrentUser = Depends(require_admin)) -> dict:
    stats = realtime_hub.stats()
    return {"backend": stats["backend"], "subscribers": stats["subscribers"]}


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
    tenant_ids = [str(item) for item in current_user.tenant_ids]
    scoped_events = [
        RealtimeEventOutbox.payload["tenant_id"].astext.in_(tenant_ids),
        *[
            RealtimeEventOutbox.payload["tenant_ids"].contains([tenant_id])
            for tenant_id in tenant_ids
        ],
    ]
    stmt = stmt.where(or_(*scoped_events) if scoped_events else false())
    if topic:
        stmt = stmt.where(RealtimeEventOutbox.topic == topic)
    # Filter before LIMIT so invisible events cannot starve the replay cursor.
    visible_ids = clinician_patient_ids(current_user.id, current_user.tenant_ids).subquery()
    stmt = stmt.where(RealtimeEventOutbox.payload["patient_id"].astext.in_(
        select(cast(visible_ids.c.patient_id, Text))
    ))
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": row.id,
            "topic": row.topic,
            "payload": row.payload,
            "created_at": row.created_at.isoformat(),
            "published_at": row.published_at.isoformat() if row.published_at else None,
        }
        for row in rows
    ]


class _SocketScope:
    """Authorization of an open socket, re-derived from the database.

    The token is re-validated and the visible patient set reloaded at least
    every REFRESH_SECONDS, so expiry, removal from a clinic, demotion or a
    territory change cuts the stream without waiting for a reconnect.
    """

    REFRESH_SECONDS = 10.0

    def __init__(self, token: str) -> None:
        self.token = token
        self.expires_at = 0.0
        self.loaded_at = 0.0
        self.tenant_ids: set[str] = set()
        self.patient_ids: set[str] = set()

    async def refresh(self) -> None:
        payload = decode_token(self.token)  # raises once expired
        principal = _decode_bearer(HTTPAuthorizationCredentials(scheme="Bearer", credentials=self.token))
        if principal.role not in CLINICIAN_ROLES:
            raise PermissionError("clinician token required")
        async with get_db_context() as session:
            principal = await _apply_rls_context(principal, session)
            rows = await session.execute(clinician_patient_ids(principal.id, principal.tenant_ids))
            self.patient_ids = {str(item) for item in rows.scalars().all()}
        self.tenant_ids = {str(item) for item in principal.tenant_ids}
        self.expires_at = float(payload["exp"])
        self.loaded_at = time.monotonic()

    def seconds_until_check(self) -> float:
        until_refresh = self.loaded_at + self.REFRESH_SECONDS - time.monotonic()
        until_expiry = self.expires_at - time.time()
        return max(0.0, min(until_refresh, until_expiry))

    def allows(self, event: Any) -> bool:
        patient_id = event.payload.get("patient_id")
        return (
            patient_id is not None
            and str(patient_id) in self.patient_ids
            and _payload_visible(event.payload, role="", tenant_ids=self.tenant_ids)
        )


@router.websocket("/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    offered_protocols = {
        item.strip()
        for item in websocket.headers.get("sec-websocket-protocol", "").split(",")
    }
    authorization = websocket.headers.get("authorization", "")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        token = next(
            (
                item.removeprefix("bearer.")
                for item in offered_protocols
                if item.startswith("bearer.")
            ),
            "",
        )
    topic = websocket.query_params.get("topic", "*")
    scope = _SocketScope(token)
    try:
        if "wmax" not in offered_protocols and not authorization:
            raise ValueError("WebSocket auth protocol required")
        if topic != "*" and topic not in ALLOWED_TOPICS:
            raise ValueError("Unsupported realtime topic")
        await scope.refresh()
    except Exception:
        await websocket.close(code=1008)
        return

    queue = await realtime_hub.subscribe(topic)
    try:
        await websocket.accept(subprotocol="wmax" if "wmax" in offered_protocols else None)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=scope.seconds_until_check())
            except asyncio.TimeoutError:
                event = None
            try:
                if scope.seconds_until_check() <= 0:
                    await scope.refresh()
                if event is not None and scope.allows(event):
                    await websocket.send_json(event.as_dict())
            finally:
                if event is not None:
                    queue.task_done()
    except WebSocketDisconnect:
        return
    except Exception:
        # Expired token, revoked membership or a broken socket all end here.
        try:
            await websocket.close(code=1008)
        except Exception:
            pass
    finally:
        await realtime_hub.unsubscribe(topic, queue)
