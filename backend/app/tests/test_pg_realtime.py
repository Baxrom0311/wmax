"""WebSocket authorization regressions (finding 5): the real realtime_ws
handler, the real hub and PostgreSQL relationships; only the socket transport
is replaced by an in-memory double."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

from app.api import realtime as realtime_api
from app.core.realtime import realtime_hub
from app.core.security import create_access_token
from app.tests.pg_support import World, bearer, requires_pg, rollback_session

pytestmark = requires_pg


class FakeSocket:
    def __init__(self, token: str) -> None:
        self.headers = {"authorization": f"Bearer {token}", "sec-websocket-protocol": ""}
        self.query_params = {"topic": "alert.created"}
        self.sent: list[dict] = []
        self.accepted = asyncio.Event()
        self.closed_with: int | None = None

    async def accept(self, subprotocol=None) -> None:
        self.accepted.set()

    async def send_json(self, data) -> None:
        self.sent.append(data)

    async def close(self, code: int = 1000) -> None:
        self.closed_with = code


@pytest.fixture
async def world(monkeypatch):
    async with rollback_session() as session:
        lock = asyncio.Lock()

        @asynccontextmanager
        async def shared_context():
            # Socket re-checks reuse the test transaction, serialized.
            async with lock:
                yield session

        monkeypatch.setattr(realtime_api, "get_db_context", shared_context)
        monkeypatch.setattr(realtime_api._SocketScope, "REFRESH_SECONDS", 0.2)
        yield World(session)


async def _publish(patient, tenant) -> None:
    await realtime_hub.publish("alert.created", {
        "patient_id": str(patient.id), "tenant_ids": [str(tenant.id)], "level": "red",
    })


async def _wait(predicate, timeout: float = 3.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("condition not reached")
        await asyncio.sleep(0.02)


async def test_socket_only_streams_patients_in_current_scope_and_stops_after_removal(world):
    clinic = await world.tenant()
    nurse, member = await world.member(clinic, "nurse", mahallas=("Navbahor",))
    own = await world.patient(clinic, mahalla="Navbahor")
    other = await world.patient(clinic, mahalla="Gulshan")
    socket = FakeSocket(bearer(nurse, "nurse", tenant_ids=[clinic.id]))

    handler = asyncio.create_task(realtime_api.realtime_ws(socket))
    await asyncio.wait_for(socket.accepted.wait(), 3)

    await _publish(other, clinic)
    await _publish(own, clinic)
    await _wait(lambda: len(socket.sent) == 1)
    assert socket.sent[0]["payload"]["patient_id"] == str(own.id)

    member.left_at = datetime.now(timezone.utc)
    await world.session.flush()
    await _wait(lambda: handler.done())
    assert socket.closed_with == 1008
    await _publish(own, clinic)
    assert len(socket.sent) == 1


async def test_socket_closes_when_access_token_expires(world):
    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",))
    token = create_access_token(
        subject=str(nurse.id),
        claims={"role": "nurse", "full_name": "x", "tenant_ids": [str(clinic.id)]},
        expires_delta=timedelta(seconds=1),
    )
    socket = FakeSocket(token)
    handler = asyncio.create_task(realtime_api.realtime_ws(socket))
    await asyncio.wait_for(socket.accepted.wait(), 3)
    await _wait(lambda: handler.done(), timeout=5)
    assert socket.closed_with == 1008


async def test_socket_rejects_clinician_without_current_membership(world):
    clinic = await world.tenant()
    stranger = await world.account()
    socket = FakeSocket(bearer(stranger, "doctor", tenant_ids=[clinic.id]))
    await asyncio.wait_for(realtime_api.realtime_ws(socket), 3)
    assert not socket.accepted.is_set()
    assert socket.closed_with == 1008
