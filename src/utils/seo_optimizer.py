from __future__ import annotations

from typing import List, Dict
import re

class SEOOptimizer:
    """Lightweight SEO helper for keyword placement and meta data."""

    def __init__(self, primary_keywords: List[str] | None = None):
        self.primary_keywords = [k.lower() for k in (primary_keywords or [])]

    def generate_meta_description(self, text: str, max_len: int = 155) -> str:
        snippet = text.strip().replace('\n', ' ')
        if len(snippet) <= max_len:
            return snippet
        cutoff = snippet[: max_len - 3].rsplit(' ', 1)[0]
        return f"{cutoff}..."

    def embed_keywords(self, text: str) -> str:
        """Ensure primary keywords appear; append if missing."""
        lower = text.lower()
        missing = [kw for kw in self.primary_keywords if kw not in lower]
        if not missing:
            return text
        addition = "\n\nKeywords: " + ", ".join(missing)
        return text + addition

    def keyword_density(self, text: str) -> Dict[str, float]:
        words = re.findall(r"\b\w+\b", text.lower())
        total = max(len(words), 1)
        density: Dict[str, float] = {}
        for kw in self.primary_keywords:
            count = text.lower().count(kw)
            density[kw] = round((count / total) * 100, 3)
        return density

    def make_slug(self, title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
        return slug.strip('-')
