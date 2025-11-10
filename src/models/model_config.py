"""Helpers for loading model configuration from YAML files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class GenerationConfig:
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9


@dataclass
class QuantizationConfig:
    load_in_8bit: bool = True
    device_map: str = "auto"


@dataclass
class ModelConfig:
    model_name: str
    quantization: QuantizationConfig
    generation: GenerationConfig

    @classmethod
    def from_file(cls, path: str | Path) -> "ModelConfig":
        data = _load_yaml(path)
        quant = data.get("quantization", {})
        gen = data.get("generation", {})
        return cls(
            model_name=data.get("default_model", "meta-llama/Meta-Llama-3-8B-Instruct"),
            quantization=QuantizationConfig(
                load_in_8bit=bool(quant.get("load_in_8bit", True)),
                device_map=str(quant.get("device_map", "auto")),
            ),
            generation=GenerationConfig(
                max_new_tokens=int(gen.get("max_new_tokens", 512)),
                temperature=float(gen.get("temperature", 0.7)),
                top_p=float(gen.get("top_p", 0.9)),
            ),
        )


def _load_yaml(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
