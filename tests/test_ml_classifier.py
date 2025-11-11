from __future__ import annotations

from src.router.classifier import RouterClassifier


class DummyEmbeddingModel:
    def encode(self, text):
        text = text.lower()
        return [
            1.0 if "code" in text else 0.0,
            1.0 if "science" in text else 0.0,
            1.0 if "story" in text else 0.0,
        ]

    def batch_encode(self, texts):
        return [self.encode(text) for text in texts]


def test_router_classifier_trains_and_predicts():
    classifier = RouterClassifier(embedding_model=DummyEmbeddingModel())
    training_corpus = {
        "code": ["Help with code"],
        "science": ["science homework"],
        "creative": ["tell me a story"],
    }
    classifier.train(training_corpus)

    expert, confidence = classifier.predict("Need help with science project")
    assert expert == "science"
    assert confidence > 0.5
