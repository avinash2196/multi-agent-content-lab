from __future__ import annotations

from typing import List
import re


class HashtagEngine:
    """Generate simple, topic-based hashtags."""

    def __init__(self, max_length: int = 25):
        self.max_length = max_length

    def generate(self, topic: str, key_points: List[str] | None = None, count: int = 5) -> List[str]:
        # Build token pool from topic + key points to keep hashtags relevant
        texts: List[str] = []
        if topic:
            texts.append(topic)
        if key_points:
            texts.extend(key_points)

        tokens: List[str] = []
        for t in texts:
            tokens.extend(self._tokenize(t))

        # Deduplicate while preserving order
        seen_tokens = set()
        ordered_tokens: List[str] = []
        for tok in tokens:
            if tok not in seen_tokens:
                seen_tokens.add(tok)
                ordered_tokens.append(tok)

        hashtags: List[str] = []
        for token in ordered_tokens:
            tag = f"#{token[: self.max_length]}"
            if len(tag) > 1 and tag not in hashtags:  # Check for duplicates
                hashtags.append(tag)
            if len(hashtags) >= count:
                break

        # Curated fallbacks to pad when not enough relevant tags
        curated = ["insights", "strategy", "innovation", "ai", "trends", "growth", "leadership", "research"]
        for tag in curated:
            if len(hashtags) >= count:
                break
            candidate = f"#{tag}" if not tag.startswith("#") else tag
            if candidate not in hashtags:
                hashtags.append(candidate[: self.max_length + 1])

        return hashtags[:count]

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        tokens = []
        for w in words:
            if len(w) < 3:
                continue
            tokens.append(w)
        # Add combined tokens for specificity
        if len(tokens) >= 2:
            tokens.append("".join(tokens[:2]))
        return tokens
