import time

from src.utils.rate_limiter import RateLimiter


def test_rate_limiter_allows_within_limit():
    rl = RateLimiter(max_requests=3, window_seconds=1)
    assert rl.allow()
    assert rl.allow()
    assert rl.allow()
    assert rl.remaining() == 0
    assert rl.allow() is False or rl.remaining() == 0


def test_rate_limiter_blocks_and_recovers():
    rl = RateLimiter(max_requests=1, window_seconds=1)
    assert rl.allow()
    assert rl.allow() is False
    time.sleep(1.05)
    assert rl.allow()
