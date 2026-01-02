import pytest
from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        return AgentOutput(
            content=f"Processed: {input_data.query}",
            metadata={"test": True},
            success=True
        )


@pytest.mark.asyncio
async def test_base_agent_execution():
    """Test basic agent execution."""
    agent = MockAgent(name="test_agent")
    
    input_data = AgentInput(query="Test query", session_id="test-123")
    response = await agent.run(input_data)
    
    assert response.agent_name == "test_agent"
    assert response.output.success is True
    assert "Processed: Test query" in response.output.content
    assert response.execution_time >= 0


@pytest.mark.asyncio
async def test_base_agent_validation():
    """Test input validation."""
    agent = MockAgent(name="test_agent")
    
    # Empty query should fail
    input_data = AgentInput(query="", session_id="test-123")
    response = await agent.run(input_data)
    
    assert response.output.success is False
    assert response.output.error is not None
