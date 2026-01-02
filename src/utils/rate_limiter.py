from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional


class RateLimiter:
    """Simple sliding-window rate limiter (requests per window_seconds)."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.events: Deque[float] = deque()

    def allow(self) -> bool:
        now = time.time()
        cutoff = now - self.window
        while self.events and self.events[0] < cutoff:
            self.events.popleft()
        if len(self.events) >= self.max_requests:
            return False
        self.events.append(now)
        return True

    def ensure(self) -> None:
        if not self.allow():
            raise RuntimeError("rate_limited")

    def remaining(self) -> int:
        now = time.time()
        cutoff = now - self.window
        while self.events and self.events[0] < cutoff:
            self.events.popleft()
        return max(0, self.max_requests - len(self.events))
