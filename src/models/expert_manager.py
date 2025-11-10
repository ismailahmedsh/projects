"""Management utilities for expert adapters."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.utils.logger import get_logger

logger = get_logger()

from .expert import Expert


class ExpertManager:
    def __init__(self, experts_dir: str | Path) -> None:
        self.experts_dir = Path(experts_dir)
        self.metadata_file = self.experts_dir / "metadata.json"
        self._experts: Dict[str, Expert] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        if not self.metadata_file.exists():
            logger.warning("Expert metadata file not found at {}", self.metadata_file)
            return
        with self.metadata_file.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        for entry in data.get("experts", []):
            expert = Expert(
                expert_id=entry["expert_id"],
                domain=entry.get("domain", "unknown"),
                description=entry.get("description", ""),
                adapter_path=self.experts_dir / Path(entry.get("adapter_path", "")),
                metadata=entry,
            )
            self._experts[expert.expert_id] = expert
            logger.debug("Registered expert '{}'", expert.expert_id)

    def list_experts(self) -> Iterable[Expert]:
        return self._experts.values()

    def get_expert_by_id(self, expert_id: str) -> Optional[Expert]:
        return self._experts.get(expert_id)

    def register_new_expert(self, expert_config: Dict[str, any]) -> Expert:
        expert = Expert(
            expert_id=expert_config["expert_id"],
            domain=expert_config.get("domain", "unknown"),
            description=expert_config.get("description", ""),
            adapter_path=self.experts_dir / Path(expert_config.get("adapter_path", "")),
            metadata=expert_config,
        )
        self._experts[expert.expert_id] = expert
        self._persist_metadata()
        logger.info("Registered new expert '{}'", expert.expert_id)
        return expert

    def _persist_metadata(self) -> None:
        data = {"experts": [exp.metadata for exp in self._experts.values()]}
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with self.metadata_file.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def get_expert_stats(self) -> List[Dict[str, any]]:
        return [exp.get_metadata() for exp in self._experts.values()]
