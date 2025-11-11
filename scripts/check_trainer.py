"""Manual smoke test for the LoRA trainer scaffold."""
from __future__ import annotations

from pathlib import Path

from src.training import LoRATrainer, load_training_config


SAMPLE_DATASET = [
    {
        "instruction": "Provide python code to add two numbers",
        "response": "def add(a, b):\n    return a + b",
    },
    {
        "instruction": "Explain Newton's second law",
        "response": "Force equals mass times acceleration.",
    },
]


def main() -> None:
    config = load_training_config()
    trainer = LoRATrainer(base_model="llama-3.2", training_config=config)
    trainer.configure_lora()
    metrics = trainer.train(SAMPLE_DATASET)
    adapter_path = Path("experts/demo_adapter")
    metadata_file = trainer.save_adapter(adapter_path)
    print("Training metrics:", metrics)
    print("Adapter metadata saved to:", metadata_file)


if __name__ == "__main__":
    main()
