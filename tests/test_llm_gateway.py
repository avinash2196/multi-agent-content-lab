import pytest

from src.services.llm_gateway import LLMGateway
from src.utils.rate_limiter import RateLimiter


class FakeProvider:
    def __init__(self, name: str, response: str, should_fail: bool = False):
        self.name = name
        self.response = response
        self.should_fail = should_fail
        self.calls = 0

    async def chat(self, messages, model=None, **kwargs):
        self.calls += 1
        if self.should_fail:
            raise RuntimeError(f"{self.name}_fail")
        return self.response


@pytest.mark.asyncio
async def test_llm_gateway_fallbacks_to_next_provider():
    bad = FakeProvider("bad", response="", should_fail=True)
    good = FakeProvider("good", response="ok")
    gateway = LLMGateway(providers=[bad, good], rate_limiter=RateLimiter(max_requests=5, window_seconds=60))

    result = await gateway.chat([{"role": "user", "content": "hi"}])

    assert result == "ok"
    assert bad.calls == 1
    assert good.calls == 1


@pytest.mark.asyncio
async def test_llm_gateway_rate_limit_blocks_excess_calls():
    provider = FakeProvider("only", response="ok")
    gateway = LLMGateway(providers=[provider], rate_limiter=RateLimiter(max_requests=1, window_seconds=60))

    await gateway.chat([{"role": "user", "content": "first"}])

    with pytest.raises(RuntimeError):
        await gateway.chat([{"role": "user", "content": "second"}])

    assert provider.calls == 1


@pytest.mark.asyncio
async def test_llm_gateway_raises_when_all_providers_fail():
    bad1 = FakeProvider("bad1", response="", should_fail=True)
    bad2 = FakeProvider("bad2", response="", should_fail=True)
    gateway = LLMGateway(providers=[bad1, bad2])

    with pytest.raises(RuntimeError):
        await gateway.chat([{"role": "user", "content": "hi"}])

    assert bad1.calls == 1
    assert bad2.calls == 1
