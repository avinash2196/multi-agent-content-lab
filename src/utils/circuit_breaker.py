from __future__ import annotations

import time
from typing import Callable, Optional


class CircuitBreaker:
    """Simple circuit breaker with failure threshold and cool-down."""

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "closed"  # closed, open, half-open
        self.opened_at: Optional[float] = None

    def allow(self) -> bool:
        if self.state == "open":
            if self.opened_at and (time.time() - self.opened_at) > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        return True

    def record_success(self) -> None:
        self.failures = 0
        self.state = "closed"
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.time()

    def wrap(self, func: Callable):
        def wrapper(*args, **kwargs):
            if not self.allow():
                raise RuntimeError("circuit_open")
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception:
                self.record_failure()
                raise
        return wrapper
