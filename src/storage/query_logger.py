"""SQLite-backed query logging utilities."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from src.utils.logger import get_logger

logger = get_logger()

SCHEMA_PATH = Path(__file__).with_name("database_schema.sql")


def _ensure_schema(connection: sqlite3.Connection) -> None:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        connection.executescript(handle.read())


class QueryLogger:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        _ensure_schema(self._connection)
        logger.debug("Initialized QueryLogger with database at {}", self.db_path)

    def _hash_query(self, query: str) -> str:
        return hashlib.sha256(query.encode("utf-8")).hexdigest()

    def log_query(
        self,
        query: str,
        *,
        embedding_id: Optional[int],
        expert_used: str,
        confidence: float,
        response: str,
        response_time_ms: int,
    ) -> None:
        query_hash = self._hash_query(query)
        logger.debug("Logging query '{}' routed to '{}'", query[:32], expert_used)
        with self._connection:
            self._connection.execute(
                """
                INSERT OR IGNORE INTO queries (
                    query_text, query_hash, embedding_id, expert_used,
                    confidence, response_text, response_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    query,
                    query_hash,
                    embedding_id,
                    expert_used,
                    confidence,
                    response,
                    response_time_ms,
                ),
            )

    def get_recent_queries(self, limit: int = 20) -> Iterable[Dict[str, Any]]:
        cursor = self._connection.execute(
            "SELECT id, query_text, expert_used, confidence, timestamp "
            "FROM queries ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_queries_for_clustering(self, limit: int | None = None) -> Iterable[Dict[str, Any]]:
        """Return queries with metadata suitable for clustering analysis."""

        query = (
            "SELECT id, query_text, expert_used, confidence, embedding_id "
            "FROM queries ORDER BY id DESC"
        )
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        cursor = self._connection.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self) -> None:
        self._connection.close()
