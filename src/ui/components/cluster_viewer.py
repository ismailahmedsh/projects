"""Placeholder for cluster visualisation."""
from __future__ import annotations

import streamlit as st


def render_clusters(clusters) -> None:
    if not clusters:
        st.warning("Clustering has not been run yet.")
        return
    for cluster in clusters:
        st.subheader(cluster.get("cluster_label", "Unnamed cluster"))
        st.write(f"Size: {cluster.get('size', 0)}")
        st.write(f"Average confidence: {cluster.get('avg_confidence', 0):.2f}")
        st.write("Representative queries:")
        for query in cluster.get("representative_queries", []):
            st.markdown(f"- {query}")
        if cluster.get("needs_expert"):
            st.button("Create Expert", key=f"create_{cluster['cluster_id']}")
