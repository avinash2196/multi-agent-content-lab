from __future__ import annotations

from typing import List, Dict
import re


class SEOOptimizer:
    """Lightweight utility for basic on-page SEO tasks.

    Purpose:
        After the blog writer produces article text, this class handles small
        but important SEO hygiene tasks: ensuring target keywords appear in the
        body, generating a meta description, computing keyword density, and
        producing a URL-safe slug.

    How it fits into the system:
        ``BlogWriterAgent`` owns an ``SEOOptimizer`` instance and calls it
        after LLM generation to apply keyword embedding and produce metadata
        (slug, meta description) that would be needed by a CMS.

    Simplification for learning:
        Real SEO tools (e.g., Yoast, Surfer SEO) perform semantic analysis,
        TF-IDF scoring against competitor pages, structured data injection, and
        more.  This class only covers deterministic string operations so the
        logic stays readable and unit-testable without mocking.

    Args:
        primary_keywords: List of keywords to track and potentially inject
            into generated content.
    """

    def __init__(self, primary_keywords: List[str] | None = None):
        self.primary_keywords = [k.lower() for k in (primary_keywords or [])]

    def generate_meta_description(self, text: str, max_len: int = 155) -> str:
        """Truncate ``text`` to a search-engine-friendly meta description length.

        Google truncates meta descriptions at roughly 155–160 characters.
        We truncate at the last word boundary before that limit to avoid
        cutting words mid-way.
        """
        snippet = text.strip().replace('\n', ' ')
        if len(snippet) <= max_len:
            return snippet
        cutoff = snippet[: max_len - 3].rsplit(' ', 1)[0]
        return f"{cutoff}..."

    def embed_keywords(self, text: str) -> str:
        """Ensure primary keywords appear in the text; append missing ones.

        If the LLM already used the keyword naturally, nothing changes.
        Otherwise a keyword footer is appended.  This is a simplified approach
        — a production tool would inject keywords into headings or existing
        sentences.
        """
        lower = text.lower()
        missing = [kw for kw in self.primary_keywords if kw not in lower]
        if not missing:
            return text
        addition = "\n\nKeywords: " + ", ".join(missing)
        return text + addition

    def keyword_density(self, text: str) -> Dict[str, float]:
        """Return the density (as a percentage) of each primary keyword in ``text``."""
        words = re.findall(r"\b\w+\b", text.lower())
        total = max(len(words), 1)
        density: Dict[str, float] = {}
        for kw in self.primary_keywords:
            count = text.lower().count(kw)
            density[kw] = round((count / total) * 100, 3)
        return density

    def make_slug(self, title: str) -> str:
        """Convert a title string into a lowercase URL-safe slug.

        Example: "AI in Healthcare: Trends" → "ai-in-healthcare-trends"
        """
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
        return slug.strip('-')
