"""Cache in-memory sederhana dengan dukungan TTL dan fallback STALE (PRD §8)."""
from __future__ import annotations

import time
from typing import Any, Optional


class CachedItem:
    def __init__(self, value: Any, ttl_seconds: int) -> None:
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> int:
        return int(time.time() - self.created_at)


class SimpleCache:
    def __init__(self) -> None:
        self._store: dict[str, CachedItem] = {}

    def get(self, key: str) -> Optional[CachedItem]:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = CachedItem(value=value, ttl_seconds=ttl_seconds)

    def clear(self) -> None:
        self._store.clear()

