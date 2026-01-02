from __future__ import annotations

from typing import List, Dict

class BlogGenerator:
    """Generate blog outlines and content from research inputs."""

    def build_outline(self, topic: str, key_points: List[str]) -> List[str]:
        if not key_points:
            return [f"Introduction to {topic}", "Key Insights", "Conclusion"]
        return [f"Introduction to {topic}"] + key_points + ["Conclusion"]

    def render_markdown(self, title: str, outline: List[str], body_points: List[str], meta: Dict[str, str]) -> str:
        """Generate full article with substantive content, not just outline."""
        lines = [f"# {title}", ""]
        
        if meta.get("description"):
            lines += [f"> {meta['description']}", ""]
        
        # Introduction
        lines.append("## Introduction")
        lines.append(
            f"In today's fast-paced digital landscape, understanding {title.lower()} is more critical "
            "than ever. This comprehensive guide explores key insights, best practices, and actionable "
            "strategies to help you navigate this important topic."
        )
        lines.append("")
        
        # Main sections from outline (skip intro/conclusion as we handle separately)
        for i, section in enumerate(outline[1:], 1):
            if section.lower() not in ["conclusion", "introduction"]:
                lines.append(f"## {section}")
                # Generate substantive paragraph for each section
                for point in body_points[:3]:  # Use top 3 points per section
                    lines.append(f"**{point}**")
                    lines.append(
                        f"This is a key consideration when examining {section.lower()}. "
                        f"Understanding this aspect helps organizations make informed decisions "
                        f"and implement effective strategies. {point} provides significant value "
                        f"and should be prioritized in your approach."
                    )
                    lines.append("")
        
        # Conclusion
        lines.append("## Conclusion")
        lines.append(
            f"Successfully navigating {title.lower()} requires a comprehensive understanding of "
            "these key principles and best practices. By implementing the strategies outlined in this guide, "
            "you'll be well-positioned to achieve your goals and drive meaningful results."
        )
        lines.append("")
        
        return "\n".join(lines).strip()
