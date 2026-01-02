import time

from src.cache.cache_manager import CacheManager


def test_cache_set_get_and_expiry():
    cache = CacheManager(ttl_seconds=1)
    cache.set("key", "value")
    assert cache.get("key") == "value"
    time.sleep(1.2)
    assert cache.get("key") is None


def test_cache_decorator():
    cache = CacheManager(ttl_seconds=5)

    calls = {"count": 0}

    @cache.cached()
    def compute(x):
        calls["count"] += 1
        return x * 2

    assert compute(2) == 4
    assert compute(2) == 4
    assert calls["count"] == 1  # cached
