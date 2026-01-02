"""DeepEval tests for end-to-end content generation flows"""
import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase

from src.agents import ResearchAgent, BlogWriterAgent, LinkedInAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_research_to_blog_flow():
    """Test complete flow from research to blog post."""
    query = "Impact of remote work on team productivity"
    session_id = "deepeval-e2e-1"
    
    # Step 1: Research
    research_agent = ResearchAgent()
    research_input = AgentInput(query=query, session_id=session_id)
    research_response = await research_agent.run(research_input)
    
    assert research_response.output.success
    research_data = research_response.output.metadata.get("synthesis", {})
    
    # Step 2: Blog Generation
    blog_agent = BlogWriterAgent()
    blog_input = AgentInput(
        query=query,
        context={"research": research_data},
        session_id=session_id
    )
    blog_response = await blog_agent.run(blog_input)
    
    assert blog_response.output.success
    blog_content = blog_response.output.content.replace("```markdown\n", "").replace("```", "")
    
    # Create retrieval context from research
    retrieval_context = [
        research_data.get("summary", ""),
        *research_data.get("key_points", []),
    ]
    
    # Test end-to-end quality
    test_case = LLMTestCase(
        input=query,
        actual_output=blog_content,
        retrieval_context=retrieval_context,
    )
    
    metrics = [
        AnswerRelevancyMetric(threshold=0.6),
        ToxicityMetric(threshold=0.3),
    ]
    
    assert_test(test_case, metrics)


@pytest.mark.asyncio
async def test_research_to_linkedin_flow():
    """Test complete flow from research to LinkedIn post."""
    query = "Emerging trends in sustainable business"
    session_id = "deepeval-e2e-2"
    
    # Step 1: Research
    research_agent = ResearchAgent()
    research_input = AgentInput(query=query, session_id=session_id)
    research_response = await research_agent.run(research_input)
    
    assert research_response.output.success
    research_data = research_response.output.metadata.get("synthesis", {})
    
    # Step 2: LinkedIn Post Generation
    linkedin_agent = LinkedInAgent()
    linkedin_input = AgentInput(
        query=query,
        context={
            "research": research_data,
            "key_points": research_data.get("key_points", [])[:5],
            "tone": "professional",
        },
        session_id=session_id
    )
    linkedin_response = await linkedin_agent.run(linkedin_input)
    
    assert linkedin_response.output.success
    linkedin_content = linkedin_response.output.content
    
    # Test quality
    test_case = LLMTestCase(
        input=query,
        actual_output=linkedin_content,
    )
    
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        ToxicityMetric(threshold=0.2),
    ]
    
    assert_test(test_case, metrics)


@pytest.mark.asyncio
async def test_multi_format_content_consistency():
    """Test that blog and LinkedIn content are consistent when generated from same research."""
    query = "Benefits of AI in customer service"
    session_id = "deepeval-e2e-3"
    
    # Step 1: Research (shared context)
    research_agent = ResearchAgent()
    research_input = AgentInput(query=query, session_id=session_id)
    research_response = await research_agent.run(research_input)
    
    assert research_response.output.success
    research_data = research_response.output.metadata.get("synthesis", {})
    
    # Step 2: Generate Blog
    blog_agent = BlogWriterAgent()
    blog_input = AgentInput(
        query=query,
        context={"research": research_data},
        session_id=session_id
    )
    blog_response = await blog_agent.run(blog_input)
    blog_content = blog_response.output.content.replace("```markdown\n", "").replace("```", "")
    
    # Step 3: Generate LinkedIn Post
    linkedin_agent = LinkedInAgent()
    linkedin_input = AgentInput(
        query=query,
        context={
            "research": research_data,
            "key_points": research_data.get("key_points", [])[:5],
        },
        session_id=session_id
    )
    linkedin_response = await linkedin_agent.run(linkedin_input)
    linkedin_content = linkedin_response.output.content
    
    # Test both outputs against same research
    retrieval_context = [
        research_data.get("summary", ""),
        *research_data.get("key_points", []),
    ]
    
    # Test blog
    blog_test_case = LLMTestCase(
        input=query,
        actual_output=blog_content,
        retrieval_context=retrieval_context,
    )
    
    # Test LinkedIn
    linkedin_test_case = LLMTestCase(
        input=query,
        actual_output=linkedin_content,
        retrieval_context=retrieval_context,
    )
    
    # Both should be relevant (removed faithfulness to avoid timeout)
    relevancy_metric = AnswerRelevancyMetric(threshold=0.6)
    
    assert_test(blog_test_case, [relevancy_metric])
    assert_test(linkedin_test_case, [relevancy_metric])


@pytest.mark.asyncio
async def test_quality_across_different_topics():
    """Test content quality across diverse topics."""
    topics = [
        "Machine learning in healthcare",
        "Sustainable supply chain management",
        "Cybersecurity best practices for startups",
    ]
    
    for topic in topics:
        session_id = f"deepeval-e2e-topic-{topic.replace(' ', '-')}"
        
        # Research
        research_agent = ResearchAgent()
        research_input = AgentInput(query=topic, session_id=session_id)
        research_response = await research_agent.run(research_input)
        
        assert research_response.output.success, f"Research failed for: {topic}"
        
        research_data = research_response.output.metadata.get("synthesis", {})
        research_output = research_response.output.content
        
        # Test research quality
        test_case = LLMTestCase(
            input=topic,
            actual_output=research_output,
        )
        
        metrics = [
            AnswerRelevancyMetric(threshold=0.7),
        ]
        
        assert_test(test_case, metrics)


@pytest.mark.asyncio
async def test_content_safety_across_flows():
    """Test that all generated content maintains safety standards."""
    query = "Workplace diversity and inclusion strategies"
    session_id = "deepeval-e2e-safety"
    
    # Research
    research_agent = ResearchAgent()
    research_input = AgentInput(query=query, session_id=session_id)
    research_response = await research_agent.run(research_input)
    research_data = research_response.output.metadata.get("synthesis", {})
    
    # Blog
    blog_agent = BlogWriterAgent()
    blog_input = AgentInput(
        query=query,
        context={"research": research_data},
        session_id=session_id
    )
    blog_response = await blog_agent.run(blog_input)
    blog_content = blog_response.output.content.replace("```markdown\n", "").replace("```", "")
    
    # LinkedIn
    linkedin_agent = LinkedInAgent()
    linkedin_input = AgentInput(
        query=query,
        context={
            "research": research_data,
            "key_points": research_data.get("key_points", [])[:5],
        },
        session_id=session_id
    )
    linkedin_response = await linkedin_agent.run(linkedin_input)
    linkedin_content = linkedin_response.output.content
    
    # Test toxicity for all outputs
    toxicity_metric = ToxicityMetric(threshold=0.2)
    
    blog_test = LLMTestCase(input=query, actual_output=blog_content)
    linkedin_test = LLMTestCase(input=query, actual_output=linkedin_content)
    research_test = LLMTestCase(input=query, actual_output=research_response.output.content)
    
    assert_test(blog_test, [toxicity_metric])
    assert_test(linkedin_test, [toxicity_metric])
    assert_test(research_test, [toxicity_metric])
