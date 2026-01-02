"""Tests for LinkedIn and image-related features"""
import pytest
from src.agents.image_agent import ImageAgent
from src.agents.linkedin_agent import LinkedInAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_image_agent_with_research_context():
    """Test image generation with research context."""
    agent = ImageAgent()
    
    input_data = AgentInput(
        query="AI innovation",
        context={
            "research": {
                "summary": "AI is transforming industries",
                "key_points": ["Automation", "Efficiency", "Innovation"],
            },
            "style": "modern",
        },
    )
    
    # This uses the new LLM-enhanced prompt building
    output = await agent.execute(input_data)
    
    assert output.success is True
    assert "prompt" in output.metadata


@pytest.mark.asyncio
async def test_linkedin_with_key_points():
    """Test LinkedIn generation with key points for hashtags."""
    agent = LinkedInAgent()
    
    input_data = AgentInput(
        query="Cloud computing trends",
        context={
            "key_points": [
                "Serverless architecture gaining popularity",
                "Multi-cloud strategies emerging",
                "Edge computing integration",
            ],
        },
    )
    
    response = await agent.run(input_data)
    
    assert response.output.success is True
    assert "hashtags" in response.output.metadata
    # Should have hashtags based on key points, not numbered placeholders
    hashtags = response.output.metadata["hashtags"]
    assert all(not tag.endswith(str(i)) for tag in hashtags for i in range(10))
