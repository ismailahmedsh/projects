"""FAISS-based vector storage."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np

try:  # pragma: no cover - optional dependency
    import faiss
except Exception:  # pragma: no cover
    faiss = None  # type: ignore


class VectorStore:
    def __init__(self, dimension: int = 384, index_path: str | Path = "data/embeddings.faiss") -> None:
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self._index = None
        self._next_id = 0
        self._load_index()

    def _load_index(self) -> None:
        if self.index_path.exists() and faiss is not None:
            self._index = faiss.read_index(str(self.index_path))  # type: ignore[arg-type]
            self._next_id = self._index.ntotal
        elif faiss is not None:
            self._index = faiss.IndexFlatIP(self.dimension)
        else:
            self._index = None

    def add_embedding(self, embedding: Iterable[float]) -> int:
        vector = np.array([list(embedding)], dtype="float32")
        if faiss is None:
            raise RuntimeError("FAISS is not available. Install faiss-cpu to use VectorStore.")
        if self._index is None:
            self._index = faiss.IndexFlatIP(self.dimension)
        self._index.add(vector)
        embedding_id = self._next_id
        self._next_id += 1
        return embedding_id

    def search_similar(self, embedding: Iterable[float], k: int = 5) -> List[Tuple[int, float]]:
        if faiss is None or self._index is None:
            raise RuntimeError("FAISS index not available for similarity search.")
        vector = np.array([list(embedding)], dtype="float32")
        distances, indices = self._index.search(vector, k)
        return [(int(idx), float(dist)) for idx, dist in zip(indices[0], distances[0])]

    def save_index(self) -> None:
        if faiss is None or self._index is None:
            return
        faiss.write_index(self._index, str(self.index_path))  # type: ignore[arg-type]
