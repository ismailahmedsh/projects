"""Helpers for loading training configuration from YAML."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import yaml
except ModuleNotFoundError:  # pragma: no cover - allow fallback
    yaml = None  # type: ignore


DEFAULT_CONFIG: Dict[str, Any] = {
    "lora": {
        "r": 16,
        "alpha": 32,
        "dropout": 0.1,
        "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    },
    "training": {
        "learning_rate": 0.0002,
        "num_epochs": 3,
        "batch_size": 4,
        "gradient_accumulation_steps": 4,
        "warmup_steps": 100,
        "max_length": 512,
        "fp16": True,
        "optimizer": "paged_adamw_8bit",
    },
}


def load_training_config(path: str | Path | None = None) -> Dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "training_config.yaml"
    config_path = Path(path)
    if yaml is None:
        return DEFAULT_CONFIG.copy()
    if not config_path.exists():
        raise FileNotFoundError(f"Training config not found at {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
