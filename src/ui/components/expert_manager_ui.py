"""Expert management UI helpers."""
from __future__ import annotations

import streamlit as st


def render_expert_overview(experts) -> None:
    if not experts:
        st.info("No experts registered yet.")
        return
    for expert in experts:
        with st.expander(expert["expert_id"]):
            st.write(expert["description"])
            st.write(f"Domain: {expert['domain']}")
            st.write(f"Queries served: {expert['queries_served']}")
            if expert.get("avg_confidence") is not None:
                st.write(f"Average confidence: {expert['avg_confidence']:.2f}")
