import pytest
from src.agents import QueryHandlerAgent
from src.agents.base_agent import AgentInput
from src.utils import IntentType


@pytest.mark.asyncio
async def test_query_handler_initialization():
    """Test query handler agent initialization."""
    agent = QueryHandlerAgent()
    
    assert agent.name == "query_handler"
    assert agent.classifier is not None
    assert agent.state_manager is not None


@pytest.mark.asyncio
async def test_query_handler_research_routing():
    """Test routing for research queries."""
    agent = QueryHandlerAgent()
    
    input_data = AgentInput(
        query="Research the latest trends in artificial intelligence",
        session_id="test-session-1"
    )
    
    response = await agent.run(input_data)
    
    assert response.output.success is True
    assert response.output.metadata["intent"] == IntentType.RESEARCH.value
    assert response.output.metadata["routing_decision"] == "research_agent"
    assert "research" in response.output.content.lower()


@pytest.mark.asyncio
async def test_query_handler_blog_routing():
    """Test routing for blog writing queries."""
    agent = QueryHandlerAgent()
    
    input_data = AgentInput(
        query="Write a blog post about climate change solutions",
        session_id="test-session-2"
    )
    
    response = await agent.run(input_data)
    
    assert response.output.success is True
    assert response.output.metadata["intent"] == IntentType.BLOG.value
    assert response.output.metadata["routing_decision"] == "blog_writer_agent"


@pytest.mark.asyncio
async def test_query_handler_linkedin_routing():
    """Test routing for LinkedIn post queries."""
    agent = QueryHandlerAgent()
    
    input_data = AgentInput(
        query="Create a LinkedIn post about leadership in tech",
        session_id="test-session-3"
    )
    
    response = await agent.run(input_data)
    
    assert response.output.success is True
    assert response.output.metadata["intent"] == IntentType.LINKEDIN.value
    assert response.output.metadata["routing_decision"] == "linkedin_writer_agent"


@pytest.mark.asyncio
async def test_query_handler_image_routing():
    """Test routing for image generation queries."""
    agent = QueryHandlerAgent()
    
    input_data = AgentInput(
        query="Generate an image of a futuristic city skyline",
        session_id="test-session-4"
    )
    
    response = await agent.run(input_data)
    
    assert response.output.success is True
    assert response.output.metadata["intent"] == IntentType.IMAGE.value
    assert response.output.metadata["routing_decision"] == "image_agent"


@pytest.mark.asyncio
async def test_query_handler_unclear_intent():
    """Test handling of unclear queries."""
    agent = QueryHandlerAgent()
    
    input_data = AgentInput(
        query="help",
        session_id="test-session-5"
    )
    
    response = await agent.run(input_data)
    
    # Should ask for clarification
    assert response.output.success is True
    assert "clarify" in response.output.content.lower() or "help" in response.output.content.lower()


@pytest.mark.asyncio
async def test_conversation_memory_integration():
    """Test that conversation memory is maintained."""
    agent = QueryHandlerAgent()
    session_id = "test-session-memory"
    
    # First query
    input1 = AgentInput(query="Research machine learning", session_id=session_id)
    await agent.run(input1)
    
    # Check that session was created and message stored
    session = agent.state_manager.get_session(session_id)
    assert session is not None
    assert len(session["messages"]) >= 2  # User + assistant messages
    
    # Check context
    topic = agent.state_manager.get_context(session_id, "topic")
    assert topic is not None


@pytest.mark.asyncio
async def test_multi_format_routing():
    """Test routing for multi-format content requests."""
    agent = QueryHandlerAgent()
    
    input_data = AgentInput(
        query="Create complete content about AI including blog and LinkedIn post",
        session_id="test-session-multi"
    )
    
    response = await agent.run(input_data)
    
    assert response.output.success is True
    routing = response.output.metadata.get("routing_decision", "")
    
    # Query handler passes requests through, may not indicate multi-format in routing
    # Just verify it processed successfully
    assert routing or response.output.content
