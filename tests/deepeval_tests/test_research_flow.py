"""DeepEval tests for Research Agent flow"""
import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
)
from deepeval.test_case import LLMTestCase

from src.agents import ResearchAgent
from src.agents.base_agent import AgentInput


@pytest.mark.asyncio
async def test_research_relevancy():
    """Test that research output is relevant to the query."""
    agent = ResearchAgent()
    
    query = "What are the latest trends in artificial intelligence for 2024?"
    input_data = AgentInput(query=query, session_id="deepeval-research-1")
    
    response = await agent.run(input_data)
    
    # Extract research content and sources
    output = response.output.content
    sources = response.output.metadata.get("sources", [])
    
    # Create retrieval context from sources
    retrieval_context = [
        f"{src.get('title', '')}: {src.get('snippet', '')}"
        for src in sources
    ]
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
        retrieval_context=retrieval_context,
    )
    
    # Test relevancy
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [relevancy_metric])


@pytest.mark.asyncio
async def test_research_faithfulness():
    """Test that research output is faithful to retrieved sources."""
    agent = ResearchAgent()
    
    query = "Benefits of cloud computing in healthcare"
    input_data = AgentInput(query=query, session_id="deepeval-research-2")
    
    response = await agent.run(input_data)
    
    output = response.output.content
    sources = response.output.metadata.get("sources", [])
    
    retrieval_context = [
        f"{src.get('title', '')}: {src.get('snippet', '')}"
        for src in sources
    ]
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
        retrieval_context=retrieval_context,
    )
    
    # Test faithfulness - output should be grounded in sources
    faithfulness_metric = FaithfulnessMetric(threshold=0.7)
    assert_test(test_case, [faithfulness_metric])


@pytest.mark.asyncio
async def test_research_contextual_relevancy():
    """Test that retrieved sources are contextually relevant."""
    agent = ResearchAgent()
    
    query = "Machine learning applications in finance"
    input_data = AgentInput(query=query, session_id="deepeval-research-3")
    
    response = await agent.run(input_data)
    
    output = response.output.content
    sources = response.output.metadata.get("sources", [])
    
    retrieval_context = [
        f"{src.get('title', '')}: {src.get('snippet', '')}"
        for src in sources
    ]
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
        retrieval_context=retrieval_context,
        expected_output="Research should cover ML applications specifically in finance sector"
    )
    
    # Test contextual relevancy of retrieved sources
    contextual_metric = ContextualRelevancyMetric(threshold=0.7)
    assert_test(test_case, [contextual_metric])


@pytest.mark.asyncio
async def test_research_synthesis_quality():
    """Test overall quality of research synthesis."""
    agent = ResearchAgent()
    
    query = "Impact of quantum computing on cybersecurity"
    input_data = AgentInput(query=query, session_id="deepeval-research-4")
    
    response = await agent.run(input_data)
    
    output = response.output.content
    sources = response.output.metadata.get("sources", [])
    synthesis = response.output.metadata.get("synthesis", {})
    
    # Verify synthesis structure
    assert "summary" in synthesis
    assert "key_points" in synthesis
    assert len(synthesis["key_points"]) > 0
    
    retrieval_context = [
        f"{src.get('title', '')}: {src.get('snippet', '')}"
        for src in sources
    ]
    
    test_case = LLMTestCase(
        input=query,
        actual_output=output,
        retrieval_context=retrieval_context,
    )
    
    # Combined metrics for comprehensive evaluation
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
    ]
    
    assert_test(test_case, metrics)
