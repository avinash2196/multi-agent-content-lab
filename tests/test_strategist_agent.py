import pytest

from src.agents.strategist_agent import StrategistAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_strategist_agent_summarizes_outputs():
    agent = StrategistAgent()
    input_data = AgentInput(
        query="AI in healthcare",
        context={
            "research": {"summary": "AI transforms healthcare", "key_points": ["Diagnostics", "Triage"], "sources": [1, 2]},
            "blog": "# Blog content",
            "linkedin": "LinkedIn draft",
            "images": ["http://img/1.png", "http://img/2.png"],
        },
    )

    resp = await agent.run(input_data)

    assert resp.output.success is True
    assert "Content Package Summary" in resp.output.content
    assert resp.output.metadata["image_count"] == 2
    assert resp.output.metadata["has_blog"] is True
    assert resp.output.metadata["has_linkedin"] is True
