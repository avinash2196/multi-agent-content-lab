from __future__ import annotations

from typing import Any, Dict, Optional, List

from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from src.utils import (
    LinkedInFormatter,
    HashtagEngine,
    TextProcessor,
    BrandVoiceProfile,
    BrandVoiceChecker,
    BrandVoiceRewriter,
)
from src.services.llm_gateway import LLMGateway


class LinkedInAgent(BaseAgent):
    """Generate engaging LinkedIn posts with hooks, body, CTA, and hashtags."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_gateway: Optional[LLMGateway] = None):
        super().__init__(name="linkedin_writer_agent", config=config)
        self.formatter = LinkedInFormatter()
        self.hashtags = HashtagEngine()
        self.tp = TextProcessor()
        self.default_cta = "What do you think?"
        self.max_chars = (config or {}).get("max_chars", 1200)
        self.use_llm_polish = (config or {}).get("use_llm_polish", False)
        self.llm_gateway = llm_gateway or LLMGateway.from_settings()
        self.voice_profile = BrandVoiceProfile(**(config.get("brand_voice", {}) if config else {}))
        self.voice_checker = BrandVoiceChecker(self.voice_profile)
        self.voice_rewriter = BrandVoiceRewriter(self.voice_profile, llm_gateway=self.llm_gateway)
        self.logger.info("LinkedIn Agent initialized")

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        topic = input_data.query or ""
        context = input_data.context or {}
        research = context.get("research", {})
        key_points: List[str] = context.get("key_points") or research.get("key_points") or []
        tone = (context.get("tone") or "professional").lower()
        cta = context.get("cta") or self.default_cta
        linkedin_with_images = context.get("linkedin_with_images", False)

        # Generate full post via LLM
        post_text = await self._generate_post_with_llm(topic, key_points, research, tone, cta)
        
        tags = self.hashtags.generate(topic, key_points=key_points, count=6)
        post_text = f"{post_text}\n\n{' '.join([f'#{tag}' for tag in tags])}"
        
        # Add images if requested
        if linkedin_with_images:
            images = context.get("images") or []
            if images:
                post_text += f"\n\n[Images: {len(images)} visual(s) attached]"
                for img_url in images[:1]:  # Attach first image as primary
                    post_text += f"\n{img_url}"

        voice_result = self.voice_checker.check(post_text)
        if self.llm_gateway and voice_result.score < 0.85:
            post_text = await self._polish(post_text, tone=tone, topic=topic)
            voice_result = self.voice_checker.check(post_text)

        return AgentOutput(
            content=post_text,
            success=True,
            metadata={
                "topic": topic,
                "tone": tone,
                "cta": cta,
                "hashtags": tags,
                "length": len(post_text),
                "voice_score": voice_result.score,
                "voice_issues": voice_result.issues,
            },
        )

    async def _generate_post_with_llm(
        self, topic: str, key_points: List[str], research: dict, tone: str, cta: str
    ) -> str:
        """Generate engaging LinkedIn post via LLM."""
        if not self.llm_gateway:
            # Fallback to template
            body = self._make_body(topic, key_points, tone)
            hook = self._make_hook(topic, tone)
            return f"{hook}\n\n" + "\n".join(body)
        
        try:
            research_summary = research.get("summary", "") or ""
            key_points_str = "\n".join([f"• {p}" for p in (key_points[:5] or [])])
            
            prompt = f"""Write an engaging LinkedIn post about "{topic}" that drives engagement and sparks conversation.

Research Context: {research_summary}

Key Points to Include:
{key_points_str}

Requirements:
- Start with a compelling hook (question or bold statement)
- Keep tone: {tone}
- Include 3-5 substantive insights (not just bullets)
- Make it conversational and authentic
- End with: {cta}
- Total length: 250-350 words (LinkedIn sweet spot for engagement)
- Make it inspirational/thought-provoking
- Return ONLY the post text, no markdown formatting, no hashtags

Write the LinkedIn post:"""
            
            messages = [
                {"role": "system", "content": "You are a LinkedIn content strategist. Write posts that are authentic, insightful, and drive meaningful engagement."},
                {"role": "user", "content": prompt}
            ]
            
            post = await self.llm_gateway.chat(
                messages=messages,
                model=self.config.get("model", "gpt-4o-mini"),
                temperature=0.8,
                max_tokens=600,
            )
            return post or self._make_template_post(topic, key_points, tone, cta)
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"LLM post generation failed, using template: {e}")
            return self._make_template_post(topic, key_points, tone, cta)

    def _make_template_post(self, topic: str, key_points: List[str], tone: str, cta: str) -> str:
        """Fallback template post if LLM fails."""
        hook = self._make_hook(topic, tone)
        body = self._make_body(topic, key_points, tone)
        return f"{hook}\n\n" + "\n".join(body) + f"\n\n{cta}"

    async def _polish(self, text: str, tone: str, topic: str) -> str:
        try:
            messages = [
                {"role": "system", "content": "You are a concise LinkedIn editor. Keep it tight and engaging."},
                {
                    "role": "user",
                    "content": (
                        f"Polish this LinkedIn post about {topic}. Keep length under {self.max_chars} chars, "
                        f"tone {tone}, preserve hashtags and CTA. Return plain text only."
                    ),
                },
                {"role": "user", "content": text},
            ]
            return await self.llm_gateway.chat(
                messages=messages,
                model=self.config.get("model", "gpt-4"),
                temperature=0.5,
                max_tokens=400,
            )
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"LLM polish skipped: {e}")
            return text

    def _make_hook(self, topic: str, tone: str) -> str:
        topic_clean = topic.strip() or "this topic"
        if tone == "casual":
            return f"Quick thought on {topic_clean} →"
        return f"3 insights on {topic_clean} you can use today"

    def _make_body(self, topic: str, key_points: List[str], tone: str) -> List[str]:
        if not key_points:
            key_points = [f"Why {topic} matters", f"Common mistake to avoid in {topic}", f"One quick win for {topic}"]
        # Keep lines concise for LinkedIn readability
        body = []
        for idx, point in enumerate(key_points[:4], start=1):
            body.append(f"{idx}. {point}")
        if tone == "casual":
            body.append("")
            body.append("If this helps, drop a comment 🙌")
        return body
