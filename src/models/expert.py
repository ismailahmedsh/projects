"""Expert adapter representation."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class Expert:
    expert_id: str
    domain: str
    description: str
    adapter_path: Path
    metadata: Dict[str, Any] = field(default_factory=dict)
    queries_served: int = 0
    avg_confidence: Optional[float] = None

    def load_adapter(self, base_model: Any) -> None:  # pragma: no cover - thin wrapper
        if base_model is None:
            raise ValueError("Base model must be provided to load an adapter.")
        logger.debug("Loading adapter '{}' from {}", self.expert_id, self.adapter_path)
        if hasattr(base_model, "load_adapter"):
            base_model.load_adapter(str(self.adapter_path))
        else:
            logger.warning(
                "Base model object does not expose 'load_adapter'; skipping actual load for {}",
                self.expert_id,
            )

    def unload_adapter(self, base_model: Any) -> None:  # pragma: no cover - thin wrapper
        if base_model is None:
            return
        if hasattr(base_model, "unload_adapter"):
            base_model.unload_adapter(str(self.adapter_path))
            logger.debug("Adapter '{}' unloaded", self.expert_id)

    def update_stats(self, *, query_count: int, confidence: Optional[float]) -> None:
        self.queries_served += query_count
        if confidence is not None:
            if self.avg_confidence is None:
                self.avg_confidence = confidence
            else:
                self.avg_confidence = (self.avg_confidence + confidence) / 2
        logger.debug(
            "Updated stats for expert '{}': queries_served={}, avg_confidence={}",
            self.expert_id,
            self.queries_served,
            self.avg_confidence,
        )

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "expert_id": self.expert_id,
            "domain": self.domain,
            "description": self.description,
            "adapter_path": str(self.adapter_path),
            "metadata": self.metadata,
            "queries_served": self.queries_served,
            "avg_confidence": self.avg_confidence,
        }
