from __future__ import annotations

from pathlib import Path

from src.analysis.clustering import QueryClusterer
from src.models.expert_manager import ExpertManager
from src.router.classifier import RouterClassifier
from src.router.router import QueryRouter
from src.storage.query_logger import QueryLogger


class DummyEmbeddingModel:
    def encode(self, text):
        text = text.lower()
        return [
            1.0 if "code" in text else 0.0,
            1.0 if "science" in text else 0.0,
            1.0 if "story" in text else 0.0,
        ]

    def batch_encode(self, texts):
        return [self.encode(text) for text in texts]


def test_end_to_end_router_logging_and_clustering(tmp_path):
    experts_dir = tmp_path / "experts"
    experts_dir.mkdir()
    metadata = {
        "experts": [
            {
                "expert_id": "code",
                "domain": "code",
                "description": "programming",
                "adapter_path": "code",
            },
            {
                "expert_id": "science",
                "domain": "science",
                "description": "physics",
                "adapter_path": "science",
            },
        ]
    }
    (experts_dir / "metadata.json").write_text(__import__("json").dumps(metadata))
    manager = ExpertManager(experts_dir)

    classifier = RouterClassifier(embedding_model=DummyEmbeddingModel())
    router = QueryRouter(classifier, manager, confidence_threshold=0.6)
    router.retrain_classifier(samples_per_keyword=1)

    db_path = tmp_path / "queries.db"
    logger = QueryLogger(db_path)

    queries = [
        "Help with code bug",
        "Explain physics homework",
        "Another coding question",
    ]
    for query in queries:
        result = router.route_query(query)
        logger.log_query(
            query,
            embedding_id=None,
            expert_used=result.expert_id,
            confidence=result.confidence,
            response="demo",
            response_time_ms=100,
        )

    recent = list(logger.get_recent_queries())
    embeddings = [classifier.embedding_model.encode(row["query_text"]) for row in recent]
    clusterer = QueryClusterer(min_cluster_size=1, min_samples=1)
    clusterer.cluster_queries(
        embeddings,
        [row["id"] for row in recent],
        queries=[row["query_text"] for row in recent],
        confidences=[float(row["confidence"] or 0.0) for row in recent],
    )
    distribution = clusterer.cluster_distribution()
    assert sum(distribution.values()) == len(recent)
