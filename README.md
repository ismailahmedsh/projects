# Dynamic Expert System

This repository contains the foundations for a self-expanding expert routing system. The current MVP focuses on the initial infrastructure required to load a base model, register LoRA experts, route queries, and expose a Streamlit monitoring dashboard.

## Project Structure

The project follows a modular layout under `src/`:

- `src/models/` – base model and expert management utilities.
- `src/router/` – keyword-based routing logic, ready to be upgraded to ML routing.
- `src/storage/` – SQLite logging and FAISS vector index helpers.
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

The dashboard currently wires up a rule-based router that maps keyword patterns to the three seed experts defined in `experts/metadata.json`. Logged queries are persisted to `data/queries.db` using SQLite.

## Next Steps

The foundation is ready for Phase 2 and Phase 3 enhancements:

- Replace the rule-based router with an embedding + classifier pipeline.
- Implement clustering, research, training automation, and deployment workflows.
- Expand Streamlit dashboards to surface clusters, training jobs, and automated insights.

Contributions and iterations should build on the modular abstractions introduced in this commit.
