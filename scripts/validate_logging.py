"""Utility script to inspect recently logged queries."""
from __future__ import annotations

import json
from pathlib import Path

from src.storage.query_logger import QueryLogger


def main() -> None:
    db_path = Path("data/queries.db")
    logger = QueryLogger(db_path)
    recent = list(logger.get_recent_queries(limit=10))
    print(json.dumps(recent, indent=2, default=str))
    logger.close()


if __name__ == "__main__":
    main()
