"""Lightweight LoRA training scaffolding for the MVP pipeline."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass
class TrainingMetrics:
    epochs: int
    examples: int
    avg_instruction_length: float
    avg_response_length: float


@dataclass
class LoRATrainer:
    base_model: str
    training_config: Dict[str, object]
    _lora_config: Dict[str, object] = field(default_factory=dict)
    _metrics: TrainingMetrics | None = field(default=None, init=False)

    def configure_lora(self, **overrides: object) -> None:
        config = dict(self.training_config.get("lora", {}))
        config.update(overrides)
        self._lora_config = config

    def prepare_dataset(self, dataset: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
        prepared: List[Dict[str, str]] = []
        for row in dataset:
            instruction = row.get("instruction", "").strip()
            response = row.get("response", "").strip()
            if not instruction or not response:
                continue
            prepared.append({"instruction": instruction, "response": response})
        if not prepared:
            raise ValueError("Dataset must contain at least one instruction/response pair.")
        return prepared

    def train(self, dataset: Iterable[Dict[str, str]], num_epochs: int | None = None) -> TrainingMetrics:
        prepared = self.prepare_dataset(dataset)
        epochs = num_epochs or int(self.training_config.get("training", {}).get("num_epochs", 1))
        avg_instruction = sum(len(row["instruction"]) for row in prepared) / len(prepared)
        avg_response = sum(len(row["response"]) for row in prepared) / len(prepared)
        self._metrics = TrainingMetrics(
            epochs=epochs,
            examples=len(prepared),
            avg_instruction_length=avg_instruction,
            avg_response_length=avg_response,
        )
        return self._metrics

    def save_adapter(self, output_path: str | Path) -> Path:
        if self._metrics is None:
            raise RuntimeError("Cannot save adapter before training has run.")
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "base_model": self.base_model,
            "lora_config": self._lora_config,
            "metrics": self._metrics.__dict__,
        }
        adapter_file = output_dir / "adapter_metadata.json"
        adapter_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return adapter_file

    def get_training_metrics(self) -> TrainingMetrics:
        if self._metrics is None:
            raise RuntimeError("Trainer has not been run yet.")
        return self._metrics
