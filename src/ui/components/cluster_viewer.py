"""Cluster visualisation helpers."""
from __future__ import annotations

import streamlit as st


def render_clusters(clusters, recommendations=None) -> None:
    if not clusters:
        st.warning("Clustering has not been run yet.")
        return

    recommendations = recommendations or []
    rec_index = {rec.get("cluster_id"): rec for rec in recommendations}

    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        st.subheader(f"Cluster {cluster_id}")
        st.write(f"Size: {cluster.get('size', 0)}")
        st.write(f"Average confidence: {cluster.get('avg_confidence', 0.0):.2f}")
        st.write("Representative queries:")
        for query in cluster.get("representative_queries", []):
            st.markdown(f"- {query}")

        recommendation = rec_index.get(cluster_id)
        if recommendation:
            st.info(
                f"Suggested expert domain: {recommendation.get('suggested_domain', 'general')}"
            )
            if recommendation.get("should_spawn"):
                st.button("Create Expert", key=f"create_{cluster_id}")
