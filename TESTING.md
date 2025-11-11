# Phase 2 Human Testing Guide

## What This Tests
Phase 2 introduces intelligent routing (ML-based), expert training scaffolding, and query clustering. This guide helps you manually validate the new features.

## Prerequisites
- Python 3.10+
- All dependencies installed: `pip install -r requirements.txt`
- Phase 2 modules implemented (ML classifier, trainer, clustering)

## Test Scenarios

### Human Test 1: ML Router Accuracy
**What to test:** Does the ML-based router understand query intent better than keywords?

**Steps:**
1. Start dashboard: `python scripts/run_dashboard.py`
2. Type these queries in the sidebar and note expert + confidence:

| Query | Expected Expert | Expected Confidence |
|-------|-----------------|-------------------|
| "How do I write a Python loop?" | code_expert_v1 | > 0.85 |
| "Explain quantum mechanics" | science_expert_v1 | > 0.85 |
| "Write me a sci-fi story" | creative_expert_v1 | > 0.85 |
| "help with coding" | code_expert_v1 | > 0.80 |
| "what's the square root of 16?" | science_expert_v1 | > 0.75 |

**Pass Criteria:** At least 4/5 correct with confidence > 0.75

---

### Human Test 2: Query Logging & Embedding
**What to test:** Does the system correctly log queries and compute embeddings?

**Steps:**
1. Submit 5 queries via dashboard
2. Run: `python scripts/validate_logging.py`
3. Check output:
   - All 5 queries appear in database
   - Each has embedding vector stored (non-null embedding ids if FAISS is used)
   - No duplicate entries

**Pass Criteria:** All queries logged with embeddings

---

### Human Test 3: Clustering Visualization
**What to test:** Can you see query patterns in the dashboard?

**Steps:**
1. Submit 20 diverse queries (mix of code, science, creative)
2. Go to "Clusters" tab in dashboard
3. Verify you see clusters with:
   - Cluster ID
   - Number of queries in cluster
   - Most common expert for that cluster
   - Example queries from cluster

**Pass Criteria:** Clusters are meaningful and coherent

---

### Human Test 4: Expert Training Status
**What to test:** Can you monitor when experts are being fine-tuned?

**Steps:**
1. Go to "Training" tab in dashboard
2. Trigger training: `python scripts/train_expert.py code_expert_v1`
3. Refresh the dashboard and verify the training tab shows:
   - The expert ID
   - Epochs completed
   - Examples processed
   - Average response length from the training metadata

**Pass Criteria:** Training status updates after script completes

---

### Human Test 5: Performance Metrics
**What to test:** Do expert statistics update after queries?

**Steps:**
1. Go to "Experts" tab
2. Note the baseline stats (queries_served, avg_confidence)
3. Submit 10 queries via sidebar
4. Refresh dashboard
5. Check if stats increased:
   - `code_expert_v1` queries served increases for coding queries
   - `science_expert_v1` increases for science queries
   - etc.

**Pass Criteria:** Stats update after each query

---

## Automated Tests

Run all phase 2 tests:
```bash
pytest tests/test_ml_classifier.py -v
pytest tests/test_trainer.py -v
pytest tests/test_clustering.py -v
pytest tests/test_e2e_phase2.py -v
```

## Reporting Issues

If a test fails:
1. Note the test name and step number
2. Run with verbose logging: `LOGLEVEL=DEBUG python scripts/check_<name>.py`
3. Share the error output and which test failed

## Success Criteria for Phase 2

- [ ] ML classifier routes with >0.80 confidence
- [ ] 50+ queries logged with embeddings
- [ ] Clustering finds 2-5 meaningful clusters
- [ ] Expert training completes without errors
- [ ] Dashboard displays all 4 tabs with data
- [ ] All automated tests pass
