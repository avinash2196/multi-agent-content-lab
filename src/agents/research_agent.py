from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from src.services.serp_service import SerpService
from src.services.tavily_service import TavilyService
from src.services.search_gateway import SearchGateway
from src.cache import CacheManager
from src.utils.rate_limiter import RateLimiter
from src.utils import ResearchSynthesizer, ReportFormatter, TextProcessor


class ResearchAgent(BaseAgent):
    """Agent that performs web research and produces a structured report."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        serp_service: Optional[SerpService] = None,
        search_gateway: Optional[SearchGateway] = None,
    ):
        super().__init__(name="research_agent", config=config)
        self.search_gateway = search_gateway or self._build_default_gateway()
        self.serp_service = serp_service or SerpService()
        self.synthesizer = ResearchSynthesizer()
        self.formatter = ReportFormatter()
        self.text_processor = TextProcessor()
        self.logger.info("Research Agent initialized")

    def _build_default_gateway(self) -> Optional[SearchGateway]:
        try:
            cache = CacheManager(ttl_seconds=self.config.get("cache_ttl", 300) if self.config else 300)
            rate = RateLimiter(max_requests=self.config.get("rpm", 30) if self.config else 30, window_seconds=60)
            serp = SerpService(cache=cache, rate_limiter=rate)
            providers = [serp]

            # Add Tavily if key configured
            try:
                tavily = TavilyService(cache=cache, rate_limiter=rate)
                if tavily.api_key:
                    providers.append(tavily)
            except Exception:
                pass

            return SearchGateway(providers=providers, cache=cache, rate_limiter=rate)
        except Exception:
            return None

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        query = input_data.query
        topic = self.text_processor.clean_text(query)

        # Fetch research results via gateway (with caching/rate-limit/failover) if available
        if self.search_gateway:
            results = await self.search_gateway.search(topic, num_results=self.config.get("num_results", 5))
        else:
            results = await self.serp_service.search(topic, num_results=self.config.get("num_results", 5))

        # Synthesize findings
        synthesis = self.synthesizer.synthesize(results)
        report = self.formatter.format_research_report(
            topic=topic,
            summary=synthesis.get("summary", ""),
            key_points=synthesis.get("key_points", []),
            sources=synthesis.get("sources", []),
        )

        return AgentOutput(
            content=report,
            success=True,
            metadata={
                "topic": topic,
                "sources": [r.to_dict() for r in results],
                "synthesis": synthesis,
            },
        )
