from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.text_processor import TextProcessor


@dataclass
class BrandVoiceProfile:
    """Declarative brand voice configuration."""

    name: str = "default"
    tone: str = "professional"
    formality: str = "medium"  # low|medium|high
    energy: str = "medium"  # low|medium|high
    do_use: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)
    banned: List[str] = field(default_factory=list)
    preferred_vocab: List[str] = field(default_factory=list)
    persona: str = "Clear, helpful, and concise."


@dataclass
class VoiceCheckResult:
    score: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class BrandVoiceChecker:
    """Lightweight rule-based checker for brand voice adherence."""

    def __init__(self, profile: Optional[BrandVoiceProfile] = None):
        self.profile = profile or BrandVoiceProfile()
        self.tp = TextProcessor()

    def check(self, text: str) -> VoiceCheckResult:
        issues: List[str] = []
        recs: List[str] = []
        score = 1.0

        lower = text.lower()

        # Banned terms
        banned_hits = [w for w in self.profile.banned if w.lower() in lower]
        if banned_hits:
            issues.append(f"Banned terms present: {', '.join(banned_hits)}")
            score -= 0.3

        # Avoid terms
        avoid_hits = [w for w in self.profile.avoid if w.lower() in lower]
        if avoid_hits:
            issues.append(f"Contains discouraged terms: {', '.join(avoid_hits)}")
            score -= 0.15

        # Preferred vocab
        if self.profile.preferred_vocab:
            used = [w for w in self.profile.preferred_vocab if w.lower() in lower]
            if not used:
                recs.append("Add preferred vocabulary where natural")
                score -= 0.05

        # Length / brevity check for social
        word_count = self.tp.count_words(text)
        if word_count > 250 and self.profile.tone in {"concise", "punchy"}:
            issues.append("Too long for concise voice; tighten wording")
            score -= 0.1

        score = max(0.0, min(1.0, score))
        return VoiceCheckResult(score=score, issues=issues, recommendations=recs)


class BrandVoiceRewriter:
    """Optional LLM-backed rewriter to align content to voice profile."""

    def __init__(self, profile: Optional[BrandVoiceProfile] = None, llm_gateway=None):
        self.profile = profile or BrandVoiceProfile()
        self.llm_gateway = llm_gateway

    async def rewrite(self, text: str, model: str = "gpt-4") -> str:
        if not self.llm_gateway:
            return text
        prompt = (
            "Rewrite the content to match this brand voice. Keep meaning, facts, and length similar. "
            f"Tone: {self.profile.tone}. Formality: {self.profile.formality}. Energy: {self.profile.energy}. "
            f"Use these preferences: {', '.join(self.profile.preferred_vocab) or 'none'}. Avoid: {', '.join(self.profile.avoid) or 'none'}. "
            f"Do not use banned terms: {', '.join(self.profile.banned) or 'none'}. Return the rewritten content only."
        )
        messages = [
            {"role": "system", "content": "You are a precise brand voice editor."},
            {"role": "user", "content": prompt},
            {"role": "user", "content": text},
        ]
        try:
            return await self.llm_gateway.chat(messages=messages, model=model, temperature=0.4, max_tokens=1500)
        except Exception:
            return text


__all__ = [
    "BrandVoiceProfile",
    "BrandVoiceChecker",
    "BrandVoiceRewriter",
    "VoiceCheckResult",
]