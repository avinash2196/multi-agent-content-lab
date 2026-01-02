from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time


@dataclass
class ImageEntry:
    url: str
    prompt: str
    aspect_ratio: str
    created: float
    provider: str = "openai"
    model: str = "dall-e-3"
    alt_text: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class ImageManager:
    """In-memory image store with optional alt text enrichment."""

    def __init__(self):
        self.store: Dict[str, List[ImageEntry]] = {}

    def add_images(
        self,
        key: str,
        urls: List[str],
        prompt: str,
        aspect_ratio: str,
        created: float,
        provider: str = "openai",
        model: str = "dall-e-3",
    ) -> List[ImageEntry]:
        entries: List[ImageEntry] = []
        for url in urls:
            entry = ImageEntry(
                url=url,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                created=created or time.time(),
                provider=provider,
                model=model,
            )
            entries.append(entry)
        self.store.setdefault(key, []).extend(entries)
        return entries

    def list_images(self, key: str) -> List[ImageEntry]:
        return list(self.store.get(key, []))

    def set_alt_text(self, key: str, url: str, alt_text: str) -> bool:
        for entry in self.store.get(key, []):
            if entry.url == url:
                entry.alt_text = alt_text
                return True
        return False

    def primary(self, key: str) -> Optional[ImageEntry]:
        images = self.store.get(key, [])
        return images[0] if images else None

    async def enrich_alt_text(
        self,
        key: str,
        llm_gateway: Any,
        model: str = "gpt-4o-mini",
        max_chars: int = 120,
    ) -> List[ImageEntry]:
        """Generate alt text for images lacking it using the provided LLM gateway."""
        if not llm_gateway:
            return self.list_images(key)

        images = self.store.get(key, [])
        for entry in images:
            if entry.alt_text:
                continue
            prompt = (
                f"Write concise alt text (<= {max_chars} chars) for an image described as: {entry.prompt}. "
                f"Aspect ratio: {entry.aspect_ratio}. Keep factual and specific."
            )
            messages = [
                {"role": "system", "content": "You generate concise, factual alt text."},
                {"role": "user", "content": prompt},
            ]
            try:
                alt = await llm_gateway.chat(messages=messages, model=model, temperature=0.2, max_tokens=80)
                if alt:
                    entry.alt_text = alt.strip()
            except Exception:
                continue
        return images


__all__ = ["ImageManager", "ImageEntry"]