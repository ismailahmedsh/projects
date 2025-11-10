CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    query_hash TEXT UNIQUE,
    embedding_id INTEGER,
    expert_used TEXT,
    confidence FLOAT,
    response_text TEXT,
    response_time_ms INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_feedback INTEGER
);

CREATE TABLE IF NOT EXISTS clusters (
    cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_label TEXT,
    size INTEGER,
    avg_confidence FLOAT,
    representative_queries TEXT,
    needs_expert BOOLEAN DEFAULT FALSE,
    expert_created TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expert_performance (
    expert_id TEXT,
    date DATE,
    queries_count INTEGER,
    avg_confidence FLOAT,
    avg_response_time_ms INTEGER,
    PRIMARY KEY (expert_id, date)
);
