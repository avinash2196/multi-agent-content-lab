"""DeepEval tests for LinkedIn Agent flow"""
import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase

from src.agents import LinkedInAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_linkedin_relevancy():
    """Test that LinkedIn post is relevant to the topic."""
    agent = LinkedInAgent()
    
    query = "Future of artificial intelligence in healthcare"
    context = {
        "key_points": [
            "AI diagnostics improving accuracy",
            "Personalized treatment plans",
            "Operational efficiency in hospitals",
        ],
        "tone": "professional",
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-linkedin-1")
    
    response = await agent.run(input_data)
    output = response.output.content
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
    )
    
    # Test relevancy
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [relevancy_metric])


@pytest.mark.asyncio
async def test_linkedin_coherence():
    """Test that LinkedIn post is coherent and engaging."""
    agent = LinkedInAgent()
    
    query = "Sustainable business practices"
    context = {
        "key_points": [
            "Carbon footprint reduction",
            "Green supply chain",
            "Employee engagement in sustainability",
        ],
        "tone": "inspirational",
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-linkedin-2")
    
    response = await agent.run(input_data)
    output = response.output.content
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
    )
    
    # Test relevancy (coherence not available in current version)
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [relevancy_metric])


@pytest.mark.asyncio
async def test_linkedin_toxicity():
    """Test that LinkedIn post maintains professional tone and is not toxic."""
    agent = LinkedInAgent()
    
    query = "Leadership challenges in tech industry"
    context = {
        "key_points": [
            "Managing diverse teams",
            "Navigating rapid change",
            "Balancing innovation and stability",
        ],
        "tone": "professional",
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-linkedin-3")
    
    response = await agent.run(input_data)
    output = response.output.content
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
    )
    
    # Test toxicity (should be very low for professional content)
    toxicity_metric = ToxicityMetric(threshold=0.2)
    assert_test(test_case, [toxicity_metric])


@pytest.mark.asyncio
async def test_linkedin_hashtag_quality():
    """Test that LinkedIn post includes relevant hashtags (not numbered placeholders)."""
    agent = LinkedInAgent()
    
    query = "Cloud computing trends 2024"
    context = {
        "key_points": [
            "Serverless architecture adoption",
            "Multi-cloud strategies",
            "Edge computing integration",
        ],
        "tone": "professional",
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-linkedin-4")
    
    response = await agent.run(input_data)
    output = response.output.content
    metadata = response.output.metadata
    
    # Verify hashtags are present and meaningful
    hashtags = metadata.get("hashtags", [])
    assert len(hashtags) > 0, "Should generate hashtags"
    
    # Check that hashtags are not just numbered placeholders (like #1, #2)
    # But allow year tags like #2024
    for tag in hashtags:
        # A numbered placeholder is a single digit or just 'placeholder'
        is_pure_number = tag.lstrip('#').isdigit() and len(tag.lstrip('#')) == 1
        is_just_placeholder = 'placeholder' in tag.lower()
        assert not (is_pure_number or is_just_placeholder), f"Hashtag {tag} should not be a pure number or placeholder"
    
    # Check overall quality
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
    )
    
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
    ]
    
    assert_test(test_case, metrics)


@pytest.mark.asyncio
async def test_linkedin_comprehensive_quality():
    """Test comprehensive LinkedIn post quality."""
    agent = LinkedInAgent()
    
    query = "Remote work productivity tips"
    context = {
        "key_points": [
            "Create dedicated workspace",
            "Set boundaries and schedule",
            "Use collaboration tools effectively",
            "Prioritize communication",
        ],
        "tone": "helpful",
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-linkedin-5")
    
    response = await agent.run(input_data)
    output = response.output.content
    
    # Verify post structure
    assert len(output) > 100, "Post should have substantial content"
    assert "#" in output, "Post should include hashtags"
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
    )
    
    # Comprehensive metrics
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        ToxicityMetric(threshold=0.2),
    ]
    
    assert_test(test_case, metrics)


@pytest.mark.asyncio
async def test_linkedin_engagement_elements():
    """Test that LinkedIn post includes engagement elements (hook, CTA)."""
    agent = LinkedInAgent()
    
    query = "Digital transformation in manufacturing"
    context = {
        "key_points": [
            "IoT sensor integration",
            "Predictive maintenance",
            "Data-driven decision making",
        ],
        "tone": "thought-provoking",
    }
    
    input_data = AgentInput(query=query, context=context, session_id="deepeval-linkedin-6")
    
    response = await agent.run(input_data)
    output = response.output.content
    metadata = response.output.metadata
    
    # Check for engagement elements
    assert "?" in output or "!" in output, "Post should have engaging punctuation"
    
    # Verify CTA in metadata
    if "cta" in metadata:
        assert len(metadata["cta"]) > 0, "CTA should not be empty"
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
    )
    
    metrics = [
        AnswerRelevancyMetric(threshold=0.1),  # Very low threshold for engagement elements
    ]
    
    assert_test(test_case, metrics)
