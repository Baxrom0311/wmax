from __future__ import annotations

import asyncio
import json
import logging
import socket
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any

from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RealtimeEvent:
    topic: str
    payload: dict[str, Any]
    ts: datetime
    id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "payload": self.payload,
            "ts": self.ts.isoformat(),
        }


class RealtimeHub:
    """Small in-process fanout hub.

    The public interface is intentionally queue-like so it can be backed by
    Redis Streams or NATS JetStream without changing endpoint code.
    """

    def __init__(self) -> None:
        self._channels: dict[str, set[asyncio.Queue[RealtimeEvent]]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._redis = None
        self._bridge_task: asyncio.Task | None = None
        self._last_stream_id = "$"
        self.instance_id = f"{socket.gethostname()}:{uuid.uuid4().hex}"

    async def subscribe(self, topic: str) -> asyncio.Queue[RealtimeEvent]:
        queue: asyncio.Queue[RealtimeEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._channels[topic].add(queue)
        return queue

    async def unsubscribe(self, topic: str, queue: asyncio.Queue[RealtimeEvent]) -> None:
        async with self._lock:
            queues = self._channels.get(topic)
            if not queues:
                return
            queues.discard(queue)
            if not queues:
                self._channels.pop(topic, None)

    async def publish(
        self, topic: str, payload: dict[str, Any], event_id: int | None = None
    ) -> int:
        event = RealtimeEvent(
            id=event_id,
            topic=topic,
            payload=payload,
            ts=datetime.now(timezone.utc),
        )
        await self._publish_to_transport(event)
        return await self.publish_local(event)

    async def publish_local(self, event: RealtimeEvent) -> int:
        async with self._lock:
            subscribers = list(self._channels.get(event.topic, ())) + list(self._channels.get("*", ()))

        delivered = 0
        for queue in subscribers:
            try:
                queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.task_done()
                    queue.put_nowait(event)
                    delivered += 1
                except asyncio.QueueEmpty:
                    pass
        return delivered

    def start_stream_bridge(self) -> None:
        if settings.REALTIME_TRANSPORT != "redis_streams":
            return
        if self._bridge_task and not self._bridge_task.done():
            return
        self._bridge_task = asyncio.create_task(self._run_stream_bridge())

    async def stop_stream_bridge(self) -> None:
        if not self._bridge_task:
            return
        self._bridge_task.cancel()
        await asyncio.gather(self._bridge_task, return_exceptions=True)
        self._bridge_task = None

    async def _run_stream_bridge(self) -> None:
        while True:
            try:
                redis = await self._redis_client()
                rows = await redis.xread(
                    {settings.REALTIME_STREAM_KEY: self._last_stream_id},
                    count=100,
                    block=5000,
                )
                for _stream, messages in rows:
                    for message_id, fields in messages:
                        self._last_stream_id = message_id
                        if self._is_own_stream_event(fields):
                            continue
                        event = self._event_from_stream_fields(fields)
                        await self.publish_local(event)
            except asyncio.CancelledError:
                raise
            except Exception as err:
                logger.warning("Realtime Redis stream bridge failed: %s", err)
                await asyncio.sleep(2)

    def stats(self) -> dict[str, Any]:
        return {
            "backend": settings.REALTIME_TRANSPORT,
            "stream_key": settings.REALTIME_STREAM_KEY if settings.REALTIME_TRANSPORT == "redis_streams" else None,
            "instance_id": self.instance_id,
            "topics": {topic: len(queues) for topic, queues in self._channels.items()},
            "subscribers": sum(len(queues) for queues in self._channels.values()),
        }

    async def _publish_to_transport(self, event: RealtimeEvent) -> None:
        if settings.REALTIME_TRANSPORT == "memory":
            return
        if settings.REALTIME_TRANSPORT != "redis_streams":
            raise RuntimeError(f"Unsupported realtime transport: {settings.REALTIME_TRANSPORT}")
        if not settings.REDIS_URL:
            raise RuntimeError("REDIS_URL is required for redis_streams realtime transport")
        redis = await self._redis_client()
        await redis.xadd(
            settings.REALTIME_STREAM_KEY,
            {
                "topic": event.topic,
                "payload": json.dumps(event.payload, separators=(",", ":"), ensure_ascii=False),
                "ts": event.ts.isoformat(),
                "origin": self.instance_id,
                "outbox_id": "" if event.id is None else str(event.id),
            },
            maxlen=100_000,
            approximate=True,
        )

    async def _redis_client(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis
        except ImportError as exc:
            raise RuntimeError("redis package is required for redis_streams realtime transport") from exc
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            decode_responses=True,
        )
        return self._redis

    def _event_from_stream_fields(self, fields: dict[str, Any]) -> RealtimeEvent:
        raw_payload = fields.get("payload") or "{}"
        try:
            payload = json.loads(raw_payload)
        except (TypeError, json.JSONDecodeError):
            payload = {"raw": raw_payload}
        raw_ts = fields.get("ts")
        try:
            ts = datetime.fromisoformat(str(raw_ts)) if raw_ts else datetime.now(timezone.utc)
        except ValueError:
            ts = datetime.now(timezone.utc)
        return RealtimeEvent(
            id=self._optional_int(fields.get("outbox_id")),
            topic=str(fields.get("topic") or "unknown"),
            payload=payload if isinstance(payload, dict) else {"value": payload},
            ts=ts,
        )

    def _is_own_stream_event(self, fields: dict[str, Any]) -> bool:
        return str(fields.get("origin") or "") == self.instance_id

    def _optional_int(self, value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value))
        except ValueError:
            return None


realtime_hub = RealtimeHub()


async def send_websocket_events(
    websocket: WebSocket,
    topic: str,
    event_filter: Callable[[RealtimeEvent], bool] | None = None,
) -> None:
    queue = await realtime_hub.subscribe(topic)
    try:
        await websocket.accept()
        while True:
            event = await queue.get()
            if event_filter is None or event_filter(event):
                await websocket.send_json(event.as_dict())
            queue.task_done()
    finally:
        await realtime_hub.unsubscribe(topic, queue)
