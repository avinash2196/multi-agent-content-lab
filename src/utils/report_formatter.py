from __future__ import annotations

from typing import List, Dict


class ReportFormatter:
    """Format research outputs into structured Markdown."""

    def format_research_report(
        self,
        topic: str,
        summary: str,
        key_points: List[str],
        sources: List[Dict],
    ) -> str:
        lines = [f"# Research Report: {topic}", "", "## Summary", summary or "No summary available."]

        if key_points:
            lines.extend(["", "## Key Findings", *[f"- {point}" for point in key_points]])

        if sources:
            lines.extend(["", "## Sources"])
            for src in sources:
                title = src.get("title", "Untitled")
                link = src.get("link", "")
                snippet = src.get("snippet", "")
                cred = src.get("credibility")
                cred_str = f" (credibility: {cred:.2f})" if cred is not None else ""
                lines.append(f"- [{title}]({link}) — {snippet}{cred_str}")

        return "\n".join(lines)
