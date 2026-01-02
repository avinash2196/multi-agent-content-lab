import pytest

from src.services.search_gateway import SearchGateway
from src.cache import CacheManager
from src.utils.rate_limiter import RateLimiter


class FakeProvider:
    def __init__(self, name: str, results, should_fail=False):
        self.name = name
        self.results = results
        self.should_fail = should_fail
        self.calls = 0

    async def search(self, query: str, num_results: int = 5, **params):
        self.calls += 1
        if self.should_fail:
            raise RuntimeError(f"{self.name} fail")
        return self.results[:num_results]


@pytest.mark.asyncio
async def test_gateway_uses_cache_and_rate_limit():
    cache = CacheManager(ttl_seconds=100)
    rl = RateLimiter(max_requests=2, window_seconds=60)
    provider = FakeProvider("p1", [1, 2, 3])
    gw = SearchGateway(providers=[provider], cache=cache, rate_limiter=rl)

    r1 = await gw.search("ai", num_results=2)
    r2 = await gw.search("ai", num_results=2)

    assert r1 == r2
    assert provider.calls == 1  # second call from cache


@pytest.mark.asyncio
async def test_gateway_fallback_on_failure():
    good = FakeProvider("good", ["ok"], should_fail=False)
    bad = FakeProvider("bad", ["bad"], should_fail=True)
    gw = SearchGateway(providers=[bad, good])

    result = await gw.search("test")

    assert result == ["ok"]
    assert bad.calls == 1
    assert good.calls == 1
