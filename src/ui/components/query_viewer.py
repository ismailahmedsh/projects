"""Streamlit components for displaying recent queries."""
from __future__ import annotations

import streamlit as st


def render_recent_queries(queries) -> None:
    if not queries:
        st.info("No queries logged yet.")
        return
    for item in queries:
        with st.expander(f"{item['timestamp']} — {item['expert_used']}"):
            st.write(item["query_text"])
            st.caption(f"Confidence: {item['confidence']:.2f}")
