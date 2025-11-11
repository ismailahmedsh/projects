# Dynamic Expert System

This repository contains the foundations for a self-expanding expert routing system. The current MVP focuses on the initial infrastructure required to load a base model, register LoRA experts, run an embedding-powered router, surface clustering insights, and expose a Streamlit monitoring dashboard.

## Project Structure

The project follows a modular layout under `src/`:

- `src/models/` – base model and expert management utilities.
- `src/router/` – embedding model helpers, classifier, and router orchestration.
- `src/storage/` – SQLite logging and FAISS vector index helpers.
- `src/analysis/` – clustering and pattern detection utilities.
- `src/training/` – lightweight LoRA trainer scaffold and evaluation helpers.
- `src/ui/` – Streamlit dashboard and reusable components.
- `src/utils/` – shared helpers such as logging configuration.

Configuration files live in `config/`, while runtime data is stored in `data/` and LoRA adapters in `experts/`.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure logging and environment variables as needed (see `.env.example` when available).
3. Launch the monitoring dashboard:
   ```bash
   python scripts/run_dashboard.py
   ```

The dashboard wires up an embedding classifier that maps queries to the three seed experts defined in `experts/metadata.json`. Logged queries are persisted to `data/queries.db` using SQLite, while the cluster and training tabs surface insights from recent interactions.

## Next Steps

The foundation is ready for Phase 2 and Phase 3 enhancements:

- Expand the clustering engine with richer visualisations.
- Plug the lightweight LoRA trainer into a real model fine-tuning flow.
- Implement research, automated deployment workflows, and API endpoints.

Contributions and iterations should build on the modular abstractions introduced in this commit.

## Helpful scripts

The `scripts/` directory provides quick validation commands:

- `python scripts/check_ml_classifier.py` – exercise the embedding router using a lightweight embedding model.
- `python scripts/check_clustering.py` – run the query clustering pipeline with sample data.
- `python scripts/check_trainer.py` – execute the LoRA trainer scaffold and emit metrics.
- `python scripts/check_e2e_phase2.py` – smoke test routing, logging, and clustering end-to-end.
- `python scripts/train_expert.py <expert_id>` – generate synthetic training data from metadata and persist adapter metadata.
