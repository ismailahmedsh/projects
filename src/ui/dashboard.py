from __future__ import annotations

import json

import streamlit as st

from src.analysis.clustering import QueryClusterer
from src.analysis.pattern_detector import PatternDetector
from src.models.expert_manager import ExpertManager
from src.router.classifier import RouterClassifier
from src.router.embedding_model import EmbeddingModel
from src.router.router import QueryRouter
from src.storage.query_logger import QueryLogger
from src.ui.components.cluster_viewer import render_clusters
from src.ui.components.expert_manager_ui import render_expert_overview
from src.ui.components.query_viewer import render_recent_queries
from src.ui.components.training_monitor import render_training_status


def main() -> None:
    st.set_page_config(page_title="Dynamic Expert System", layout="wide")
    st.title("Dynamic Expert System Dashboard")

    expert_manager = ExpertManager("experts")
    embedding_model = EmbeddingModel()
    classifier = RouterClassifier(embedding_model=embedding_model)
    router = QueryRouter(classifier, expert_manager)
    try:
        router.retrain_classifier(samples_per_keyword=3)
    except Exception as exc:  # pragma: no cover - UI safeguard
        st.warning(f"Router classifier training skipped: {exc}")
    query_logger = QueryLogger("data/queries.db")

    clustering_summaries = []
    pattern_recommendations = []
    try:
        recent_queries = query_logger.get_queries_for_clustering(limit=200)
        if recent_queries:
            embeddings = [embedding_model.encode(row["query_text"]) for row in recent_queries]
            clusterer = QueryClusterer()
            clusterer.cluster_queries(
                embeddings,
                [row["id"] for row in recent_queries],
                queries=[row["query_text"] for row in recent_queries],
                confidences=[float(row["confidence"] or 0.0) for row in recent_queries],
            )
            underserved = clusterer.identify_underserved_clusters()
            clustering_summaries = [summary.__dict__ for summary in underserved]
            detector = PatternDetector()
            pattern_recommendations = [
                {
                    "cluster_id": rec.cluster_id,
                    "suggested_domain": rec.suggested_domain,
                    "should_spawn": rec.should_spawn,
                    "representative_queries": rec.representative_queries,
                }
                for rec in detector.detect_new_patterns(underserved)
            ]
    except Exception as exc:  # pragma: no cover - surface to UI
        st.warning(f"Clustering unavailable: {exc}")

    with st.sidebar:
        st.header("Router")
        user_query = st.text_area("Enter a query", height=150)
        if st.button("Route query") and user_query:
            result = router.route_query(user_query)
            st.success(f"Expert: {result.expert_id} (confidence {result.confidence:.2f})")
            st.caption(result.explanation)

    tab_query, tab_experts, tab_clusters, tab_training = st.tabs(
        ["Queries", "Experts", "Clusters", "Training"]
    )

    with tab_query:
        st.subheader("Recent queries")
        render_recent_queries(query_logger.get_recent_queries())

    with tab_experts:
        st.subheader("Expert overview")
        render_expert_overview(expert_manager.get_expert_stats())

    with tab_clusters:
        st.subheader("Cluster analysis")
        render_clusters(clustering_summaries, pattern_recommendations)

    with tab_training:
        st.subheader("Training monitor")
        render_training_status(_load_training_history(expert_manager))


def _load_training_history(expert_manager: ExpertManager):
    history = []
    for expert in expert_manager.list_experts():
        metadata_path = expert.adapter_path / "adapter_metadata.json"
        if metadata_path.exists():
            try:
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            metrics = payload.get("metrics", {})
            history.append(
                {
                    "id": expert.expert_id,
                    "epochs": metrics.get("epochs", 0),
                    "examples": metrics.get("examples", 0),
                    "avg_response_length": metrics.get("avg_response_length", 0.0),
                }
            )
    return history


if __name__ == "__main__":
    main()
