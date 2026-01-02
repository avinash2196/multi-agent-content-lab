from __future__ import annotations

from typing import List, Dict, Any
import logging

from src.services.serp_service import SearchResult


class ResearchSynthesizer:
    """Aggregate and synthesize research from multiple sources."""

    def __init__(self):
        self.logger = logging.getLogger("research_synthesizer")

    def deduplicate_sources(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate links while preserving order."""
        seen = set()
        unique_results: List[SearchResult] = []
        for res in results:
            if res.link in seen:
                continue
            seen.add(res.link)
            unique_results.append(res)
        return unique_results

    def credibility_scores(self, results: List[SearchResult]) -> Dict[str, float]:
        """Naive credibility scoring based on domain heuristics."""
        scores: Dict[str, float] = {}
        for res in results:
            domain = self._extract_domain(res.link)
            base_score = 0.6
            if any(domain.endswith(tld) for tld in [".edu", ".gov"]):
                base_score = 0.9
            elif "wikipedia" in domain:
                base_score = 0.7
            elif any(domain.endswith(tld) for tld in [".org"]):
                base_score = 0.75
            scores[res.link] = base_score
        return scores

    def synthesize(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Produce a structured synthesis with key points and sources."""
        if not results:
            return {"summary": "No results found.", "key_points": [], "sources": []}

        unique = self.deduplicate_sources(results)
        scores = self.credibility_scores(unique)

        key_points = []
        for res in unique:
            snippet = res.snippet or res.title
            if not snippet:
                continue
            key_points.append(f"{res.title}: {snippet}")

        sources = [res.to_dict() | {"credibility": scores.get(res.link, 0.6)} for res in unique]

        summary = self._generate_summary(key_points)
        return {
            "summary": summary,
            "key_points": key_points[:5],
            "sources": sources,
        }

    def _generate_summary(self, key_points: List[str]) -> str:
        if not key_points:
            return "No key points available."
        if len(key_points) == 1:
            return key_points[0]
        return " ".join(key_points[:3])

    def _extract_domain(self, url: str) -> str:
        if "//" in url:
            return url.split("//", 1)[1].split("/", 1)[0]
        return url.split("/", 1)[0]
