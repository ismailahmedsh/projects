"""Training monitor UI component."""
from __future__ import annotations

import streamlit as st


def render_training_status(jobs) -> None:
    if not jobs:
        st.info("No training jobs running.")
        return
    for job in jobs:
        st.write(f"Job {job['id']}: epoch {job['epoch']} / {job['total_epochs']}")
        st.progress(job.get("progress", 0.0))
