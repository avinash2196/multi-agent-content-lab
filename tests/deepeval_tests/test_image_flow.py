"""DeepEval tests for Image Agent flow"""
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

from src.agents import ImageAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_image_prompt_relevancy():
    """Test that generated image prompt is relevant to the topic."""
    agent = ImageAgent()
    
    query = "Modern office workspace with collaborative design"
    context = {
        "style": "professional",
        "research": {
            "summary": "Modern offices emphasize collaboration, natural light, and flexible spaces",
            "key_points": [
                "Open floor plans",
                "Natural lighting",
                "Collaborative zones",
            ],
        },
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-image-1")
    
    response = await agent.execute(input_data)
    
    # Get the generated prompt
    prompt = response.metadata.get("prompt", "")
    
    assert len(prompt) > 0, "Prompt should be generated"
    
    # Test that prompt is relevant to the input
    test_case = LLMTestCase(
        input=query,
        actual_output=prompt,
    )
    
    relevancy_metric = AnswerRelevancyMetric(threshold=0.5)
    assert_test(test_case, [relevancy_metric])


@pytest.mark.asyncio
async def test_image_metadata_quality():
    """Test that image generation includes proper metadata."""
    agent = ImageAgent()
    
    query = "Sustainable energy solutions"
    context = {
        "style": "clean",
        "aspect_ratio": "1024x1024",
        "n": 1,
        "research": {
            "summary": "Renewable energy includes solar, wind, and hydroelectric power",
            "key_points": [
                "Solar panel technology",
                "Wind turbine efficiency",
                "Grid integration",
            ],
        },
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-image-3")
    
    response = await agent.execute(input_data)
    metadata = response.metadata
    
    # Verify metadata completeness
    assert "prompt" in metadata
    assert "urls" in metadata
    assert "aspect_ratio" in metadata
    assert metadata["aspect_ratio"] == "1024x1024"
    assert "count" in metadata
    assert metadata["count"] == 1
    
    # Test prompt quality
    prompt = metadata["prompt"]
    test_case = LLMTestCase(
        input=query,
        actual_output=prompt,
    )
    
    relevancy_metric = AnswerRelevancyMetric(threshold=0.6)
    assert_test(test_case, [relevancy_metric])


@pytest.mark.asyncio
async def test_image_prompt_style_integration():
    """Test that image prompt properly integrates style preferences."""
    agent = ImageAgent()
    
    query = "Digital marketing campaign visualization"
    
    styles = ["minimal", "vibrant", "professional", "artistic"]
    
    for style in styles:
        context = {
            "style": style,
            "research": {
                "summary": "Digital marketing uses data-driven strategies and creative content",
                "key_points": ["Social media engagement", "Content marketing", "Analytics"],
            },
        }
        
        input_data = AgentInput(
            query=query,
            context=context,
            session_id=f"deepeval-image-style-{style}"
        )
        
        response = await agent.execute(input_data)
        prompt = response.metadata.get("prompt", "")
        
        # Verify prompt is not empty and relates to query
        assert len(prompt) > 0, f"Prompt should be generated for style: {style}"
        
        test_case = LLMTestCase(
            input=f"{query} with {style} style",
            actual_output=prompt,
        )
        
        relevancy_metric = AnswerRelevancyMetric(threshold=0.45)
        assert_test(test_case, [relevancy_metric])


@pytest.mark.asyncio
async def test_image_prompt_fallback():
    """Test image prompt generation with minimal context (fallback behavior)."""
    agent = ImageAgent()
    
    query = "Technology innovation concept"
    context = {
        "style": "modern",
        # No research context provided
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-image-fallback")
    
    response = await agent.execute(input_data)
    
    prompt = response.metadata.get("prompt", "")
    
    # Even without research, should generate a reasonable prompt
    assert len(prompt) > 0, "Prompt should be generated even without research"
    assert query.lower() in prompt.lower() or "technology" in prompt.lower(), "Prompt should relate to query"
    
    test_case = LLMTestCase(
        input=query,
        actual_output=prompt,
    )
    
    relevancy_metric = AnswerRelevancyMetric(threshold=0.2)  # Very low threshold for fallback
    assert_test(test_case, [relevancy_metric])
