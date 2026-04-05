import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    """Input schema shared by all agents.

    Every agent in the pipeline receives a standardised input so that the
    orchestration layer (agent_graph.py) can pass state between nodes without
    knowing the internals of each agent.

    Design note:
        Using Pydantic for input/output gives us free validation and clear
        documentation. An alternative would be plain dataclasses, but Pydantic
        makes it easier to serialise/deserialise state as the graph grows.

    Attributes:
        query: The user's original request, or the sub-task delegated by the
            query handler.
        context: Optional dict carrying data produced by upstream agents
            (e.g., research results passed to the blog writer).
        session_id: Stable identifier for a single user session, used by the
            StateManager to maintain conversation history.
    """

    query: str = Field(..., description="The user query or request")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context from previous agents"
    )
    session_id: Optional[str] = Field(
        default=None, description="Session identifier for conversation tracking"
    )


class AgentOutput(BaseModel):
    """Output schema shared by all agents.

    Structured output allows the orchestration layer to read results
    consistently regardless of which agent produced them, and makes it
    straightforward to surface errors without raising exceptions across
    graph boundaries.

    Attributes:
        content: The primary result — article text, post text, image URLs, etc.
        metadata: Provider-specific extras: quality scores, slugs, hashtag
            lists, image dimensions, etc.
        success: False when the agent caught a handled error; the graph can
            check this to decide whether to proceed or surface a warning.
        error: Human-readable description of the failure when success is False.
    """

    content: str = Field(..., description="The generated content or response")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the response"
    )
    success: bool = Field(default=True, description="Whether the operation succeeded")
    error: Optional[str] = Field(
        default=None, description="Error message if operation failed"
    )


@dataclass
class AgentResponse:
    """Wrapper returned by BaseAgent.run() that bundles output with execution metadata.

    Separating this from AgentOutput keeps the domain object (AgentOutput)
    clean of infrastructure concerns like timing.
    """

    output: AgentOutput
    agent_name: str
    execution_time: float


class BaseAgent(ABC):
    """Abstract base class that every agent in the pipeline must extend.

    Responsibilities:
        - Enforce a consistent interface (execute / run / validate).
        - Provide shared infrastructure: structured logging, input/output
          validation, and timing.

    How it fits into the system:
        AgentGraph instantiates concrete subclasses (ResearchAgent,
        BlogWriterAgent, etc.) and calls their ``run()`` method inside each
        LangGraph node function.  The graph does not interact with ``execute()``
        directly — that is the agent's internal implementation detail.

    Design trade-off:
        We use ABC + abstractmethod rather than a Protocol so that shared
        behaviour (logging setup, run wrapper) lives in one place.  A Protocol
        would be cleaner for dependency injection in tests, but is harder to
        enforce.

    Learning note:
        This is the **Template Method** design pattern: BaseAgent defines the
        algorithm skeleton (validate → execute → record timing) and delegates
        the domain-specific step (``execute``) to subclasses.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Create a named logger scoped to this agent instance.

        Using a per-agent logger name (``agent.<name>``) means log output can
        be filtered by agent in production tooling without code changes.
        """
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
        """Reject clearly invalid inputs before wasting an API call.

        This is intentionally minimal — Pydantic already enforces types.
        We only add the one check (non-empty query) that Pydantic cannot
        express as a field constraint in this simplified form.
        """
        try:
            if not input_data.query or not input_data.query.strip():
                raise ValueError("Query cannot be empty")
            return True
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            raise

    def validate_output(self, output_data: AgentOutput) -> bool:
        """Ensure failed outputs include a useful error message.

        Without this check a caller cannot tell whether an empty ``content``
        string represents success or a silent failure.
        """
        try:
            if not output_data.success and not output_data.error:
                raise ValueError("Failed operations must include an error message")
            return True
        except Exception as e:
            self.logger.error(f"Output validation failed: {e}")
            raise

    @abstractmethod
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """Perform the agent's domain-specific work.

        Subclasses implement all LLM calls, service calls, and business logic
        here.  The ``run()`` wrapper handles timing and validation so
        ``execute()`` can focus on the task.
        """
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
