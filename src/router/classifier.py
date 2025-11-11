"""Machine-learning based router classifier implementation."""
from __future__ import annotations

import math
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:  # pragma: no cover - optional dependency
    import numpy as _np
except ModuleNotFoundError:  # pragma: no cover - executed when numpy missing
    _np = None

try:  # pragma: no cover - optional dependency
    from sklearn.linear_model import LogisticRegression as _SklearnLogisticRegression
    from sklearn.preprocessing import LabelEncoder as _SklearnLabelEncoder
except ModuleNotFoundError:  # pragma: no cover - executed when sklearn missing
    _SklearnLogisticRegression = None
    _SklearnLabelEncoder = None

try:  # pragma: no cover - optional dependency
    from joblib import dump, load
except ModuleNotFoundError:  # pragma: no cover - executed when joblib missing
    def dump(obj, path):
        with Path(path).open("wb") as handle:
            pickle.dump(obj, handle)

    def load(path):
        with Path(path).open("rb") as handle:
            return pickle.load(handle)

from src.router.embedding_model import EmbeddingModel


def _to_float_vector(vector: Sequence[float]) -> List[float]:
    return [float(value) for value in vector]


def _argmax(values: Sequence[float]) -> int:
    best_index = 0
    best_value = values[0]
    for index, value in enumerate(values[1:], start=1):
        if value > best_value:
            best_index = index
            best_value = value
    return best_index


def _softmax(values: Sequence[float]) -> List[float]:
    if not values:
        return []
    max_value = max(values)
    exp_values = [math.exp(value - max_value) for value in values]
    total = sum(exp_values)
    if total == 0:
        return [1.0 / len(exp_values) for _ in exp_values]
    return [value / total for value in exp_values]


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    numerator = sum(x * y for x, y in zip(a, b))
    denom_a = math.sqrt(sum(x * x for x in a))
    denom_b = math.sqrt(sum(y * y for y in b))
    if denom_a == 0.0 or denom_b == 0.0:
        return 0.0
    return numerator / (denom_a * denom_b)


class _FallbackLabelEncoder:
    def __init__(self) -> None:
        self.classes_: List[str] = []
        self._index: Dict[str, int] = {}

    def fit(self, labels: Sequence[str]) -> "_FallbackLabelEncoder":
        self._index = {}
        self.classes_ = []
        for label in labels:
            if label not in self._index:
                self._index[label] = len(self._index)
                self.classes_.append(label)
        return self

    def fit_transform(self, labels: Sequence[str]) -> List[int]:
        self.fit(labels)
        return [self._index[label] for label in labels]

    def inverse_transform(self, indices: Sequence[int]) -> List[str]:
        return [self.classes_[int(index)] for index in indices]


class _FallbackClassifier:
    """Simple centroid-based classifier used when sklearn is unavailable."""

    def __init__(self, scale: float = 5.0) -> None:
        self.centroids: Dict[int, List[float]] = {}
        self.classes_: List[int] = []
        self._scale = scale

    def fit(self, embeddings: Sequence[Sequence[float]], targets: Sequence[int]) -> None:
        if not embeddings:
            raise ValueError("No embeddings provided for fallback classifier training.")

        dimension = len(embeddings[0])
        sums: Dict[int, List[float]] = {}
        counts: Dict[int, int] = {}

        for vector, label in zip(embeddings, targets):
            vector_floats = _to_float_vector(vector)
            if label not in sums:
                sums[label] = [0.0] * dimension
                counts[label] = 0
            sums[label] = [acc + value for acc, value in zip(sums[label], vector_floats)]
            counts[label] += 1

        self.classes_ = list(sums.keys())
        self.centroids = {
            label: [value / counts[label] for value in sums[label]]
            for label in self.classes_
        }

    def predict_proba(self, embeddings: Sequence[Sequence[float]]) -> List[List[float]]:
        probabilities: List[List[float]] = []
        for vector in embeddings:
            vector_floats = _to_float_vector(vector)
            if not self.classes_:
                probabilities.append([1.0])
                continue
            scores = [
                _cosine_similarity(vector_floats, self.centroids[label])
                for label in self.classes_
            ]
            scaled = [score * self._scale for score in scores]
            probabilities.append(_softmax(scaled))
        return probabilities


def _create_label_encoder(use_sklearn: bool):
    if use_sklearn and _SklearnLabelEncoder is not None and _np is not None:  # pragma: no cover - sklearn path
        return _SklearnLabelEncoder()
    return _FallbackLabelEncoder()


@dataclass
class RouterClassifier:
    """Classifier that routes queries to experts using embeddings."""

    embedding_model: EmbeddingModel
    default_expert: str = "base"
    max_iter: int = 1000
    multi_class: str = "auto"
    _model: object | None = field(default=None, init=False, repr=False)
    _label_encoder: object | None = field(default=None, init=False, repr=False)
    _use_sklearn: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._use_sklearn = (
            _SklearnLogisticRegression is not None
            and _SklearnLabelEncoder is not None
            and _np is not None
        )

    def predict(self, query: str) -> Tuple[str, float]:
        """Predict the best expert for the supplied query."""

        if self._model is None or self._label_encoder is None:
            return self.default_expert, 0.0

        embedding = self.embedding_model.encode(query)
        if self._use_sklearn:
            assert _np is not None  # Narrow type for type-checkers
            embedding_array = _np.asarray(embedding).reshape(1, -1)
            probabilities = self._model.predict_proba(embedding_array)[0]
            best_index = int(_np.argmax(probabilities))
        else:
            probabilities = self._model.predict_proba([embedding])[0]
            best_index = _argmax(probabilities)

        expert_id = str(self._label_encoder.inverse_transform([best_index])[0])
        confidence = float(probabilities[best_index])
        return expert_id, confidence

    def train(self, training_corpus: Dict[str, Iterable[str]]) -> None:
        """Train the classifier from a corpus of labelled example queries."""

        texts: List[str] = []
        labels: List[str] = []

        for expert_id, examples in training_corpus.items():
            for example in examples:
                cleaned = example.strip()
                if not cleaned:
                    continue
                texts.append(cleaned)
                labels.append(expert_id)

        if not texts:
            raise ValueError("Training corpus is empty; cannot train router classifier.")

        embeddings = self.embedding_model.batch_encode(texts)
        label_encoder = _create_label_encoder(self._use_sklearn)
        targets = label_encoder.fit_transform(labels)

        if len(getattr(label_encoder, "classes_", [])) < 2:
            raise ValueError("Router classifier requires at least two distinct classes.")

        if self._use_sklearn:
            assert _np is not None and _SklearnLogisticRegression is not None
            model = _SklearnLogisticRegression(max_iter=self.max_iter, multi_class=self.multi_class)
            model.fit(_np.asarray(embeddings), targets)
        else:
            model = _FallbackClassifier()
            model.fit([_to_float_vector(vec) for vec in embeddings], targets)

        self._model = model
        self._label_encoder = label_encoder

    def save(self, path: str | Path) -> None:
        """Persist the trained classifier to disk."""

        if self._model is None or self._label_encoder is None:
            raise ValueError("Cannot save an untrained router classifier.")

        if self._use_sklearn:
            classes = getattr(self._label_encoder, "classes_")
        else:
            classes = list(getattr(self._label_encoder, "classes_", []))

        payload = {
            "model": self._model,
            "classes": classes,
            "default_expert": self.default_expert,
            "max_iter": self.max_iter,
            "multi_class": self.multi_class,
            "use_sklearn": self._use_sklearn,
        }
        dump(payload, Path(path))

    @classmethod
    def load(cls, path: str | Path, embedding_model: EmbeddingModel) -> "RouterClassifier":
        """Load a previously persisted classifier."""

        payload = load(Path(path))
        classifier = cls(
            embedding_model=embedding_model,
            default_expert=payload.get("default_expert", "base"),
            max_iter=payload.get("max_iter", 1000),
            multi_class=payload.get("multi_class", "auto"),
        )

        use_sklearn_payload = bool(payload.get("use_sklearn", classifier._use_sklearn))
        classifier._use_sklearn = (
            use_sklearn_payload
            and _SklearnLogisticRegression is not None
            and _SklearnLabelEncoder is not None
            and _np is not None
        )

        classifier._model = payload["model"]
        if classifier._use_sklearn:
            label_encoder = _SklearnLabelEncoder()
            assert _np is not None
            label_encoder.classes_ = _np.asarray(payload["classes"])
        else:
            label_encoder = _FallbackLabelEncoder()
            classes = list(payload.get("classes", []))
            label_encoder.classes_ = classes
            label_encoder._index = {label: idx for idx, label in enumerate(classes)}

        classifier._label_encoder = label_encoder
        return classifier
