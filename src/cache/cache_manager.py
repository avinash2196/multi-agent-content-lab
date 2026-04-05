from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, Hashable


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class CacheManager:
    """In-memory TTL (time-to-live) cache with optional decorator support.

    Purpose:
        Many steps in the pipeline (especially web search) are expensive and
        can safely return the same result if called again within a short window.
        This cache avoids redundant API calls during a single workflow run,
        reducing latency and cost.

    How it fits into the system:
        - ``ResearchAgent`` caches search results keyed on the query string.
        - ``SearchGateway`` passes the same cache instance to each provider so
          a hit on SerpAPI avoids also calling Tavily.

    Design trade-off:
        In-memory storage means the cache is per-process and per-run.  Reuse
        across runs or across multiple backend workers requires an external
        store (Redis is the typical choice).  For this learning project,
        simplicity wins.

    Learning note:
        The ``cached()`` decorator is an example of a **higher-order function**:
        it takes a key-building function and returns a decorator that wraps any
        callable with cache-check-then-compute logic.

    Args:
        ttl_seconds: Default time-to-live for cache entries in seconds.
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.store: Dict[Hashable, CacheEntry] = {}

    def get(self, key: Hashable) -> Optional[Any]:
        """Return the cached value for ``key``, or None if missing/expired."""
        entry = self.store.get(key)
        if not entry:
            return None
        if entry.expires_at < time.time():
            self.store.pop(key, None)
            return None
        return entry.value

    def set(self, key: Hashable, value: Any, ttl: Optional[int] = None) -> None:
        """Store ``value`` under ``key`` with an optional override TTL."""
        expires = time.time() + (ttl if ttl is not None else self.ttl)
        self.store[key] = CacheEntry(value=value, expires_at=expires)

    def cached(self, key_func: Callable[..., Hashable] | None = None, ttl: Optional[int] = None):
        """Decorator that wraps a function with transparent cache-check-then-call logic.

        Args:
            key_func: Optional callable that receives the same args as the
                decorated function and returns the cache key.  If omitted, a
                default key is built from the function name and arguments.
            ttl: Optional per-call TTL override.
        """
        def decorator(fn: Callable):
            def wrapper(*args, **kwargs):
                key = key_func(*args, **kwargs) if key_func else (fn.__name__, args, frozenset(kwargs.items()))
                cached_val = self.get(key)
                if cached_val is not None:
                    return cached_val
                result = fn(*args, **kwargs)
                self.set(key, result, ttl=ttl)
                return result
            return wrapper
        return decorator

    def clear(self):
        """Evict all entries — useful for testing or session teardown."""
        self.store.clear()
