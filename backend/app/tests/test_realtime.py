from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from types import SimpleNamespace
import uuid

import pytest

from app.core.config import settings
from app.core.realtime import RealtimeEvent, RealtimeHub
from app.models import RealtimeEventOutbox
from app.services.live_event_service import LiveEventService


@pytest.mark.asyncio
async def test_realtime_hub_fans_out_to_topic_and_wildcard():
    hub = RealtimeHub()
    readings = await hub.subscribe("readings")
    wildcard = await hub.subscribe("*")

    delivered = await hub.publish("readings", {"accepted": ["2026-09-22T10:00:00Z"]})

    assert delivered == 2
    assert (await readings.get()).payload["accepted"] == ["2026-09-22T10:00:00Z"]
    assert (await wildcard.get()).topic == "readings"


@pytest.mark.asyncio
async def test_realtime_hub_unsubscribe_removes_subscriber():
    hub = RealtimeHub()
    queue = await hub.subscribe("readings")
    await hub.unsubscribe("readings", queue)

    assert hub.stats()["subscribers"] == 0


@pytest.mark.asyncio
async def test_live_event_service_persists_without_publishing_before_commit(monkeypatch):
    session = MagicMock()
    session.flush = AsyncMock()
    async def flush_with_id():
        session.add.call_args.args[0].id = 123

    session.flush = AsyncMock(side_effect=flush_with_id)
    publisher = AsyncMock(return_value=0)
    monkeypatch.setattr("app.services.live_event_service.realtime_hub.publish", publisher)

    event_id = await LiveEventService(session).publish("readings", {"accepted": ["w1"]})

    assert event_id == 123
    event = session.add.call_args.args[0]
    assert isinstance(event, RealtimeEventOutbox)
    assert event.topic == "readings"
    assert event.payload == {"accepted": ["w1"]}
    session.flush.assert_awaited_once()
    publisher.assert_not_awaited()


@pytest.mark.asyncio
async def test_live_event_service_publishes_alert_payload(monkeypatch):
    publisher = AsyncMock(return_value=0)
    monkeypatch.setattr("app.services.live_event_service.realtime_hub.publish", publisher)
    patient_id = uuid.uuid4()

    alert = SimpleNamespace(
        id=9,
        patient_id=patient_id,
        ts=datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc),
        level="red",
        composite_score=7.5,
        reason="critical_spo2",
    )

    await LiveEventService().publish_alert(alert)

    publisher.assert_awaited_once()
    topic, payload = publisher.await_args.args[:2]
    assert topic == "alert.created"
    assert payload["id"] == 9
    assert payload["patient_id"] == str(patient_id)
    assert payload["level"] == "red"


@pytest.mark.asyncio
async def test_live_event_service_publishes_task_payload(monkeypatch):
    publisher = AsyncMock(return_value=0)
    monkeypatch.setattr("app.services.live_event_service.realtime_hub.publish", publisher)
    patient_id = uuid.uuid4()
    assignee_id = uuid.uuid4()

    task = SimpleNamespace(
        id=12,
        patient_id=patient_id,
        status="acknowledged",
        kind="clinical",
        assignee_account_id=assignee_id,
        due_at=datetime(2026, 9, 22, 11, 0, tzinfo=timezone.utc),
    )

    await LiveEventService().publish_task(task, action="acknowledged")

    topic, payload = publisher.await_args.args[:2]
    assert topic == "task.acknowledged"
    assert payload["id"] == 12
    assert payload["assignee_account_id"] == str(assignee_id)


@pytest.mark.asyncio
async def test_live_event_service_publishes_sos_payload(monkeypatch):
    publisher = AsyncMock(return_value=0)
    monkeypatch.setattr("app.services.live_event_service.realtime_hub.publish", publisher)
    patient_id = uuid.uuid4()
    sos_id = uuid.uuid4()
    raised_at = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    event = SimpleNamespace(
        id=sos_id,
        patient_id=patient_id,
        status="raised",
        source="watch_button",
        raised_at=raised_at,
    )

    await LiveEventService().publish_sos(event, action="raised")

    topic, payload = publisher.await_args.args[:2]
    assert topic == "sos.raised"
    assert payload["id"] == str(sos_id)
    assert payload["patient_id"] == str(patient_id)
    assert payload["raised_at"] == raised_at.isoformat()


@pytest.mark.asyncio
async def test_realtime_hub_writes_to_redis_stream_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "REALTIME_TRANSPORT", "redis_streams")
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "REALTIME_STREAM_KEY", "wmax:test:realtime")
    hub = RealtimeHub()
    redis = AsyncMock()
    hub._redis = redis

    await hub.publish("reading.accepted", {"windows": ["w1"]}, event_id=321)

    redis.xadd.assert_awaited_once()
    stream_key, fields = redis.xadd.await_args.args[:2]
    assert stream_key == "wmax:test:realtime"
    assert fields["topic"] == "reading.accepted"
    assert fields["payload"] == '{"windows":["w1"]}'
    assert fields["origin"] == hub.instance_id
    assert fields["outbox_id"] == "321"
    assert "ts" in fields
    assert redis.xadd.await_args.kwargs["maxlen"] == 100_000
    assert redis.xadd.await_args.kwargs["approximate"] is True


@pytest.mark.asyncio
async def test_realtime_stream_fields_fan_out_locally_without_republish(monkeypatch):
    monkeypatch.setattr(settings, "REALTIME_TRANSPORT", "redis_streams")
    monkeypatch.setattr(settings, "REALTIME_STREAM_KEY", "wmax:test:realtime")
    hub = RealtimeHub()
    queue = await hub.subscribe("reading.accepted")
    redis = AsyncMock()
    hub._redis = redis

    event = hub._event_from_stream_fields(
        {
            "topic": "reading.accepted",
            "payload": '{"windows":["w1"]}',
            "ts": "2026-09-22T10:00:00+00:00",
            "outbox_id": "77",
        }
    )
    delivered = await hub.publish_local(event)

    assert delivered == 1
    received = await queue.get()
    assert isinstance(received, RealtimeEvent)
    assert received.topic == "reading.accepted"
    assert received.id == 77
    assert received.payload == {"windows": ["w1"]}
    redis.xadd.assert_not_called()


def test_realtime_hub_marks_own_stream_events():
    hub = RealtimeHub()

    assert hub._is_own_stream_event({"origin": hub.instance_id}) is True
    assert hub._is_own_stream_event({"origin": "other-instance"}) is False


def test_realtime_visibility_fails_closed_for_unscoped_events():
    from app.api.realtime import _payload_visible

    assert _payload_visible({"windows": ["w1"]}, role="doctor", tenant_ids={"tenant-a"}) is False
    assert _payload_visible(
        {"tenant_ids": ["tenant-a"]}, role="doctor", tenant_ids={"tenant-a"}
    ) is True
