"""Query clustering utilities for identifying emerging topics."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - keep optional
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import hdbscan  # type: ignore
except Exception:  # pragma: no cover
    hdbscan = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from sklearn.cluster import KMeans  # type: ignore
except Exception:  # pragma: no cover
    KMeans = None  # type: ignore


@dataclass
class ClusterSummary:
    """Lightweight description of a discovered query cluster."""

    cluster_id: int
    size: int
    avg_confidence: float
    query_ids: List[int]
    representative_queries: List[str]
    needs_expert: bool = False


class QueryClusterer:
    """Run clustering over query embeddings with graceful fallbacks."""

    def __init__(self, min_cluster_size: int = 5, min_samples: int = 3) -> None:
        self.min_cluster_size = max(2, min_cluster_size)
        self.min_samples = max(1, min_samples)
        self._cluster_labels: List[int] | None = None
        self._embeddings: Sequence[Sequence[float]] | None = None
        self._query_ids: Sequence[int] | None = None
        self._queries: Sequence[str] | None = None
        self._confidences: Sequence[float] | None = None

    def cluster_queries(
        self,
        embeddings: Sequence[Sequence[float]],
        query_ids: Sequence[int],
        *,
        queries: Sequence[str] | None = None,
        confidences: Sequence[float] | None = None,
    ) -> Mapping[int, List[int]]:
        if len(embeddings) != len(query_ids):
            raise ValueError("Embeddings and query_ids must have matching lengths.")
        if not embeddings:
            self._cluster_labels = []
            self._embeddings = []
            self._query_ids = []
            self._queries = queries or []
            self._confidences = confidences or []
            return {}

        labels = self._run_clustering(embeddings)
        assignments: MutableMapping[int, List[int]] = defaultdict(list)
        for idx, label in enumerate(labels):
            if label < 0:
                # HDBSCAN uses -1 for noise; we skip those from summaries.
                continue
            assignments[int(label)].append(int(query_ids[idx]))

        self._cluster_labels = [int(label) for label in labels]
        self._embeddings = embeddings
        self._query_ids = query_ids
        self._queries = queries or [""] * len(query_ids)
        if confidences is not None:
            self._confidences = confidences
        else:
            self._confidences = [0.0] * len(query_ids)

        return assignments

    def _run_clustering(self, embeddings: Sequence[Sequence[float]]) -> List[int]:
        if np is not None:
            vectors = np.asarray(embeddings, dtype=float)
        else:
            vectors = embeddings

        if (
            hdbscan is not None
            and np is not None
            and len(embeddings) >= self.min_cluster_size
        ):  # pragma: no cover - exercised when hdbscan installed
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
            )
            labels = clusterer.fit_predict(vectors)
            return [int(label) for label in labels]

        if KMeans is not None and len(embeddings) >= 2:
            n_clusters = min(max(1, len(embeddings) // self.min_cluster_size), len(embeddings))
            if n_clusters == 1 and len(embeddings) >= self.min_cluster_size:
                n_clusters = 2
            kmeans = KMeans(n_clusters=n_clusters, n_init="auto", random_state=42)
            labels = kmeans.fit_predict(vectors)
            return [int(label) for label in labels]

        # Fallback: assign everything to a single cluster.
        return [0 for _ in embeddings]

    def get_cluster_summary(self, cluster_id: int) -> ClusterSummary:
        if self._cluster_labels is None or self._query_ids is None:
            raise RuntimeError("No clustering results available. Call cluster_queries first.")

        indices = [
            idx
            for idx, label in enumerate(self._cluster_labels)
            if label == cluster_id and idx < len(self._query_ids)
        ]
        if not indices:
            raise KeyError(f"Cluster {cluster_id} not found in latest clustering run.")

        confidences = [self._confidences[idx] for idx in indices] if self._confidences else []
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        representative_queries: List[str] = []
        if self._queries:
            for idx in indices[:5]:
                query_text = self._queries[idx]
                if query_text:
                    representative_queries.append(query_text)

        return ClusterSummary(
            cluster_id=cluster_id,
            size=len(indices),
            avg_confidence=avg_conf,
            query_ids=[int(self._query_ids[idx]) for idx in indices],
            representative_queries=representative_queries,
        )

    def identify_underserved_clusters(
        self,
        confidence_threshold: float = 0.6,
        *,
        min_size: Optional[int] = None,
    ) -> List[ClusterSummary]:
        if self._cluster_labels is None:
            return []

        summaries: List[ClusterSummary] = []
        observed_clusters = {label for label in self._cluster_labels if label >= 0}
        for label in observed_clusters:
            summary = self.get_cluster_summary(label)
            size_threshold = min_size or self.min_cluster_size
            if summary.size >= size_threshold and summary.avg_confidence < confidence_threshold:
                summary.needs_expert = True
                summaries.append(summary)
        return summaries

    def visualise_clusters(self) -> Dict[str, Sequence]:
        """Return cluster embeddings and labels for downstream visualisation."""

        if self._cluster_labels is None or self._embeddings is None:
            return {"embeddings": [], "labels": []}
        return {"embeddings": self._embeddings, "labels": self._cluster_labels}

    def cluster_distribution(self) -> Mapping[int, int]:
        if self._cluster_labels is None:
            return {}
        counts: MutableMapping[int, int] = Counter()
        for label in self._cluster_labels:
            if label >= 0:
                counts[int(label)] += 1
        return dict(counts)
