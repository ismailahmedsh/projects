"""Simple evaluation helpers for trained experts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class EvaluationMetrics:
    avg_response_length: float
    avg_instruction_length: float
    improvement: float


class ModelEvaluator:
    def __init__(self, base_model: str, expert_adapter: str | None = None) -> None:
        self.base_model = base_model
        self.expert_adapter = expert_adapter
        self._metrics: EvaluationMetrics | None = None

    def evaluate_on_test_set(self, test_data: Iterable[Dict[str, str]]) -> EvaluationMetrics:
        instructions: List[str] = []
        responses: List[str] = []
        for row in test_data:
            instructions.append(row.get("instruction", ""))
            responses.append(row.get("response", ""))
        if not instructions:
            raise ValueError("Test data must include at least one sample.")
        avg_instr = sum(len(text) for text in instructions) / len(instructions)
        avg_resp = sum(len(text) for text in responses) / len(responses)
        # Improvement is a simple heuristic comparing response length to instruction length.
        improvement = (avg_resp - avg_instr) / max(avg_instr, 1.0)
        self._metrics = EvaluationMetrics(
            avg_response_length=avg_resp,
            avg_instruction_length=avg_instr,
            improvement=improvement,
        )
        return self._metrics

    def compare_to_base_model(self, base_metrics: EvaluationMetrics) -> float:
        if self._metrics is None:
            raise RuntimeError("Run evaluate_on_test_set before comparing metrics.")
        return self._metrics.improvement - base_metrics.improvement

    def check_quality_threshold(self, min_improvement: float = 0.15) -> bool:
        if self._metrics is None:
            raise RuntimeError("No evaluation metrics computed yet.")
        return self._metrics.improvement >= min_improvement

    def generate_evaluation_report(self) -> str:
        if self._metrics is None:
            raise RuntimeError("No evaluation metrics available for report generation.")
        return (
            f"Evaluation Report\n"
            f"Base model: {self.base_model}\n"
            f"Adapter: {self.expert_adapter or 'N/A'}\n"
            f"Average instruction length: {self._metrics.avg_instruction_length:.1f}\n"
            f"Average response length: {self._metrics.avg_response_length:.1f}\n"
            f"Improvement score: {self._metrics.improvement:.3f}"
        )
