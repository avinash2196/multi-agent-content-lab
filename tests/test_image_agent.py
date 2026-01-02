import pytest

from src.agents.image_agent import ImageAgent
from src.agents.base_agent import AgentInput


class FakeDalleService:
    def __init__(self):
        self.calls = []

    async def generate(self, prompt: str, size: str, n: int):
        self.calls.append({"prompt": prompt, "size": size, "n": n})
        return {
            "urls": ["https://img.local/one.png"],
            "created": 1234,
        }


@pytest.mark.asyncio
async def test_image_agent_uses_prompt_optimizer_and_returns_urls():
    dalle = FakeDalleService()
    agent = ImageAgent(dalle_service=dalle)

    input_data = AgentInput(
        query="sunset beach",
        context={
            "style": "minimal",
            "aspect_ratio": "512x512",
            "n": 1,
            "context": "portfolio card",
        },
    )

    output = await agent.execute(input_data)

    assert "https://img.local/one.png" in output.content
    assert output.metadata["aspect_ratio"] == "512x512"
    assert dalle.calls[0]["size"] == "512x512"
    assert "sunset beach" in dalle.calls[0]["prompt"].lower()
    assert "minimal" in dalle.calls[0]["prompt"].lower()


@pytest.mark.asyncio
async def test_image_agent_handles_failure_gracefully():
    class FailingDalle(FakeDalleService):
        async def generate(self, prompt: str, size: str, n: int):  # type: ignore[override]
            raise RuntimeError("fail")

    agent = ImageAgent(dalle_service=FailingDalle())
    input_data = AgentInput(query="bad input")

    result = await agent.run(input_data)

    assert result.output.success is False
    assert result.output.metadata["error_type"] == "RuntimeError"
