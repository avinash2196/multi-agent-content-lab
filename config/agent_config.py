from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ModelConfig:
    """Configuration for LLM model parameters."""
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


@dataclass
class AgentConfig:
    """Base configuration for agents."""
    name: str
    model_config: ModelConfig
    enabled: bool = True
    timeout: int = 60
    max_retries: int = 3
    custom_params: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "model_config": {
                "model_name": self.model_config.model_name,
                "temperature": self.model_config.temperature,
                "max_tokens": self.model_config.max_tokens,
                "top_p": self.model_config.top_p,
                "frequency_penalty": self.model_config.frequency_penalty,
                "presence_penalty": self.model_config.presence_penalty,
            },
            "enabled": self.enabled,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "custom_params": self.custom_params or {},
        }


# Predefined configurations for each agent type
QUERY_HANDLER_CONFIG = AgentConfig(
    name="query_handler",
    model_config=ModelConfig(model_name="gpt-4", temperature=0.3, max_tokens=500),
)

RESEARCH_AGENT_CONFIG = AgentConfig(
    name="research_agent",
    model_config=ModelConfig(model_name="gpt-4", temperature=0.5, max_tokens=3000),
    timeout=120,
)

BLOG_WRITER_CONFIG = AgentConfig(
    name="blog_writer",
    model_config=ModelConfig(model_name="gpt-4", temperature=0.7, max_tokens=4000),
)

LINKEDIN_WRITER_CONFIG = AgentConfig(
    name="linkedin_writer",
    model_config=ModelConfig(model_name="gpt-4", temperature=0.8, max_tokens=1000),
)

IMAGE_AGENT_CONFIG = AgentConfig(
    name="image_agent",
    model_config=ModelConfig(model_name="dall-e-3", temperature=0.0, max_tokens=1000),
)

STRATEGIST_CONFIG = AgentConfig(
    name="strategist",
    model_config=ModelConfig(model_name="gpt-4", temperature=0.6, max_tokens=2000),
)
