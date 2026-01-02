import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
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
