"""Query routing orchestration."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List

from src.models.expert import Expert
from src.models.expert_manager import ExpertManager
from src.utils.logger import get_logger

from .classifier import RouterClassifier


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
            explanation = "Routed to base model due to low classifier confidence."
            return RoutingResult("base", confidence, explanation)

        expert = self.expert_manager.get_expert_by_id(expert_id)
        if expert is None:
            self._logger.warning(
                "Expert '{}' not found. Falling back to base model.", expert_id
            )
            return RoutingResult(
                "base", confidence, "Expert unavailable; fallback to base model"
            )

        explanation = (
            f"Embedding classifier matched query to expert '{expert.domain}' with confidence"
            f" {confidence:.2f}."
        )
        return RoutingResult(expert_id, confidence, explanation)

    def get_routing_explanation(self, query: str) -> str:
        result = self.route_query(query)
        return result.explanation

    def retrain_classifier(self, samples_per_keyword: int = 5) -> None:
        """Retrain the classifier using metadata-derived training prompts."""

        training_corpus = self._build_training_corpus(samples_per_keyword)
        if not training_corpus or len(training_corpus) <= 1:
            self._logger.warning("Not enough training data generated for router classifier.")
            return
        self.classifier.train(training_corpus)
        self._logger.info("Router classifier retrained with %d classes.", len(training_corpus))

    def _build_training_corpus(self, samples_per_keyword: int) -> Dict[str, List[str]]:
        experts = list(self.expert_manager.list_experts())
        corpus: Dict[str, List[str]] = {}

        for expert in experts:
            keywords = self._extract_keywords(expert)
            if not keywords:
                continue
            corpus[expert.expert_id] = self._generate_prompts(keywords, samples_per_keyword)

        # Include a generic base class to help the classifier recognise off-domain queries.
        corpus["base"] = [
            "Hello, how are you?",
            "Tell me something interesting.",
            "What's the weather like?",
            "Share a fun fact.",
            "Write a friendly greeting.",
        ]
        return corpus

    @staticmethod
    def _extract_keywords(expert: Expert) -> Iterable[str]:
        text = f"{expert.domain} {expert.description}".lower()
        keywords = {
            token
            for token in re.split(r"[^a-z0-9_]+", text)
            if token and len(token) > 2
        }
        return keywords

    @staticmethod
    def _generate_prompts(keywords: Iterable[str], samples_per_keyword: int) -> List[str]:
        templates = [
            "I have a question about {keyword}.",
            "Can you explain {keyword}?",
            "Need help with {keyword} topic.",
        ]
        prompts: List[str] = []
        for keyword in keywords:
            for index in range(samples_per_keyword):
                template = templates[index % len(templates)]
                prompts.append(template.format(keyword=keyword))
        return prompts
