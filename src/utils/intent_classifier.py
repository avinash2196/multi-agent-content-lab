from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import json


class IntentType(str, Enum):
    """Types of user intents."""
    RESEARCH = "research"
    BLOG = "blog"
    LINKEDIN = "linkedin"
    IMAGE = "image"
    STRATEGY = "strategy"
    MULTI_FORMAT = "multi_format"
    UNCLEAR = "unclear"


class ClassificationResult(BaseModel):
    """Result of intent classification."""
    intent: IntentType
    topic: str
    confidence: float = Field(ge=0.0, le=1.0)
    requirements: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentClassifier:
    """Classifies user queries to determine intent and extract relevant information."""
    
    def __init__(self):
        self.logger = logging.getLogger("intent_classifier")
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Set up keyword patterns for intent detection."""
        self.intent_patterns = {
            IntentType.RESEARCH: [
                "research", "find information", "learn about", "what is", 
                "tell me about", "explain", "investigate", "study", "analyze",
                "gather data", "facts about", "statistics on"
            ],
            IntentType.BLOG: [
                "blog post", "article", "write about", "blog about",
                "seo content", "long form", "comprehensive guide",
                "tutorial", "how to", "guide to", "write an article"
            ],
            IntentType.LINKEDIN: [
                "linkedin", "linkedin post", "professional post",
                "social media post", "share on linkedin", "post about",
                "professional update", "thought leadership"
            ],
            IntentType.IMAGE: [
                "image", "picture", "generate image", "create visual",
                "illustration", "graphic", "dall-e", "draw", "visualize",
                "design", "create image"
            ],
            IntentType.STRATEGY: [
                "improve", "enhance", "optimize", "review content",
                "make better", "refine", "edit", "polish", "format",
                "organize content", "content strategy"
            ],
            IntentType.MULTI_FORMAT: [
                "complete content", "full package", "all formats",
                "blog and linkedin", "including blog", "content series", "multi-format",
                "research and blog", "everything about"
            ]
        }
    
    def classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """Classify the user query and extract intent."""
        query_lower = query.lower()
        context = context or {}
        
        # Score each intent based on keyword matches
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            scores[intent] = score
        
        # Get the highest scoring intent
        max_score = max(scores.values()) if scores else 0
        
        if max_score == 0:
            # No clear matches, use heuristics
            classified_intent = self._fallback_classification(query_lower)
            confidence = 0.3
        else:
            classified_intent = max(scores, key=scores.get)
            # Normalize confidence (simple approach)
            confidence = min(0.95, 0.5 + (max_score * 0.15))
        
        # Extract topic
        topic = self._extract_topic(query)
        
        # Extract requirements
        requirements = self._extract_requirements(query)
        
        # Extract keywords
        keywords = self._extract_keywords(query)
        
        result = ClassificationResult(
            intent=classified_intent,
            topic=topic,
            confidence=confidence,
            requirements=requirements,
            keywords=keywords,
            metadata={
                "scores": {k.value: v for k, v in scores.items()},
                "query_length": len(query),
                "context_available": bool(context)
            }
        )
        
        self.logger.info(f"Classified intent: {classified_intent.value} (confidence: {confidence:.2f})")
        return result
    
    def _fallback_classification(self, query_lower: str) -> IntentType:
        """Fallback classification when no patterns match."""
        # Default heuristics
        if "?" in query_lower or query_lower.startswith(("what", "why", "how", "when", "where")):
            return IntentType.RESEARCH
        elif len(query_lower.split()) > 10:
            return IntentType.BLOG
        elif any(word in query_lower for word in ["post", "share", "update"]):
            return IntentType.LINKEDIN
        else:
            return IntentType.UNCLEAR
    
    def _extract_topic(self, query: str) -> str:
        """Extract the main topic from the query."""
        # Remove common intent words to get topic
        words_to_remove = [
            "write", "create", "generate", "make", "blog", "post", 
            "article", "about", "on", "regarding", "concerning",
            "please", "can", "you", "could", "would", "i", "need",
            "want", "a", "an", "the"
        ]
        
        words = query.lower().split()
        topic_words = [w for w in words if w not in words_to_remove and len(w) > 2]
        
        # Take first 5 significant words as topic
        topic = " ".join(topic_words[:5]) if topic_words else query
        
        return topic.strip()
    
    def _extract_requirements(self, query: str) -> List[str]:
        """Extract specific requirements from the query."""
        requirements = []
        query_lower = query.lower()
        
        # Length requirements
        if "short" in query_lower or "brief" in query_lower:
            requirements.append("short_form")
        elif "long" in query_lower or "detailed" in query_lower or "comprehensive" in query_lower:
            requirements.append("long_form")
        
        # Tone requirements
        if "professional" in query_lower:
            requirements.append("professional_tone")
        elif "casual" in query_lower or "conversational" in query_lower:
            requirements.append("casual_tone")
        
        # Format requirements
        if "seo" in query_lower:
            requirements.append("seo_optimized")
        if "keywords" in query_lower:
            requirements.append("keyword_focused")
        if "hashtag" in query_lower:
            requirements.append("include_hashtags")
        
        return requirements
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract potential keywords from the query."""
        # Simple keyword extraction (can be enhanced)
        from src.utils import TextProcessor
        
        processor = TextProcessor()
        return processor.extract_keywords(query, max_keywords=5)
    
    def classify_with_llm(self, query: str, context: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """Use LLM for more accurate classification (to be implemented with OpenAI)."""
        self.logger.warning("Synchronous LLM classification not supported; using rule-based")
        return self.classify(query, context)

    async def classify_with_llm_async(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        llm_gateway: Any = None,
        model: str = "gpt-4",
    ) -> ClassificationResult:
        """Async LLM-backed classification with gateway and fallback to rule-based."""
        try:
            gateway = llm_gateway
            if gateway is None:
                try:
                    from src.services.llm_gateway import LLMGateway  # late import to avoid cycles

                    gateway = LLMGateway.from_settings()
                except Exception as e:  # noqa: BLE001
                    self.logger.warning(f"LLM gateway unavailable, falling back: {e}")
                    return self.classify(query, context)

            prompt = json.dumps({"query": query, "context": context or {}}, ensure_ascii=False)
            messages = [
                {"role": "system", "content": "Classify the intent of the query and return JSON with intent, topic, requirements, keywords."},
                {"role": "user", "content": prompt},
            ]
            response_text = await gateway.chat(messages, model=model, temperature=0.2, max_tokens=200)
            try:
                parsed = json.loads(response_text)
            except Exception:
                parsed = {}

            intent_str = parsed.get("intent", IntentType.UNCLEAR.value)
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.UNCLEAR

            return ClassificationResult(
                intent=intent,
                topic=parsed.get("topic", query),
                confidence=float(parsed.get("confidence", 0.7)),
                requirements=parsed.get("requirements", []),
                keywords=parsed.get("keywords", []),
                metadata={"source": "llm", "model": model},
            )
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"LLM classification failed, using rule-based: {e}")
            return self.classify(query, context)
