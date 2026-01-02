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
class SearchResult:
    """Normalized search result entry."""
    title: str
    link: str
    snippet: str
    source: str = "serpapi"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "source": self.source,
        }


class SerpService:
    """Lightweight SERP API client using httpx.AsyncClient."""

    BASE_URL = "https://serpapi.com/search.json"

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        cache: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        observability: Optional[Observability] = None,
    ):
        self.api_key = api_key or settings.serpapi_api_key
        self.client = client
        self.logger = logging.getLogger("serp_service")
        self.cache = cache or CacheManager(ttl_seconds=300)
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker
        self.observability = observability or Observability()

    async def search(self, query: str, num_results: int = 5, **params) -> List[SearchResult]:
        if not query or not query.strip():
            raise ValueError("Query must not be empty")
        if self.circuit_breaker and not self.circuit_breaker.allow():
            raise RuntimeError("circuit_open")

        request_params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": "google",
            **params,
        }

        cache_key = (query.lower(), num_results, frozenset(params.items()))
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.observability.record_event("serp.cache_hit", {"query": query, "num_results": num_results})
            return cached

        if self.rate_limiter:
            self.rate_limiter.ensure()

        created_client = None
        client = self.client
        if client is None:
            created_client = httpx.AsyncClient(timeout=15)
            client = created_client

        try:
            with self.observability.span("serp.search", {"num_results": num_results}):
                response = await client.get(self.BASE_URL, params=request_params)
            if response.status_code != httpx.codes.OK:
                raise RuntimeError(f"SERP API error: {response.status_code} - {response.text}")

            data = response.json()
            results = data.get("organic_results") or data.get("results") or []
            normalized = [
                SearchResult(
                    title=item.get("title") or item.get("name") or "",
                    link=item.get("link") or item.get("url") or "",
                    snippet=item.get("snippet") or item.get("description") or "",
                )
                for item in results[:num_results]
                if item
            ]
            self.logger.info(f"SERP returned {len(normalized)} results for '{query}'")
            self.cache.set(cache_key, normalized)
            if self.circuit_breaker:
                self.circuit_breaker.record_success()
            self.observability.record_event("serp.success", {"count": len(normalized)})
            return normalized
        except httpx.RequestError as exc:
            self.logger.error(f"SERP request failed: {exc}")
            if self.circuit_breaker:
                self.circuit_breaker.record_failure()
            self.observability.record_error("serp.error", exc)
            raise
        finally:
            if created_client:
                await created_client.aclose()
