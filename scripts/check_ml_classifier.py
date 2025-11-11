"""Manual validation script for the ML-based router classifier."""
from __future__ import annotations

import json
from pathlib import Path

from src.models.expert_manager import ExpertManager
from src.router.classifier import RouterClassifier
from src.router.embedding_model import EmbeddingModel
from src.router.router import QueryRouter


class _DemoEmbeddingModel(EmbeddingModel):
    """Avoid loading heavy models during manual validation."""

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


SAMPLE_QUERIES = {
    "code_expert_v1": ["How do I write a python loop?"],
    "science_expert_v1": ["Explain quantum mechanics"],
    "creative_expert_v1": ["Write a sci-fi story"],
}


def main() -> None:
    experts_dir = Path("experts")
    metadata_path = experts_dir / "metadata.json"
    if not metadata_path.exists():
        raise SystemExit("metadata.json not found. Run from repository root.")

    manager = ExpertManager(experts_dir)
    classifier = RouterClassifier(embedding_model=_DemoEmbeddingModel())
    router = QueryRouter(classifier, manager, confidence_threshold=0.6)
    router.retrain_classifier(samples_per_keyword=1)

    results = []
    for expected_expert, queries in SAMPLE_QUERIES.items():
        for query in queries:
            routed = router.route_query(query)
            results.append(
                {
                    "query": query,
                    "expected": expected_expert,
                    "predicted": routed.expert_id,
                    "confidence": routed.confidence,
                }
            )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
