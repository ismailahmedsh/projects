"""Run the Streamlit dashboard."""
from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    dashboard_path = project_root / "src" / "ui" / "dashboard.py"
    subprocess.run(["streamlit", "run", str(dashboard_path)], check=False)


if __name__ == "__main__":
    main()
