from __future__ import annotations

from typing import Any, Dict, Optional

from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from src.utils import (
    BlogGenerator,
    SEOOptimizer,
    ContentQualityChecker,
    TextProcessor,
    BrandVoiceProfile,
    BrandVoiceChecker,
    BrandVoiceRewriter,
)
from src.services.llm_gateway import LLMGateway


class BlogWriterAgent(BaseAgent):
    """Generate SEO-optimized blog content using research key points."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_gateway: Optional[LLMGateway] = None):
        super().__init__(name="blog_writer_agent", config=config)
        self.generator = BlogGenerator()
        self.seo = SEOOptimizer(primary_keywords=config.get("keywords", []) if config else [])
        self.quality = ContentQualityChecker()
        self.tp = TextProcessor()
        self.use_llm_polish = (config or {}).get("use_llm_polish", False)
        try:
            self.llm_gateway = llm_gateway or LLMGateway.from_settings()
        except Exception:
            self.llm_gateway = None
        self.voice_profile = BrandVoiceProfile(**(config.get("brand_voice", {}) if config else {}))
        self.voice_checker = BrandVoiceChecker(self.voice_profile)
        self.voice_rewriter = BrandVoiceRewriter(self.voice_profile, llm_gateway=self.llm_gateway)
        self.logger.info("Blog Writer Agent initialized")

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        topic = input_data.query or "Untitled"
        context = input_data.context or {}
        research = context.get("research", {})
        key_points = research.get("key_points") or context.get("key_points") or []

        # Build outline
        outline = self.generator.build_outline(topic, key_points)
        meta_desc = self.seo.generate_meta_description(research.get("summary", topic)) if research else ""
        
        # Generate full article content via LLM from research
        content = await self._generate_full_article_with_llm(topic, meta_desc, outline, key_points, research)

        # SEO embedding and quality metrics
        content = self.seo.embed_keywords(content)
        quality = self.quality.assess(content, keywords=self.seo.primary_keywords)
        slug = self.seo.make_slug(topic)

        voice_result = self.voice_checker.check(content)
        if self.llm_gateway and voice_result.score < 0.85:
            content = await self.voice_rewriter.rewrite(content, model=self.config.get("model", "gpt-4"))
            voice_result = self.voice_checker.check(content)

        return AgentOutput(
            content=content,
            success=True,
            metadata={
                "topic": topic,
                "outline": outline,
                "meta_description": meta_desc,
                "quality": quality,
                "slug": slug,
                "keywords": self.seo.primary_keywords,
                "voice_score": voice_result.score,
                "voice_issues": voice_result.issues,
            },
        )

    async def _generate_full_article_with_llm(
        self, topic: str, meta_desc: str, outline: list, key_points: list, research: dict
    ) -> str:
        """Generate full article content using LLM from research data."""
        if not self.llm_gateway:
            # Fallback to template if no LLM available
            return self.generator.render_markdown(topic, outline, key_points or [topic], {"description": meta_desc})
        
        try:
            research_summary = research.get("summary", "") or "No additional research data"
            key_points_str = "\n".join([f"- {p}" for p in (key_points or [])])
            
            prompt = f"""Write a comprehensive, well-structured blog post about "{topic}".

Research Summary: {research_summary}

Key Points to Cover:
{key_points_str}

Requirements:
- Write in professional, engaging markdown format
- Start with an engaging introduction that hooks the reader
- Create 3-4 substantial sections based on the outline: {', '.join(outline[1:3])}
- Each section should have 2-3 detailed paragraphs (not bullet points)
- Include the meta description naturally: "{meta_desc}"
- End with a strong conclusion that summarizes key takeaways
- Total length: 1500-2000 words minimum
- Return ONLY the markdown article, no other text

Output markdown article:"""
            
            messages = [
                {"role": "system", "content": "You are an expert technical writer. Write comprehensive, SEO-friendly blog posts that provide real value to readers."},
                {"role": "user", "content": prompt}
            ]
            
            content = await self.llm_gateway.chat(
                messages=messages,
                model=self.config.get("model", "gpt-4o-mini"),
                temperature=0.7,
                max_tokens=3000,
            )
            return content or self.generator.render_markdown(topic, outline, key_points or [topic], {"description": meta_desc})
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"LLM article generation failed, using template: {e}")
            return self.generator.render_markdown(topic, outline, key_points or [topic], {"description": meta_desc})
