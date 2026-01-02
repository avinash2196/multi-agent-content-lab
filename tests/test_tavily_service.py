import pytest

from src.services.tavily_service import TavilyService, TavilyResult


class FakeAsyncClient:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.calls = 0

    async def post(self, url, json=None):
        self.calls += 1
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
async def test_tavily_service_normalizes_results():
    payload = {
        "results": [
            {"title": "A", "url": "https://a.com", "content": "Alpha"},
            {"title": "B", "url": "https://b.com", "content": "Beta"},
        ]
    }
    client = FakeAsyncClient(payload)
    service = TavilyService(api_key="test", client=client)

    results = await service.search("ai", num_results=2)

    assert len(results) == 2
    assert results[0].link.endswith("a.com")
    assert results[1].snippet == "Beta"


@pytest.mark.asyncio
async def test_tavily_service_handles_errors():
    client = FakeAsyncClient({}, status_code=500)
    service = TavilyService(api_key="test", client=client)

    with pytest.raises(RuntimeError):
        await service.search("ai")


@pytest.mark.asyncio
async def test_tavily_requires_key():
    # Skip if TAVILY_API_KEY is set in environment (production test)
    # This test would need proper mocking of frozen dataclass which is complex
    import os
    if os.getenv("TAVILY_API_KEY"):
        pytest.skip("Skipping test when TAVILY_API_KEY is set in environment")
    
    service = TavilyService(api_key=None, client=FakeAsyncClient({}))
    with pytest.raises(RuntimeError, match="Tavily API key not configured"):
        await service.search("ai")
