from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, Hashable


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class CacheManager:
    """Simple in-memory TTL cache."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.store: Dict[Hashable, CacheEntry] = {}

    def get(self, key: Hashable) -> Optional[Any]:
        entry = self.store.get(key)
        if not entry:
            return None
        if entry.expires_at < time.time():
            self.store.pop(key, None)
            return None
        return entry.value

    def set(self, key: Hashable, value: Any, ttl: Optional[int] = None) -> None:
        expires = time.time() + (ttl if ttl is not None else self.ttl)
        self.store[key] = CacheEntry(value=value, expires_at=expires)

    def cached(self, key_func: Callable[..., Hashable] | None = None, ttl: Optional[int] = None):
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
        self.store.clear()
