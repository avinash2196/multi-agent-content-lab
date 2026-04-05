from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional


class RateLimiter:
    """Sliding-window rate limiter that enforces a maximum request count per time window.

    How it works:
        Each call to ``allow()`` records a timestamp.  Expired timestamps (older
        than ``window_seconds``) are evicted, then the current count is compared
        to ``max_requests``.  Because we track individual timestamps rather than
        fixed buckets, the window always covers the last N seconds relative to
        *now* — this avoids the "burst at boundary" problem of fixed-window
        counters.

    Why this matters:
        External APIs (OpenAI, SerpAPI, Tavily) impose rate limits.  Exceeding
        them results in 429 errors and potentially temporary bans.  Adding a
        limiter on the client side prevents this and gives us a predictable
        throughput budget.

    Simplification for learning:
        This is not thread-safe and stores state in memory only.  A production
        system would use Redis + Lua scripting (or a library like ``redis-py-ratelimit``)
        so limits are shared across multiple processes.

    Args:
        max_requests: Maximum number of requests allowed in the window.
        window_seconds: Length of the sliding window in seconds.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.events: Deque[float] = deque()

    def allow(self) -> bool:
        """Return True and record this request if still within the rate limit."""
        now = time.time()
        cutoff = now - self.window
        while self.events and self.events[0] < cutoff:
            self.events.popleft()
        if len(self.events) >= self.max_requests:
            return False
        self.events.append(now)
        return True

    def ensure(self) -> None:
        """Assert the rate limit is not exceeded; raise RuntimeError if it is.

        Use this in service call sites where you want to fail fast rather than
        silently dropping the request.
        """
        if not self.allow():
            raise RuntimeError("rate_limited")

    def remaining(self) -> int:
        """Return the number of requests still available in the current window."""
        now = time.time()
        cutoff = now - self.window
        while self.events and self.events[0] < cutoff:
            self.events.popleft()
        return max(0, self.max_requests - len(self.events))
