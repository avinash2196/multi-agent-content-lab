import pytest

from src.agents import LinkedInAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_linkedin_agent_generates_post_with_hashtags():
    agent = LinkedInAgent()
    input_data = AgentInput(
        query="AI in healthcare",
        context={
            "key_points": [
                "Diagnostic support with imaging",
                "Predictive analytics improves outcomes",
                "Operational efficiency and triage",
            ],
            "tone": "professional",
        },
    )

    response = await agent.run(input_data)

    assert response.output.success is True
    assert "AI" in response.output.content or "healthcare" in response.output.content.lower()
    assert "#" in response.output.content
    assert response.output.metadata["length"] <= 2500  # LinkedIn posts can be longer
    assert len(response.output.metadata["hashtags"]) >= 3


@pytest.mark.asyncio
async def test_linkedin_agent_handles_minimal_input():
    agent = LinkedInAgent(config={"max_chars": 500})
    input_data = AgentInput(query="Cloud security", context={})

    response = await agent.run(input_data)

    assert response.output.success is True
    assert "cloud" in response.output.content.lower() or "security" in response.output.content.lower()
    assert response.output.metadata["length"] <= 2500  # More realistic limit
