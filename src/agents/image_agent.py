from __future__ import annotations

from typing import Any, Dict, Optional

from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from src.services.dalle_service import DalleService
from src.services.llm_gateway import LLMGateway
from src.utils.observability import Observability
from src.utils.prompt_optimizer import PromptOptimizer
from src.utils.image_manager import ImageManager


class ImageAgent(BaseAgent):
    """Agent to generate images via DALL-E with prompt optimization."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        dalle_service: Optional[DalleService] = None,
        observability: Optional[Observability] = None,
        image_manager: Optional[ImageManager] = None,
        llm_gateway: Optional[LLMGateway] = None,
    ):
        super().__init__(name="image_agent", config=config)
        self.optimizer = PromptOptimizer()
        self.observability = observability or Observability()
        self.dalle = dalle_service or DalleService(observability=self.observability)
        self.image_manager = image_manager or ImageManager()
        self.use_alt_text = (config or {}).get("generate_alt_text", False)
        self.llm_gateway = llm_gateway or (LLMGateway.from_settings(observability=self.observability) if self.use_alt_text else None)
        self.logger.info("Image Agent initialized")

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        description = input_data.query or ""
        context = input_data.context or {}
        style = context.get("style", "professional")
        aspect = context.get("aspect_ratio", "1024x1024")
        n = context.get("n", 1)
        
        # Check if alt-text generation is enabled via context
        generate_alt_text = context.get("generate_alt_text", False)

        # Build enhanced prompt from research if available
        research = context.get("research", {})
        enhanced_prompt = await self._build_image_prompt(description, research, style)

        with self.observability.span(
            "image_agent.generate",
            {"aspect_ratio": aspect, "count": n, "style": style or "default"},
        ):
            images = await self.dalle.generate(prompt=enhanced_prompt, size=aspect, n=n)
            self.observability.record_event("image_agent.success", {"count": len(images.get("urls", []))})

        # Store images with metadata in manager
        key = input_data.session_id or context.get("topic") or input_data.query
        entries = self.image_manager.add_images(
            key=key or "default",
            urls=images.get("urls", []),
            prompt=enhanced_prompt,
            aspect_ratio=aspect,
            created=images.get("created") or 0,
        )

        # Generate alt-text if requested and gateway available
        if generate_alt_text and self.llm_gateway:
            try:
                await self.image_manager.enrich_alt_text(key or "default", llm_gateway=self.llm_gateway)
                self.logger.info("Alt text generation completed")
            except Exception as e:  # noqa: BLE001
                self.logger.warning(f"Alt text generation skipped: {e}")

        return AgentOutput(
            content="\n".join(images.get("urls", [])),
            success=True,
            metadata={
                "prompt": enhanced_prompt,
                "urls": images.get("urls", []),
                "created": images.get("created"),
                "aspect_ratio": aspect,
                "count": n,
                "images": [entry.__dict__ for entry in entries],
            },
        )
    async def _build_image_prompt(self, topic: str, research: dict, style: str = "professional") -> str:
        """Build an enhanced image prompt using research context and LLM if available."""
        # Extract research insights
        summary = research.get("summary", "") if research else ""
        key_points = research.get("key_points", []) if research else []
        
        # Start with base topic
        base_prompt = topic or "Professional visual concept"
        
        # Try to use LLM to create a more descriptive prompt
        if self.llm_gateway:
            try:
                context_str = ""
                if summary:
                    context_str += f"Research summary: {summary[:300]}\n"
                if key_points:
                    context_str += f"Key points: {', '.join(key_points[:5])}\n"
                
                llm_prompt = f"""Generate a concise, vivid image prompt for DALL-E based on this topic and context.
                
Topic: {base_prompt}
{context_str}
Style: {style}

Create a single, detailed image prompt (2-3 sentences max) that captures the essence of the topic with research insights. 
Focus on visual elements, composition, mood, and professional quality.
Respond with ONLY the image prompt, nothing else."""
                
                response = await self.llm_gateway.generate_text(
                    prompt=llm_prompt,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=150
                )
                if response:
                    return response.strip()
            except Exception as e:  # noqa: BLE001
                self.logger.debug(f"LLM prompt generation failed, using fallback: {e}")
        
        # Fallback: Build prompt from research manually
        if summary or key_points:
            parts = [base_prompt]
            if summary:
                parts.append(f"based on: {summary[:100]}")
            if key_points:
                parts.append(f"highlights: {key_points[0][:50]}")
            parts.append(f"style: {style}, professional, high-quality, detailed")
            return " | ".join(parts)
        
        # Final fallback: Simple prompt with style
        return f"{base_prompt} | style: {style}, professional, high-quality, detailed"