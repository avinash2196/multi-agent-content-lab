from __future__ import annotations

from typing import Dict


class PromptOptimizer:
    """Simple prompt optimizer for image generation prompts."""

    def optimize(self, description: str, style: str | None = None, context: str | None = None) -> str:
        parts = [description.strip()]
        if style:
            parts.append(f"Style: {style}")
        if context:
            parts.append(f"Context: {context}")
        parts.append("High quality, detailed, coherent, well-lit")
        return " | ".join([p for p in parts if p])
