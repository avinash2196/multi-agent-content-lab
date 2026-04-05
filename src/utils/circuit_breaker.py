from __future__ import annotations

import time
from typing import Callable, Optional


class CircuitBreaker:
    """Protects downstream services from being overwhelmed when they are failing.

    How it works (three states):
        - **closed** (normal): requests pass through; failures are counted.
        - **open** (tripped): all requests are rejected immediately without
          calling the service, giving it time to recover.
        - **half-open** (testing): after the timeout expires one request is
          allowed through.  A success resets to closed; a failure reopens.

    Why this matters:
        Without a circuit breaker, a slow or failing API can cause your entire
        pipeline to hang or retry indefinitely, exhausting threads/connections
        and making the outage worse.  This pattern comes from Michael Nygard's
        *Release It!* and is fundamental in microservice architectures.

    Simplification for learning:
        This implementation is not thread-safe. A production version would use
        a lock around state transitions, or delegate state to an external store
        so multiple processes share the same breaker.

    Args:
        failure_threshold: Number of consecutive failures before the breaker
            trips to ``open``.
        reset_timeout: Seconds to wait in ``open`` before allowing a test
            request through (``half-open`` transition).
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "closed"  # closed | open | half-open
        self.opened_at: Optional[float] = None

    def allow(self) -> bool:
        """Return True if a request should be allowed through right now."""
        if self.state == "open":
            if self.opened_at and (time.time() - self.opened_at) > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        return True

    def record_success(self) -> None:
        """Reset the breaker to closed after a successful call."""
        self.failures = 0
        self.state = "closed"
        self.opened_at = None

    def record_failure(self) -> None:
        """Increment the failure counter; trip the breaker if threshold is reached."""
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.time()

    def wrap(self, func: Callable):
        """Decorator that automatically records success/failure around a callable."""
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
