"""Training monitor UI component."""
from __future__ import annotations

import streamlit as st


def render_training_status(jobs) -> None:
    if not jobs:
        st.info("No training jobs running.")
        return
    for job in jobs:
        st.write(
            f"Expert {job.get('id')}: epochs {job.get('epochs', 0)}, examples {job.get('examples', 0)}"
        )
        avg_length = job.get("avg_response_length", 0.0)
        if avg_length:
            st.caption(f"Average response length: {avg_length:.1f} characters")
