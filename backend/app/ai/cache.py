from __future__ import annotations

import collections
import hashlib
import json
import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

DEFAULT_CACHE_TTL_SECONDS = 300.0  # 5 minutes (matches 5-minute smartwatch sampling window)
DEFAULT_MAX_ENTRIES = 1000


class CacheEntry:
    __slots__ = ("value", "expires_at", "created_at")

    def __init__(self, value: Any, ttl_seconds: float) -> None:
        self.value = value
        self.created_at = time.monotonic()
        self.expires_at = self.created_at + ttl_seconds

    @property
    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at


class AICache:
    """Thread-safe, process-wide LRU cache with TTL for AI clinical outputs.

    Eliminates redundant LLM roundtrips when clinicians refresh views or multiple
    team members inspect the same patient state during a shift.
    """

    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES, default_ttl: float = DEFAULT_CACHE_TTL_SECONDS) -> None:
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._entries: collections.OrderedDict[str, CacheEntry] = collections.OrderedDict()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def generate_key(prefix: str, identifier: str, state_fingerprint: dict[str, Any] | str) -> str:
        """Generates deterministic sha256 cache key from state parameters."""
        if isinstance(state_fingerprint, dict):
            serialized = json.dumps(state_fingerprint, sort_keys=True, default=str)
        else:
            serialized = str(state_fingerprint)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{identifier}:{digest}"

    def get(self, key: str) -> Any | None:
        """Retrieves entry if present and not expired; moves to end for LRU."""
        entry = self._entries.get(key)
        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired:
            self._entries.pop(key, None)
            self.misses += 1
            return None

        # Move to most recently used
        self._entries.move_to_end(key)
        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """Stores value with TTL; evicts oldest if capacity exceeded."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        if key in self._entries:
            self._entries.move_to_end(key)
        self._entries[key] = CacheEntry(value=value, ttl_seconds=ttl)

        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidates all cache keys matching a prefix (e.g. for a patient ID)."""
        to_remove = [k for k in self._entries if k.startswith(prefix)]
        for k in to_remove:
            self._entries.pop(k, None)
        return len(to_remove)

    def clear(self) -> None:
        self._entries.clear()
        self.hits = 0
        self.misses = 0


# Global singleton instance
ai_cache = AICache()
