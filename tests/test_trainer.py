from __future__ import annotations

from src.training import LoRATrainer, ModelEvaluator, load_training_config


DATASET = [
    {"instruction": "Summarise python lists", "response": "Lists hold ordered data."},
    {"instruction": "Explain gravity", "response": "Gravity pulls objects together."},
]


def test_trainer_produces_metrics(tmp_path):
    config = load_training_config()
    trainer = LoRATrainer(base_model="llama", training_config=config)
    trainer.configure_lora()
    metrics = trainer.train(DATASET, num_epochs=2)
    assert metrics.examples == 2
    metadata_path = trainer.save_adapter(tmp_path / "adapter")
    assert metadata_path.exists()


def test_evaluator_reports_improvement():
    evaluator = ModelEvaluator(base_model="llama")
    metrics = evaluator.evaluate_on_test_set(DATASET)
    assert metrics.avg_response_length > 0
    assert evaluator.check_quality_threshold(min_improvement=-1.0)
    report = evaluator.generate_evaluation_report()
    assert "Evaluation Report" in report
