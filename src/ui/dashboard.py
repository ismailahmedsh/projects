"""Streamlit dashboard entry point."""
from __future__ import annotations

import streamlit as st

from src.models.expert_manager import ExpertManager
from src.router.classifier import RouterClassifier
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
    classifier = RouterClassifier(
        keyword_map={
            "code": "code_expert_v1",
            "program": "code_expert_v1",
            "science": "science_expert_v1",
            "physics": "science_expert_v1",
            "story": "creative_expert_v1",
            "write": "creative_expert_v1",
        }
    )
    router = QueryRouter(classifier, expert_manager)
    query_logger = QueryLogger("data/queries.db")

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
        render_clusters([])  # Placeholder until clustering implemented

    with tab_training:
        st.subheader("Training monitor")
        render_training_status([])


if __name__ == "__main__":
    main()
