import pytest
from types import SimpleNamespace

from src.services.dalle_service import DalleService
from src.utils.rate_limiter import RateLimiter
from src.utils.circuit_breaker import CircuitBreaker


class FakeImages:
    def __init__(self, urls):
        self.urls = urls
        self.kwargs = None

    async def generate(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(data=[SimpleNamespace(url=u) for u in self.urls], created=1700000000)


class FakeClient:
    def __init__(self, urls):
        self.images = FakeImages(urls)


@pytest.mark.asyncio
async def test_dalle_service_returns_urls():
    service = DalleService(api_key="test-key", rate_limiter=RateLimiter(5, 60), circuit_breaker=CircuitBreaker())
    service.client = FakeClient(["https://img/1.png", "https://img/2.png"])

    result = await service.generate("nice prompt", size="512x512", n=2)

    assert result["urls"] == ["https://img/1.png", "https://img/2.png"]
    assert result["created"] == 1700000000
    assert service.client.images.kwargs["size"] == "512x512"
    assert service.client.images.kwargs["n"] == 2


@pytest.mark.asyncio
async def test_dalle_service_respects_rate_limit():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    service = DalleService(api_key="test-key", rate_limiter=limiter, circuit_breaker=CircuitBreaker())
    service.client = FakeClient(["https://img/1.png"])

    await service.generate("first")

    with pytest.raises(RuntimeError):
        await service.generate("second")
