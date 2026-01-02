from __future__ import annotations

from typing import Dict

from src.utils import TextProcessor

class ContentQualityChecker:
    """Basic quality checks: readability and keyword density."""

    def __init__(self):
        self.tp = TextProcessor()

    def assess(self, text: str, keywords: list[str] | None = None) -> Dict[str, float]:
        readability = self.tp.calculate_readability_score(text)
        word_count = self.tp.count_words(text)
        keywords = keywords or []
        density = {kw: round(text.lower().count(kw.lower()) / max(word_count, 1) * 100, 3) for kw in keywords}
        return {
            "readability": readability,
            "word_count": word_count,
            "keyword_density": density,
        }
