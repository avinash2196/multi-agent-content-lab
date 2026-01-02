import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    """Base input schema for all agents."""
    query: str = Field(..., description="The user query or request")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context from previous agents")
    session_id: Optional[str] = Field(default=None, description="Session identifier for conversation tracking")


class AgentOutput(BaseModel):
    """Base output schema for all agents."""
    content: str = Field(..., description="The generated content or response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the response")
    success: bool = Field(default=True, description="Whether the operation succeeded")
    error: Optional[str] = Field(default=None, description="Error message if operation failed")


@dataclass
class AgentResponse:
    """Response wrapper for agent execution."""
    output: AgentOutput
    agent_name: str
    execution_time: float


class BaseAgent(ABC):
    """Base class for all agents in the ContentAlchemy system."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up agent-specific logger."""
        logger = logging.getLogger(f"agent.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input data against schema."""
        try:
            if not input_data.query or not input_data.query.strip():
                raise ValueError("Query cannot be empty")
            return True
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            raise
    
    def validate_output(self, output_data: AgentOutput) -> bool:
        """Validate output data against schema."""
        try:
            if not output_data.success and not output_data.error:
                raise ValueError("Failed operations must include an error message")
            return True
        except Exception as e:
            self.logger.error(f"Output validation failed: {e}")
            raise
    
    @abstractmethod
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent's main logic. Must be implemented by subclasses."""
        pass
    
    async def run(self, input_data: AgentInput) -> AgentResponse:
        """Run the agent with input validation, execution, and error handling."""
        import time
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting execution for query: {input_data.query[:50]}...")
            
            # Validate input
            self.validate_input(input_data)
            
            # Execute agent logic
            output = await self.execute(input_data)
            
            # Validate output
            self.validate_output(output)
            
            execution_time = time.time() - start_time
            self.logger.info(f"Execution completed in {execution_time:.2f}s")
            
            return AgentResponse(
                output=output,
                agent_name=self.name,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Execution failed: {e}")
            
            return AgentResponse(
                output=AgentOutput(
                    content="",
                    success=False,
                    error=str(e),
                    metadata={"error_type": type(e).__name__}
                ),
                agent_name=self.name,
                execution_time=execution_time
            )
