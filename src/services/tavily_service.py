from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from config import settings
from src.cache import CacheManager
from src.utils.rate_limiter import RateLimiter
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.observability import Observability


@dataclass
class TavilyResult:
    title: str
    link: str
    snippet: str
    source: str = "tavily"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "source": self.source,
        }


class TavilyService:
    """Tavily search client with optional caching and rate limiting."""

    BASE_URL = "https://api.tavily.com/search"

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        cache: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        observability: Optional[Observability] = None,
    ):
        self.api_key = api_key or getattr(settings, "tavily_api_key", None)
        self.client = client
        self.cache = cache or CacheManager(ttl_seconds=300)
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger("tavily_service")
        self.circuit_breaker = circuit_breaker
        self.observability = observability or Observability()

    async def search(self, query: str, num_results: int = 5, **params) -> List[TavilyResult]:
        if not self.api_key:
            raise RuntimeError("Tavily API key not configured")
        if not query or not query.strip():
            raise ValueError("Query must not be empty")
        if self.circuit_breaker and not self.circuit_breaker.allow():
            raise RuntimeError("circuit_open")

        cache_key = ("tavily", query.lower(), num_results, frozenset(params.items()))
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.observability.record_event("tavily.cache_hit", {"query": query, "num_results": num_results})
            return cached

        if self.rate_limiter:
            self.rate_limiter.ensure()

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": num_results,
            "search_depth": params.get("search_depth", "basic"),
        }

        created_client = None
        client = self.client
        if client is None:
            created_client = httpx.AsyncClient(timeout=20)
            client = created_client

        try:
            with self.observability.span("tavily.search", {"num_results": num_results, "depth": payload["search_depth"]}):
                response = await client.post(self.BASE_URL, json=payload)
            if response.status_code != httpx.codes.OK:
                raise RuntimeError(f"Tavily error: {response.status_code} - {response.text}")
            data = response.json()
            results = data.get("results", [])
            normalized = [
                TavilyResult(
                    title=item.get("title") or "",
                    link=item.get("url") or "",
                    snippet=item.get("content") or "",
                )
                for item in results[:num_results]
            ]
            self.cache.set(cache_key, normalized)
            self.logger.info(f"Tavily returned {len(normalized)} results for '{query}'")
            if self.circuit_breaker:
                self.circuit_breaker.record_success()
            self.observability.record_event("tavily.success", {"count": len(normalized)})
            return normalized
        except httpx.RequestError as exc:
            self.logger.error(f"Tavily request failed: {exc}")
            if self.circuit_breaker:
                self.circuit_breaker.record_failure()
            self.observability.record_error("tavily.error", exc)
            raise
        finally:
            if created_client:
                await created_client.aclose()
