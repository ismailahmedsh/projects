from __future__ import annotations

from src.models.expert_manager import ExpertManager
from src.router.classifier import RouterClassifier
from src.router.router import QueryRouter


def test_keyword_routing(tmp_path):
    experts_dir = tmp_path / "experts"
    experts_dir.mkdir()
    metadata = {
        "experts": [
            {
                "expert_id": "code_expert_v1",
                "domain": "programming",
                "description": "",
                "adapter_path": "code_expert_v1",
            }
        ]
    }
    (experts_dir / "metadata.json").write_text(__import__("json").dumps(metadata))

    manager = ExpertManager(experts_dir)
    classifier = RouterClassifier(keyword_map={"code": "code_expert_v1"})
    router = QueryRouter(classifier, manager, confidence_threshold=0.6)

    result = router.route_query("Can you help me with some code?")
    assert result.expert_id == "code_expert_v1"
    assert result.confidence >= 0.6
