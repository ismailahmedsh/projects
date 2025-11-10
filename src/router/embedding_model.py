"""Sentence embedding utilities."""
from __future__ import annotations

from typing import Iterable, List

try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - handle gracefully when dependency missing
    SentenceTransformer = None  # type: ignore


class EmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is None:
            if SentenceTransformer is None:
                raise RuntimeError(
                    "sentence-transformers is not installed. Install dependencies to use embeddings."
                )
            self._model = SentenceTransformer(self.model_name)

    def encode(self, text: str) -> List[float]:
        self._ensure_model()
        return list(self._model.encode(text, convert_to_numpy=True))  # type: ignore[operator]

    def batch_encode(self, texts: Iterable[str]) -> List[List[float]]:
        self._ensure_model()
        return [list(vec) for vec in self._model.encode(list(texts), convert_to_numpy=True)]  # type: ignore[operator]
