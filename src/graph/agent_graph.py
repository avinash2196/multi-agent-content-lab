from typing import TypedDict, Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from src.agents.base_agent import AgentInput

from config import settings


class AgentState(TypedDict):
    """State object passed between agents in the graph."""
    messages: List[Dict[str, str]]
    current_query: str
    session_id: str
    context: Dict[str, Any]
    routing_decision: Optional[str]
    research_results: Optional[Dict[str, Any]]
    blog_content: Optional[str]
    linkedin_content: Optional[str]
    image_urls: Optional[List[str]]
    final_output: Optional[Dict[str, Any]]
    errors: List[str]


@dataclass
class AgentGraph:
    """LangGraph-based multi-agent orchestration system."""
    
    def __init__(self):
        self.logger = logging.getLogger("agent_graph")
        self.graph = None
        # Import agents here to avoid circular imports
        from src.agents import (
            QueryHandlerAgent,
            ResearchAgent,
            BlogWriterAgent,
            LinkedInAgent,
            ImageAgent,
            StrategistAgent,
        )
        # Instantiate agents
        self.query_handler = QueryHandlerAgent()
        self.research_agent = ResearchAgent()
        self.blog_agent = BlogWriterAgent()
        self.linkedin_agent = LinkedInAgent()
        self.image_agent = ImageAgent()
        self.strategist_agent = StrategistAgent()
        self._setup_graph()
    
    def _setup_graph(self):
        """Initialize the LangGraph structure."""
        try:
            from langgraph.graph import StateGraph
            
            # Create state graph
            workflow = StateGraph(AgentState)
            
            workflow.add_node("query_handler", self._query_handler_node)
            workflow.add_node("research", self._research_node)
            workflow.add_node("blog_writer", self._blog_writer_node)
            workflow.add_node("linkedin_writer", self._linkedin_writer_node)
            workflow.add_node("image_generator", self._image_generator_node)
            workflow.add_node("strategist", self._strategist_node)

            workflow.set_entry_point("query_handler")
            workflow.add_conditional_edges("query_handler", self._route_from_query, {
                "research_agent": "research",
                "blog_writer_agent": "research",
                "linkedin_writer_agent": "research",
                "image_agent": "image_generator",
                "strategist_agent": "strategist",
                "multi": "research",
                "default": "strategist",
            })

            workflow.add_edge("research", "image_generator")
            workflow.add_edge("image_generator", "blog_writer")
            workflow.add_edge("blog_writer", "linkedin_writer")
            workflow.add_edge("linkedin_writer", "strategist")
            
            self.graph = workflow
            self.logger.info("Agent graph initialized")
            
        except ImportError as e:
            self.logger.error(f"Failed to import langgraph: {e}")
            raise
    
    def add_agent_node(self, name: str, agent_func):
        """Add an agent node to the graph."""
        if self.graph:
            self.graph.add_node(name, agent_func)
            self.logger.info(f"Added agent node: {name}")
    
    def add_edge(self, from_node: str, to_node: str):
        """Add an edge between two nodes."""
        if self.graph:
            self.graph.add_edge(from_node, to_node)
            self.logger.info(f"Added edge: {from_node} -> {to_node}")
    
    def add_conditional_edge(self, from_node: str, condition_func, edge_mapping: Dict[str, str]):
        """Add a conditional edge based on state."""
        if self.graph:
            self.graph.add_conditional_edges(from_node, condition_func, edge_mapping)
            self.logger.info(f"Added conditional edge from {from_node}")
    
    def compile(self):
        """Compile the graph for execution."""
        if self.graph:
            compiled = self.graph.compile()
            self.logger.info("Graph compiled successfully")
            return compiled
        raise ValueError("Graph not initialized")
    
    async def execute(self, initial_state: AgentState):
        """Execute the agent graph with initial state."""
        compiled_graph = self.compile()
        result = await compiled_graph.ainvoke(initial_state)
        return result

    async def _query_handler_node(self, state: AgentState) -> AgentState:
        input_data = AgentInput(
            query=state.get("current_query", ""),
            context=state.get("context", {}),
            session_id=state.get("session_id"),
        )
        resp = await self.query_handler.run(input_data)

        state["routing_decision"] = resp.output.metadata.get("routing_decision") if resp.output else None
        state["messages"].append({"role": "assistant", "content": resp.output.content})
        state["context"]["classification"] = resp.output.metadata

        return state

    async def _research_node(self, state: AgentState) -> AgentState:
        input_data = AgentInput(
            query=state.get("current_query", ""),
            context=state.get("context", {}),
            session_id=state.get("session_id"),
        )
        resp = await self.research_agent.run(input_data)
        state["research_results"] = resp.output.metadata.get("synthesis") if resp.output else {}
        state["context"]["research"] = resp.output.metadata.get("synthesis") if resp.output else {}
        state["context"]["sources"] = resp.output.metadata.get("sources") if resp.output else []
        state["messages"].append({"role": "assistant", "content": resp.output.content})
        return state

    async def _blog_writer_node(self, state: AgentState) -> AgentState:
        self.logger.info("Running blog_writer_node")
        input_data = AgentInput(
            query=state.get("current_query", ""),
            context={
                **state.get("context", {}),
                "research": state.get("research_results", {}),
                "images": state.get("image_urls", []),
            },
            session_id=state.get("session_id"),
        )
        resp = await self.blog_agent.run(input_data)
        state["blog_content"] = resp.output.content if resp.output else None
        state["context"]["blog"] = resp.output.content if resp.output else None
        if resp.output and resp.output.content:
            state["messages"].append({"role": "assistant", "content": resp.output.content})
            self.logger.info(f"Blog content generated: {len(resp.output.content)} chars")
        else:
            self.logger.warning("Blog agent returned no content")
        return state

    async def _linkedin_writer_node(self, state: AgentState) -> AgentState:
        self.logger.info("Running linkedin_writer_node")
        input_data = AgentInput(
            query=state.get("current_query", ""),
            context={
                **state.get("context", {}),
                "key_points": (state.get("research_results", {}) or {}).get("key_points", []),
                "images": state.get("image_urls", []),
            },
            session_id=state.get("session_id"),
        )
        resp = await self.linkedin_agent.run(input_data)
        state["linkedin_content"] = resp.output.content if resp.output else None
        state["context"]["linkedin"] = resp.output.content if resp.output else None
        if resp.output and resp.output.content:
            state["messages"].append({"role": "assistant", "content": resp.output.content})
            self.logger.info(f"LinkedIn content generated: {len(resp.output.content)} chars")
        else:
            self.logger.warning("LinkedIn agent returned no content")
        return state

    async def _image_generator_node(self, state: AgentState) -> AgentState:
        # Check if images should be generated
        ctx = state.get("context", {})
        should_generate_images = ctx.get("generate_images", False)
        linkedin_with_images = ctx.get("linkedin_with_images", False)
        
        # Auto-enable image and LinkedIn generation if linkedin_with_images is True
        if linkedin_with_images:
            if not should_generate_images:
                should_generate_images = True
                ctx["generate_images"] = True
            # Also ensure LinkedIn is enabled when requesting images in LinkedIn post
            if not ctx.get("generate_linkedin", False):
                ctx["generate_linkedin"] = True
        
        # Skip image generation if explicitly disabled and not needed for LinkedIn
        if not should_generate_images:
            return state

        if not settings.openai_api_key:
            if linkedin_with_images:
                state.setdefault("errors", []).append("image_generation_skipped_no_openai_key")
            return state

        # Respect alt-text toggle
        generate_alt = ctx.get("generate_alt_text", False)
        if generate_alt and not getattr(self.image_agent, "use_alt_text", False):
            self.image_agent.use_alt_text = True
            if getattr(self.image_agent, "llm_gateway", None) is None:
                try:
                    from src.services.llm_gateway import LLMGateway

                    self.image_agent.llm_gateway = LLMGateway.from_settings(observability=self.image_agent.observability)
                except Exception as e:  # noqa: BLE001
                    self.image_agent.logger.warning(f"Alt text gateway unavailable: {e}")

        input_data = AgentInput(
            query=state.get("current_query", ""),
            context={
                **state.get("context", {}),
                "research": state.get("research_results", {}),
            },
            session_id=state.get("session_id"),
        )
        resp = await self.image_agent.run(input_data)
        if resp.output.success:
            urls = resp.output.metadata.get("urls", [])
            state["image_urls"] = urls
            state["context"]["images"] = urls
        else:
            state.setdefault("errors", []).append(resp.output.error or "image_generation_failed")
        state["messages"].append({"role": "assistant", "content": resp.output.content})
        return state

    async def _strategist_node(self, state: AgentState) -> AgentState:
        input_data = AgentInput(
            query=state.get("current_query", ""),
            context={
                **state.get("context", {}),
                "research": state.get("research_results", {}),
                "blog": state.get("blog_content", ""),
                "linkedin": state.get("linkedin_content", ""),
                "images": state.get("image_urls", []),
            },
            session_id=state.get("session_id"),
        )
        resp = await self.strategist_agent.run(input_data)
        state["final_output"] = {
            "summary": resp.output.content,
            "metadata": resp.output.metadata,
        }
        state["messages"].append({"role": "assistant", "content": resp.output.content})
        return state

    def _route_from_query(self, state: AgentState) -> str:
        routing = (state.get("routing_decision") or "").strip()
        if not routing:
            return "default"
        if "," in routing:
            return "multi"
        return routing
