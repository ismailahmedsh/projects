"""Command-line utility to run the lightweight LoRA trainer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.models.expert_manager import ExpertManager
from src.training import LoRATrainer, load_training_config


def _load_dataset(path: Path | None, expert_id: str) -> list[dict[str, str]]:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    # Fallback dataset derived from metadata keywords.
    manager = ExpertManager("experts")
    expert = manager.get_expert_by_id(expert_id)
    if expert is None:
        raise ValueError(f"Expert {expert_id} not found in metadata.")
    keywords = (expert.description or expert.domain).split(",")
    dataset: list[dict[str, str]] = []
    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue
        dataset.append(
            {
                "instruction": f"Explain the concept of {keyword}",
                "response": f"Detailed explanation for {keyword} (placeholder).",
            }
        )
    if not dataset:
        raise ValueError("Unable to derive dataset from metadata; provide --dataset.")
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lightweight LoRA trainer")
    parser.add_argument("expert_id", help="Expert identifier to train")
    parser.add_argument(
        "--dataset",
        type=Path,
        help="Path to JSON dataset with instruction/response pairs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experts"),
        help="Directory where adapter metadata will be stored",
    )
    args = parser.parse_args()

    config = load_training_config()
    trainer = LoRATrainer(base_model="llama-3.2", training_config=config)
    trainer.configure_lora()
    dataset = _load_dataset(args.dataset, args.expert_id)
    metrics = trainer.train(dataset)
    output_dir = args.output / args.expert_id
    metadata_file = trainer.save_adapter(output_dir)
    print("Training complete", metrics)
    print("Adapter metadata:", metadata_file)


if __name__ == "__main__":
    main()
