import pytest

from src.agents import BlogWriterAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_blog_writer_generates_content_with_research():
    agent = BlogWriterAgent(config={"keywords": ["ai", "machine learning"]})
    input_data = AgentInput(
        query="AI in healthcare",
        context={
            "research": {
                "summary": "AI is transforming healthcare across diagnostics and operations.",
                "key_points": [
                    "Diagnostic support with imaging",
                    "Predictive analytics for patient outcomes",
                    "Operational efficiency and triage",
                ],
            }
        },
    )

    response = await agent.run(input_data)

    assert response.output.success is True
    assert "AI in healthcare" in response.output.content
    assert "##" in response.output.content  # headings present
    assert response.output.metadata["meta_description"].startswith("AI is transforming")
    assert response.output.metadata["quality"]["word_count"] > 5
    assert response.output.metadata["slug"] == "ai-in-healthcare"


@pytest.mark.asyncio
async def test_blog_writer_handles_missing_research():
    agent = BlogWriterAgent()
    input_data = AgentInput(query="Sustainability practices", context={})

    response = await agent.run(input_data)

    assert response.output.success is True
    # LLM may capitalize or rephrase the topic  
    assert "sustainability" in response.output.content.lower() or "practice" in response.output.content.lower()
    assert response.output.metadata["outline"]
