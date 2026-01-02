from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional, Protocol, Sequence

import google.generativeai as genai
from openai import AsyncAzureOpenAI, AsyncOpenAI

from config import settings
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.observability import Observability
from src.utils.rate_limiter import RateLimiter


class LLMProvider(Protocol):
    name: str

    async def chat(self, messages: Sequence[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:  # pragma: no cover - Protocol
        ...


class OpenAIProvider:
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        observability: Optional[Observability] = None,
    ):
        self.name = "openai"
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.observability = observability or Observability()

    async def chat(self, messages: Sequence[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        if self.rate_limiter:
            self.rate_limiter.ensure()
        if not self.circuit_breaker.allow():
            raise RuntimeError("circuit_open")

        chosen_model = model or self.model
        try:
            with self.observability.span("llm.openai.chat", {"model": chosen_model}):
                response = await self.client.chat.completions.create(
                    model=chosen_model,
                    messages=list(messages),
                    **kwargs,
                )
            self.circuit_breaker.record_success()
            return response.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            self.circuit_breaker.record_failure()
            self.observability.record_error("llm.openai.error", e)
            raise


class AzureOpenAIProvider:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        api_version: str,
        deployment: str,
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        observability: Optional[Observability] = None,
    ):
        self.name = "azure_openai"
        self.deployment = deployment
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.observability = observability or Observability()

    async def chat(self, messages: Sequence[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        if self.rate_limiter:
            self.rate_limiter.ensure()
        if not self.circuit_breaker.allow():
            raise RuntimeError("circuit_open")

        chosen_model = model or self.deployment
        try:
            with self.observability.span("llm.azure.chat", {"deployment": chosen_model}):
                response = await self.client.chat.completions.create(
                    model=chosen_model,
                    messages=list(messages),
                    **kwargs,
                )
            self.circuit_breaker.record_success()
            return response.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            self.circuit_breaker.record_failure()
            self.observability.record_error("llm.azure.error", e)
            raise


class GeminiProvider:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        observability: Optional[Observability] = None,
    ):
        self.name = "gemini"
        self.model = model
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.observability = observability or Observability()

    def _render_messages(self, messages: Sequence[Dict[str, str]]) -> str:
        return "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, "text"):
            return response.text or ""
        try:
            candidates = getattr(response, "candidates", None) or []
            if candidates and getattr(candidates[0], "content", None):
                parts = getattr(candidates[0].content, "parts", None) or []
                texts = [getattr(p, "text", "") for p in parts]
                return "".join(texts)
        except Exception:
            return ""
        return ""

    async def chat(self, messages: Sequence[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        if self.rate_limiter:
            self.rate_limiter.ensure()
        if not self.circuit_breaker.allow():
            raise RuntimeError("circuit_open")

        chosen_model = model or self.model
        prompt = self._render_messages(messages)
        try:
            with self.observability.span("llm.gemini.chat", {"model": chosen_model}):
                response = await asyncio.to_thread(self._model.generate_content, prompt, **kwargs)
            self.circuit_breaker.record_success()
            return self._extract_text(response)
        except Exception as e:  # noqa: BLE001
            self.circuit_breaker.record_failure()
            self.observability.record_error("llm.gemini.error", e)
            raise


class LLMGateway:
    """Multiprovider LLM gateway with rate limiting, circuit breakers, and observability."""

    def __init__(
        self,
        providers: List[LLMProvider],
        rate_limiter: Optional[RateLimiter] = None,
        observability: Optional[Observability] = None,
    ):
        if not providers:
            raise ValueError("At least one LLM provider required")
        self.providers = providers
        self.rate_limiter = rate_limiter
        self.observability = observability or Observability()

    async def chat(self, messages: Sequence[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        if self.rate_limiter:
            self.rate_limiter.ensure()

        last_error: Exception | None = None
        for provider in self.providers:
            try:
                with self.observability.span("llm.gateway.call", {"provider": provider.name, "model": model or "auto"}):
                    response = await provider.chat(messages=messages, model=model, **kwargs)
                self.observability.record_event("llm.gateway.success", {"provider": provider.name})
                return response
            except Exception as e:  # noqa: BLE001
                last_error = e
                self.observability.record_error("llm.gateway.error", e)
                continue

        if last_error:
            raise last_error
        raise RuntimeError("no_llm_providers_available")

    @classmethod
    def from_settings(cls, observability: Optional[Observability] = None) -> "LLMGateway":
        obs = observability or Observability()
        rpm = int(os.getenv("LLM_RPM", "60"))
        rate_limiter = RateLimiter(max_requests=rpm, window_seconds=60)

        providers: List[LLMProvider] = []
        if settings.openai_api_key:
            providers.append(
                OpenAIProvider(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    observability=obs,
                )
            )

        if (
            settings.azure_openai_api_key
            and settings.azure_openai_endpoint
            and settings.azure_openai_api_version
            and settings.azure_openai_deployment
        ):
            providers.append(
                AzureOpenAIProvider(
                    api_key=settings.azure_openai_api_key,
                    endpoint=settings.azure_openai_endpoint,
                    api_version=settings.azure_openai_api_version,
                    deployment=settings.azure_openai_deployment,
                    observability=obs,
                )
            )

        if settings.gemini_api_key:
            providers.append(
                GeminiProvider(
                    api_key=settings.gemini_api_key,
                    observability=obs,
                )
            )

        return cls(providers=providers, rate_limiter=rate_limiter, observability=obs)


__all__ = [
    "LLMGateway",
    "LLMProvider",
    "OpenAIProvider",
    "AzureOpenAIProvider",
    "GeminiProvider",
]
