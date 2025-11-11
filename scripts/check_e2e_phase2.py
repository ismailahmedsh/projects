"""End-to-end smoke test covering routing, logging, and clustering."""
from __future__ import annotations

import json
from pathlib import Path

from src.analysis.clustering import QueryClusterer
from src.models.expert_manager import ExpertManager
from src.router.classifier import RouterClassifier
from src.router.embedding_model import EmbeddingModel
from src.router.router import QueryRouter
from src.storage.query_logger import QueryLogger


class _DemoEmbeddingModel(EmbeddingModel):
    def __init__(self) -> None:  # pragma: no cover - simple override
        super().__init__(model_name="demo")
        self._model = None

    def encode(self, text: str):  # type: ignore[override]
        text_lower = text.lower()
        return [
            1.0 if "code" in text_lower else 0.0,
            1.0 if "science" in text_lower else 0.0,
            1.0 if "story" in text_lower else 0.0,
        ]

    def batch_encode(self, texts):  # type: ignore[override]
        return [self.encode(text) for text in texts]


QUERIES = [
    "Can you help me debug python code?",
    "Explain the theory of relativity",
    "Write a whimsical story about space",
    "How do I fix a bug in JavaScript?",
]


def main() -> None:
    experts_dir = Path("experts")
    manager = ExpertManager(experts_dir)
    classifier = RouterClassifier(embedding_model=_DemoEmbeddingModel())
    router = QueryRouter(classifier, manager, confidence_threshold=0.6)
    router.retrain_classifier(samples_per_keyword=1)

    db_path = Path("data/e2e_queries.db")
    logger = QueryLogger(db_path)

    routed = []
    for query in QUERIES:
        result = router.route_query(query)
        routed.append(result.__dict__)
        logger.log_query(
            query,
            embedding_id=None,
            expert_used=result.expert_id,
            confidence=result.confidence,
            response="demo",
            response_time_ms=100,
        )

    recent = list(logger.get_recent_queries())
    embeddings = [_DemoEmbeddingModel().encode(row["query_text"]) for row in recent]
    clusterer = QueryClusterer(min_cluster_size=2, min_samples=1)
    clusterer.cluster_queries(
        embeddings,
        [row["id"] for row in recent],
        queries=[row["query_text"] for row in recent],
        confidences=[float(row["confidence"] or 0.0) for row in recent],
    )
    underserved = [summary.__dict__ for summary in clusterer.identify_underserved_clusters()]

    print(json.dumps({"routed": routed, "clusters": underserved}, indent=2))


if __name__ == "__main__":
    main()
