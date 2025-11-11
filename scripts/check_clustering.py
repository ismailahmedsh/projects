"""Manual clustering validation script."""
from __future__ import annotations

import json

from src.analysis.clustering import QueryClusterer


EMBEDDINGS = [
    [1.0, 0.0, 0.0],
    [0.9, 0.1, 0.0],
    [0.0, 1.0, 0.1],
    [0.0, 0.9, 0.2],
]
QUERIES = ["Write python code", "debugging tips", "explain gravity", "physics homework"]
CONFIDENCES = [0.5, 0.55, 0.4, 0.42]


def main() -> None:
    clusterer = QueryClusterer(min_cluster_size=2, min_samples=1)
    clusterer.cluster_queries(
        EMBEDDINGS,
        list(range(len(EMBEDDINGS))),
        queries=QUERIES,
        confidences=CONFIDENCES,
    )
    underserved = clusterer.identify_underserved_clusters(confidence_threshold=0.6)
    summaries = [summary.__dict__ for summary in underserved]
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
