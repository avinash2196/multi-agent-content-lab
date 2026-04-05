from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from config import settings
from src.utils.rate_limiter import RateLimiter
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.observability import Observability


class DalleService:
    """Wrapper around OpenAI's image generation with safeguards."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "dall-e-3",
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        observability: Optional[Observability] = None,
        client: Optional[AsyncOpenAI] = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.model = model
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.logger = logging.getLogger("dalle_service")
        self.observability = observability or Observability()
        try:
            self.client = client or AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        except Exception:
            self.client = None

    async def generate(self, prompt: str, size: str = "1024x1024", n: int = 1) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("openai_api_key_missing")
        if self.rate_limiter:
            self.rate_limiter.ensure()
        if not self.circuit_breaker.allow():
            raise RuntimeError("circuit_open")

        try:
            with self.observability.span("dalle.generate", {"model": self.model, "size": size, "count": n}):
                resp = await self.client.images.generate(model=self.model, prompt=prompt, n=n, size=size)
                self.circuit_breaker.record_success()
                urls = [img.url for img in resp.data]
                self.observability.record_event("dalle.success", {"count": len(urls), "model": self.model})
                return {"urls": urls, "created": resp.created}
        except Exception as e:  # noqa: BLE001
            self.circuit_breaker.record_failure()
            self.logger.error(f"DALL-E generation failed: {e}")
            self.observability.record_error("dalle.error", e)
            raise
