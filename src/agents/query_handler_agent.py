from typing import Dict, Any, Optional, List
import logging

from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from src.utils import IntentClassifier, IntentType, PromptManager, ResponseParser
from src.utils.observability import Observability
from src.graph.state_manager import StateManager
from src.services.llm_gateway import LLMGateway


class QueryHandlerAgent(BaseAgent):
    """Agent responsible for routing user queries to appropriate agents."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_gateway: Optional[LLMGateway] = None):
        super().__init__(name="query_handler", config=config)
        self.classifier = IntentClassifier()
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
        self.state_manager = StateManager()
        self.observability = Observability()
        self.llm_gateway = llm_gateway or self._build_llm_gateway()
        
        self.logger.info("Query Handler Agent initialized")
    
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute query handling and routing logic."""
        try:
            query = input_data.query
            context = input_data.context or {}
            session_id = input_data.session_id or "default"
            
            # Add message to conversation history
            self.state_manager.add_message(session_id, "user", query)
            
            # Get conversation history for context
            history = self.state_manager.get_conversation_history(session_id, max_messages=5)
            
            # Classify intent using LLM
            classification = await self._classify_with_llm(query, history, context)
            self.observability.record_event("query_handler.classified", {"intent": classification.intent.value})
            
            # Store classification in session context
            self.state_manager.set_context(session_id, "last_intent", classification.intent.value)
            self.state_manager.set_context(session_id, "topic", classification.topic)
            
            # Determine routing decision
            routing_decision = self._determine_routing(classification)
            
            # Create response content
            response_content = self._create_response(classification, routing_decision)
            
            # Add assistant response to history
            self.state_manager.add_message(session_id, "assistant", response_content)
            
            return AgentOutput(
                content=response_content,
                success=True,
                metadata={
                    "intent": classification.intent.value,
                    "topic": classification.topic,
                    "confidence": classification.confidence,
                    "routing_decision": routing_decision,
                    "requirements": classification.requirements,
                    "keywords": classification.keywords,
                    "session_id": session_id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in query handler: {e}")
            return AgentOutput(
                content="I apologize, but I had trouble understanding your request. Could you please rephrase?",
                success=False,
                error=str(e),
                metadata={"error_type": type(e).__name__}
            )
    
    async def _classify_with_llm(
        self, 
        query: str, 
        history: List[Dict[str, str]], 
        context: Dict[str, Any]
    ) -> 'ClassificationResult':
        """Use LLM to classify the query with conversation context."""
        try:
            # Build context string from history
            history_str = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in history[-3:]  # Last 3 messages
            ]) if history else "No previous context"
            
            # Format classification prompt
            prompt = self.prompt_manager.format_prompt(
                "query_classification",
                query=query,
                context=history_str
            )
            
            if not self.llm_gateway:
                raise RuntimeError("llm_gateway_unavailable")

            with self.observability.span("query_handler.llm_classify", {"model": self.config.get("model", "gpt-4") }):
                response_text = await self.llm_gateway.chat(
                    messages=[
                        {"role": "system", "content": "You are a query classification expert. Analyze queries and return structured JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.config.get("model", "gpt-4"),
                    temperature=0.3,
                    max_tokens=500,
                )

            parsed_json = self.response_parser.parse_json_response(response_text)
            
            if parsed_json:
                # Map to IntentType
                intent_str = parsed_json.get("intent", "unclear")
                try:
                    intent = IntentType(intent_str)
                except ValueError:
                    intent = IntentType.UNCLEAR
                
                from src.utils.intent_classifier import ClassificationResult
                return ClassificationResult(
                    intent=intent,
                    topic=parsed_json.get("topic", query),
                    confidence=0.8,  # High confidence from LLM
                    requirements=parsed_json.get("requirements", []),
                    keywords=parsed_json.get("keywords", []),
                    metadata={"source": "llm", "model": self.config.get("model", "gpt-4")}
                )
            
        except Exception as e:
            self.logger.warning(f"LLM classification failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based classification
        return self.classifier.classify(query, context)

    def _build_llm_gateway(self) -> Optional[LLMGateway]:
        try:
            gateway = LLMGateway.from_settings(observability=self.observability)
            return gateway
        except Exception as e:
            self.logger.warning(f"LLM gateway not available: {e}")
            return None
    
    def _determine_routing(self, classification: 'ClassificationResult') -> str:
        """Determine which agent(s) to route to based on classification."""
        intent = classification.intent
        
        routing_map = {
            IntentType.RESEARCH: "research_agent",
            IntentType.BLOG: "blog_writer_agent",
            IntentType.LINKEDIN: "linkedin_writer_agent",
            IntentType.IMAGE: "image_agent",
            IntentType.STRATEGY: "strategist_agent",
            IntentType.MULTI_FORMAT: "research_agent,blog_writer_agent,linkedin_writer_agent,image_agent",
            IntentType.UNCLEAR: "query_handler"  # Ask for clarification
        }
        
        routing = routing_map.get(intent, "query_handler")
        self.logger.info(f"Routing to: {routing}")
        return routing
    
    def _create_response(self, classification: 'ClassificationResult', routing: str) -> str:
        """Create a response message for the user."""
        intent = classification.intent
        topic = classification.topic
        
        if intent == IntentType.UNCLEAR:
            return (
                f"I'd be happy to help! To provide the best assistance, could you clarify "
                f"what you'd like me to do? I can:\n"
                f"- Research topics and gather information\n"
                f"- Write SEO-optimized blog posts\n"
                f"- Create LinkedIn posts\n"
                f"- Generate images\n"
                f"- Help strategize and improve content"
            )
        
        response_templates = {
            IntentType.RESEARCH: f"I'll research '{topic}' for you. Gathering comprehensive information from multiple sources...",
            IntentType.BLOG: f"I'll create a blog post about '{topic}'. Starting with research and outline generation...",
            IntentType.LINKEDIN: f"I'll craft a professional LinkedIn post about '{topic}'. Creating engaging content...",
            IntentType.IMAGE: f"I'll generate an image for '{topic}'. Optimizing the prompt for best results...",
            IntentType.STRATEGY: f"I'll help optimize and improve your content about '{topic}'. Analyzing and enhancing...",
            IntentType.MULTI_FORMAT: f"I'll create a complete content package about '{topic}' including research, blog, and LinkedIn post. Starting the workflow..."
        }
        
        return response_templates.get(intent, "Processing your request...")
    
    async def handle_clarification(self, original_query: str, clarification: str, session_id: str) -> AgentOutput:
        """Handle follow-up clarification from user."""
        # Combine original query with clarification
        combined_query = f"{original_query}. {clarification}"
        
        input_data = AgentInput(
            query=combined_query,
            session_id=session_id,
            context=self.state_manager.get_session(session_id).get("context", {})
        )
        
        return await self.execute(input_data)
