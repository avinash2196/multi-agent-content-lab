from __future__ import annotations

from typing import Any, Dict, Optional, List

from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from src.utils import TextProcessor, ContentQualityChecker, ImageManager


class StrategistAgent(BaseAgent):
    """Organize multi-format outputs, suggest improvements, and surface next actions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, image_manager: Optional[ImageManager] = None):
        super().__init__(name="strategist_agent", config=config)
        self.tp = TextProcessor()
        self.quality = ContentQualityChecker()
        self.image_manager = image_manager or ImageManager()
        self.logger.info("Strategist Agent initialized")

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        context = input_data.context or {}

        research = context.get("research") or context.get("research_results") or {}
        blog = context.get("blog") or context.get("blog_content") or ""
        linkedin = context.get("linkedin") or context.get("linkedin_content") or ""
        images = context.get("images") or context.get("image_urls") or []
        topic = input_data.query or context.get("topic") or ""

        sections: List[str] = []

        sections.append("## Content Package Summary")
        sections.append(f"- Topic: {topic or 'N/A'}")
        sections.append(f"- Sources: {len(research.get('sources', [])) if isinstance(research, dict) else 0}")
        sections.append(f"- Images: {len(images) if isinstance(images, list) else 0}")

        if research:
            summary = research.get("summary") if isinstance(research, dict) else ""
            key_points = research.get("key_points", []) if isinstance(research, dict) else []
            sections.append("\n## Research Highlights")
            if summary:
                sections.append(f"- Summary: {summary}")
            for kp in key_points[:5]:
                sections.append(f"- {kp}")

        if blog:
            sections.append("\n## Blog Overview")

        if linkedin:
            sections.append("\n## LinkedIn Post")

        if images:
            sections.append("\n## Visual Assets")
            key = input_data.session_id or context.get("topic") or topic
            managed = self.image_manager.list_images(key or "default")
            if managed:
                for entry in managed[:3]:
                    label = entry.alt_text or entry.prompt[:60]
                    sections.append(f"- {entry.url} (alt: {label})")
                if len(managed) > 3:
                    sections.append(f"- (+{len(managed) - 3} more)")
            else:
                for url in images[:3]:
                    sections.append(f"- {url}")
                if len(images) > 3:
                    sections.append(f"- (+{len(images) - 3} more)")

        sections.append("\n## Next Actions")
        sections.append("- Review and edit drafts for brand tone")
        if images:
            sections.append("- Add alt text for images and embed in blog")
        if not blog:
            sections.append("- Generate blog content")
        if not linkedin:
            sections.append("- Generate LinkedIn post")
        sections.append("- Publish or schedule across channels")

        content = "\n".join(sections)

        return AgentOutput(
            content=content,
            success=True,
            metadata={
                "topic": topic,
                "has_blog": bool(blog),
                "has_linkedin": bool(linkedin),
                "image_count": len(images) if isinstance(images, list) else 0,
                "research_sources": len(research.get("sources", [])) if isinstance(research, dict) else 0,
            },
        )
