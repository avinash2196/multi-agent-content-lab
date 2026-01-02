import pytest

from src.services.serp_service import SerpService, SearchResult
from src.cache.cache_manager import CacheManager


class FakeAsyncClient:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.call_count = 0

    async def get(self, url, params=None):
        self.call_count += 1
        class Resp:
            def __init__(self, status_code, payload):
                self.status_code = status_code
                self._payload = payload
                self.text = str(payload)
            def json(self):
                return self._payload
        return Resp(self.status_code, self.payload)

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_serp_service_uses_cache():
    payload = {"organic_results": [{"title": "A", "link": "https://a.com", "snippet": "A"}]}
    client = FakeAsyncClient(payload)
    cache = CacheManager(ttl_seconds=100)
    service = SerpService(api_key="test", client=client)
    service.cache = cache

    # First call hits client
    results1 = await service.search("ai", num_results=1)
    # Second call should come from cache
    results2 = await service.search("ai", num_results=1)

    assert len(results1) == len(results2) == 1
    assert client.call_count == 1
