from __future__ import annotations

from src.analysis.clustering import QueryClusterer


def test_clusterer_groups_embeddings():
    embeddings = [
        [1.0, 0.0],
        [0.9, 0.1],
        [0.0, 1.0],
        [0.1, 0.9],
    ]
    queries = ["code", "debug", "science", "biology"]
    clusterer = QueryClusterer(min_cluster_size=2, min_samples=1)
    clusterer.cluster_queries(
        embeddings,
        list(range(len(embeddings))),
        queries=queries,
        confidences=[0.4, 0.45, 0.3, 0.35],
    )
    underserved = clusterer.identify_underserved_clusters(confidence_threshold=0.5)
    assert underserved
    summary = underserved[0]
    assert summary.size >= 2
    assert summary.needs_expert
