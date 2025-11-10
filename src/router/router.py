"""Query routing orchestration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.utils.logger import get_logger

from .classifier import RouterClassifier
from src.models.expert_manager import ExpertManager


@dataclass
class RoutingResult:
    expert_id: str
    confidence: float
    explanation: str


class QueryRouter:
    def __init__(
        self,
        classifier: RouterClassifier,
        expert_manager: ExpertManager,
        confidence_threshold: float = 0.7,
    ) -> None:
        self.classifier = classifier
        self.expert_manager = expert_manager
        self.confidence_threshold = confidence_threshold
        self._logger = get_logger()

    def route_query(self, query: str) -> RoutingResult:
        expert_id, confidence = self.classifier.predict(query)
        self._logger.debug(
            "Classifier suggested expert '{}' with confidence {}", expert_id, confidence
        )

        if confidence < self.confidence_threshold or expert_id == "base":
            explanation = "Routed to base model due to low confidence."
            return RoutingResult("base", confidence, explanation)

        expert = self.expert_manager.get_expert_by_id(expert_id)
        if expert is None:
            self._logger.warning(
                "Expert '{}' not found. Falling back to base model.", expert_id
            )
            return RoutingResult("base", confidence, "Expert unavailable; fallback to base model")

        explanation = f"Keyword match routed query to expert '{expert.domain}'."
        return RoutingResult(expert_id, confidence, explanation)

    def get_routing_explanation(self, query: str) -> str:
        result = self.route_query(query)
        return result.explanation

    def update_experts(self, keyword_mapping: Dict[str, str]) -> None:
        self.classifier.keyword_map = keyword_mapping
        self._logger.info("Updated router keyword mapping: {}", keyword_mapping)

    def retrain_classifier(self, *_args, **_kwargs) -> None:  # pragma: no cover - stub
        self._logger.warning("Retraining is not implemented for the rule-based router.")
