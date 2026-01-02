import pytest
from types import SimpleNamespace

from src.services import SerpService, SearchResult


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, payload: dict, status_code: int = 200):
        self.payload = payload
        self.status_code = status_code
        self.requested_params = None

    async def get(self, url, params=None):
        self.requested_params = params
        return FakeResponse(self.status_code, self.payload)

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_serp_service_returns_results():
    payload = {
        "organic_results": [
            {"title": "Result 1", "link": "https://example.com/1", "snippet": "Snippet 1"},
            {"title": "Result 2", "link": "https://example.com/2", "snippet": "Snippet 2"},
        ]
    }
    client = FakeAsyncClient(payload)
    service = SerpService(api_key="test", client=client)

    results = await service.search("test query", num_results=2)

    assert len(results) == 2
    assert results[0].title == "Result 1"
    assert results[1].link.endswith("/2")
    assert client.requested_params["q"] == "test query"


@pytest.mark.asyncio
async def test_serp_service_handles_errors():
    payload = {"error": "failed"}
    client = FakeAsyncClient(payload, status_code=500)
    service = SerpService(api_key="test", client=client)

    with pytest.raises(RuntimeError):
        await service.search("bad query")


@pytest.mark.asyncio
async def test_serp_service_requires_query():
    service = SerpService(api_key="test", client=FakeAsyncClient({}))
    with pytest.raises(ValueError):
        await service.search("")
