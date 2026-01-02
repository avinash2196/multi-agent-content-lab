from __future__ import annotations

import logging
from typing import List, Protocol, Any, Dict, Optional

from src.cache import CacheManager
from src.utils.rate_limiter import RateLimiter
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.observability import Observability


class SearchProvider(Protocol):
    async def search(self, query: str, num_results: int = 5, **params):
        ...


class SearchGateway:
    """Wraps search providers with caching, rate limiting, and failover."""

    def __init__(
        self,
        providers: List[SearchProvider],
        cache: CacheManager | None = None,
        rate_limiter: RateLimiter | None = None,
        observability: Observability | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        if not providers:
            raise ValueError("At least one provider required")
        self.providers = providers
        self.cache = cache or CacheManager(ttl_seconds=300)
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger("search_gateway")
        self.observability = observability or Observability()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    async def search(self, query: str, num_results: int = 5, **params):
        if self.rate_limiter:
            self.rate_limiter.ensure()
        if not self.circuit_breaker.allow():
            raise RuntimeError("circuit_open")

        cache_key = (query.lower(), num_results, frozenset(params.items()))
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.observability.record_event("search_gateway.cache_hit", {"query": query, "num_results": num_results})
            return cached

        last_error: Exception | None = None
        for provider in self.providers:
            try:
                with self.observability.span(
                    "search_gateway.search",
                    {"provider": provider.__class__.__name__, "num_results": num_results},
                ):
                    results = await provider.search(query, num_results=num_results, **params)
                self.cache.set(cache_key, results)
                self.circuit_breaker.record_success()
                self.observability.record_event(
                    "search_gateway.success", {"provider": provider.__class__.__name__, "count": len(results)}
                )
                return results
            except Exception as e:  # noqa: BLE001
                last_error = e
                self.logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                self.circuit_breaker.record_failure()
                self.observability.record_error("search_gateway.provider_error", e)
                continue
        if last_error:
            raise last_error
        raise RuntimeError("All providers failed with no error returned")
