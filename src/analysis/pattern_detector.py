"""Utilities for deriving insights from clustered queries."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .clustering import ClusterSummary


def _tokenise(text: str) -> List[str]:
    return [token for token in text.lower().split() if token]


@dataclass
class PatternRecommendation:
    """Recommendation for spawning or updating an expert."""

    cluster_id: int
    suggested_domain: str
    representative_queries: List[str]
    should_spawn: bool


class PatternDetector:
    def __init__(self, min_examples: int = 5, confidence_threshold: float = 0.6) -> None:
        self.min_examples = min_examples
        self.confidence_threshold = confidence_threshold

    def detect_new_patterns(
        self, cluster_summaries: Sequence[ClusterSummary]
    ) -> List[PatternRecommendation]:
        recommendations: List[PatternRecommendation] = []
        for summary in cluster_summaries:
            suggested_domain = self.recommend_expert_domain(summary.representative_queries)
            should_spawn = self.check_spawn_criteria(summary)
            recommendations.append(
                PatternRecommendation(
                    cluster_id=summary.cluster_id,
                    suggested_domain=suggested_domain,
                    representative_queries=summary.representative_queries,
                    should_spawn=should_spawn,
                )
            )
        return recommendations

    def analyze_cluster_topics(self, cluster_queries: Iterable[str], top_k: int = 5) -> List[str]:
        counter: Counter[str] = Counter()
        for query in cluster_queries:
            counter.update(_tokenise(query))
        return [token for token, _ in counter.most_common(top_k)]

    def recommend_expert_domain(self, cluster_queries: Iterable[str]) -> str:
        keywords = self.analyze_cluster_topics(cluster_queries, top_k=3)
        if not keywords:
            return "general"
        return "_".join(keywords)

    def check_spawn_criteria(self, summary: ClusterSummary) -> bool:
        return (
            summary.size >= self.min_examples
            and summary.avg_confidence < self.confidence_threshold
        )
