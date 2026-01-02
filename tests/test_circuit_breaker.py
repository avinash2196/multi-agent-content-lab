import pytest

from src.utils.circuit_breaker import CircuitBreaker


def test_circuit_breaker_blocks_when_open():
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=1000)
    breaker.record_failure()

    assert breaker.state == "open"
    assert breaker.allow() is False


def test_circuit_breaker_recovers_after_timeout_and_wraps():
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=0)

    def boom():
        raise ValueError("fail")

    wrapped = breaker.wrap(boom)

    with pytest.raises(ValueError):
        wrapped()

    assert breaker.state == "open"
    # With 0 timeout, need to wait a tiny bit for time comparison
    import time
    time.sleep(0.01)
    assert breaker.allow() is True  # moves to half-open after timeout
    breaker.record_success()
    assert breaker.state == "closed"
    assert breaker.failures == 0
