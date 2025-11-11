from __future__ import annotations

from src.models.expert_manager import ExpertManager
from src.router.classifier import RouterClassifier
from src.router.router import QueryRouter


class DummyEmbeddingModel:
    def encode(self, text):
        return [1.0 if "code" in text.lower() else 0.0, 1.0 if "science" in text.lower() else 0.0]

    def batch_encode(self, texts):
        return [self.encode(text) for text in texts]


def test_embedding_classifier_routing(tmp_path):
    experts_dir = tmp_path / "experts"
    experts_dir.mkdir()
    metadata = {
        "experts": [
            {
                "expert_id": "code_expert_v1",
                "domain": "programming",
                "description": "software code development",
                "adapter_path": "code_expert_v1",
            },
            {
                "expert_id": "science_expert_v1",
                "domain": "science",
                "description": "physics and biology",
                "adapter_path": "science_expert_v1",
            },
        ]
    }
    (experts_dir / "metadata.json").write_text(__import__("json").dumps(metadata))

    manager = ExpertManager(experts_dir)
    classifier = RouterClassifier(embedding_model=DummyEmbeddingModel())
    router = QueryRouter(classifier, manager, confidence_threshold=0.6)
    router.retrain_classifier(samples_per_keyword=2)

    code_result = router.route_query("Can you help me debug this code snippet?")
    assert code_result.expert_id == "code_expert_v1"
    assert code_result.confidence >= 0.6

    science_result = router.route_query("Explain this science concept")
    assert science_result.expert_id == "science_expert_v1"
    assert science_result.confidence >= 0.6

    fallback_result = router.route_query("Good morning!")
    assert fallback_result.expert_id == "base"
