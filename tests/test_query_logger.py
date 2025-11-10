from __future__ import annotations

from src.storage.query_logger import QueryLogger


def test_query_logger_inserts_and_reads(tmp_path):
    db_path = tmp_path / "queries.db"
    logger = QueryLogger(db_path)

    logger.log_query(
        "Hello world",
        embedding_id=1,
        expert_used="base",
        confidence=0.5,
        response="Hi",
        response_time_ms=100,
    )

    results = list(logger.get_recent_queries())
    assert len(results) == 1
    assert results[0]["expert_used"] == "base"
    logger.close()
