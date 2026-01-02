from __future__ import annotations

from typing import List, Dict


class LinkedInFormatter:
    """Format LinkedIn posts with hook, body, CTA, and hashtags."""

    def format_post(
        self,
        hook: str,
        body_lines: List[str],
        cta: str,
        hashtags: List[str],
        max_chars: int = 1200,
    ) -> Dict[str, str]:
        lines = [hook.strip(), ""]
        lines.extend([line.strip() for line in body_lines if line.strip()])
        if cta:
            lines.append("")
            lines.append(cta.strip())
        if hashtags:
            lines.append("")
            lines.append(" ".join(hashtags))

        post = "\n".join(lines).strip()
        if len(post) > max_chars:
            post = post[: max_chars - 3].rsplit(" ", 1)[0] + "..."
        return {"text": post, "length": len(post)}
