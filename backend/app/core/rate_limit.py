from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Sliding window rate limiter with Redis backend and in-memory fallback.

    When Redis is available (via REDIS_URL), state is shared across all API
    replicas using a sorted set (ZSET). If Redis is unreachable, it falls back
    gracefully to thread-safe process memory.
    """

    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        redis_url: str | None = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._redis_url = redis_url if redis_url is not None else os.getenv("REDIS_URL")
        self.redis_client = None

        if self._redis_url:
            try:
                import redis

                self.redis_client = redis.Redis.from_url(
                    self._redis_url,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                )
            except Exception as err:
                logger.debug("Redis rate limiter init skipped: %s", err)
                self.redis_client = None

    def _prune(self, bucket: deque[float], now: float) -> None:
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

    def check(self, key: str) -> int:
        """Records an attempt. Returns seconds to wait, or 0 when allowed."""
        now = time.time()
        if self.redis_client:
            try:
                redis_key = f"wmax:ratelimit:{key}"
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(redis_key, 0, now - self.window_seconds)
                pipe.zcard(redis_key)
                pipe.zrange(redis_key, 0, 0, withscores=True)
                results = pipe.execute()
                count = results[1]
                oldest = results[2]

                if count >= self.max_attempts:
                    oldest_ts = oldest[0][1] if oldest else now - self.window_seconds
                    retry_after = int(self.window_seconds - (now - oldest_ts)) + 1
                    return max(retry_after, 1)

                pipe = self.redis_client.pipeline()
                pipe.zadd(redis_key, {str(uuid.uuid4()): now})
                pipe.expire(redis_key, self.window_seconds)
                pipe.execute()
                return 0
            except Exception as err:
                logger.debug("Redis check failed, falling back to memory: %s", err)

        # In-memory fallback
        mono_now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            self._prune(bucket, mono_now)

            if len(bucket) >= self.max_attempts:
                retry_after = int(self.window_seconds - (mono_now - bucket[0])) + 1
                return max(retry_after, 1)

            bucket.append(mono_now)
            return 0

    def reset(self, key: str) -> None:
        """Clears a bucket — called after a successful authentication."""
        if self.redis_client:
            try:
                self.redis_client.delete(f"wmax:ratelimit:{key}")
            except Exception:
                pass
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        """Clears all rate-limit buckets."""
        if self.redis_client:
            try:
                keys = self.redis_client.keys("wmax:ratelimit:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception:
                pass
        with self._lock:
            self._hits.clear()


login_limiter = SlidingWindowRateLimiter(
    max_attempts=settings.LOGIN_RATE_LIMIT_ATTEMPTS,
    window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SEC,
)


def enforce_login_rate_limit(key: str) -> None:
    """Raises 429 with Retry-After once a client exhausts its login attempts."""
    retry_after = login_limiter.check(key)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p urinish. Birozdan so'ng qayta urinib ko'ring.",
            headers={"Retry-After": str(retry_after)},
        )
