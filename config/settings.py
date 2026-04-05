import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load .env file on import so settings are available everywhere.
# python-dotenv silently no-ops if .env does not exist.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable application configuration loaded from environment variables.

    All API keys and tuneable parameters live here so that every other module
    reads from a single source of truth rather than calling ``os.getenv``
    directly.

    Design note:
        Using a frozen dataclass (rather than a mutable dict or class)
        communicates that settings should not change at runtime.  It also
        makes the config object hashable and easy to compare in tests.

    Simplification for learning:
        A production app would use Pydantic's ``BaseSettings`` which adds
        automatic type coercion, validation, and support for reading from
        multiple sources (env vars, secrets files, AWS Secrets Manager, etc.).

    Attributes:
        openai_api_key: Required for LLM calls and DALL-E image generation.
        serpapi_api_key: Required for the SERP web search provider.
        tavily_api_key: Optional secondary search provider (used as failover).
        azure_openai_*: Optional Azure OpenAI deployment details.
        gemini_api_key: Optional Google Gemini as a third LLM fallback.
        langsmith_api_key / langsmith_project: Optional LangSmith tracing.
        backend_api_key: If set, the /run endpoint requires this key in the
            ``x-api-key`` header.
        backend_rpm: Maximum API requests per minute enforced by the backend
            rate limiter.
    """

    openai_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None
    log_level: str = "INFO"
    openai_base_url: Optional[str] = None
    tavily_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: Optional[str] = None
    azure_openai_deployment: Optional[str] = None
    gemini_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    langsmith_project: Optional[str] = None
    backend_api_key: Optional[str] = None
    backend_rpm: int = 60


def get_settings() -> Settings:
    openai_key = os.getenv("OPENAI_API_KEY")
    serp_key = os.getenv("SERPAPI_API_KEY")

    return Settings(
        openai_api_key=openai_key,
        serpapi_api_key=serp_key,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
        langsmith_project=os.getenv("LANGSMITH_PROJECT"),
        backend_api_key=os.getenv("BACKEND_API_KEY"),
        backend_rpm=int(os.getenv("BACKEND_RPM", "60")),
    )


settings = get_settings()
