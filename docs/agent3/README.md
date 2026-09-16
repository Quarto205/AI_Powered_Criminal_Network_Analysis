# Agent 3 — Standalone Development Environment

This directory contains the prerequisites and tools for developing **Agent 3 (Network Intelligence & Prediction)** in isolation from the rest of the application (Agent 1/2). 

Agent 3 runs complex analytics, including degree, betweenness centrality, community detection, deterministic pattern matching, and optional GATv2 model inference.

## Environment Overview

The standalone environment includes:
- **PostgreSQL 16**: The authoritative system of record for cases, entities, evidence, and analytical results.
- **Neo4j 5.23+ with GDS**: The analytical graph database used by Agent 3 to perform fast traversals and algorithms.
- **Deterministic Dataset**: Synthetic case data representing a criminal network (CASE-A) and background noise (CASE-B) to validate graph topology and models.
- **Israeli Burglary Benchmark Datasets**: Included real-world graph structures for validation under `data/agent3/raw/`:
  1. `israel_lea_inp_burglary_offender_id_network.json`: Directed network of offenders.
  2. `israel_lea_inp_burglary_v2_crime_id_network.json`: Undirected network of crimes with 1386-dimensional textual embeddings.

## Quick Start

### 1. Start the Databases
Ensure you have Docker and Docker Compose installed.
```bash
docker compose up -d
```
This will start PostgreSQL (port 5432) and Neo4j (ports 7474, 7687) locally. It maps data to persistent volumes so you won't lose it between restarts.

### 2. Configure Environment
If you haven't already, ensure your `.env` contains the database credentials.
```bash
cp .env.example .env
```

### 3. Install Dependencies
Agent 3 requires several scientific computing packages. Assuming you have a virtual environment activated:
```bash
pip install -r requirements.txt
```
(Check the `# Agent 3 Analytics` section in `requirements.txt` for specific additions like `networkx`, `torch`, `torch_geometric`).

### 4. Load the Israeli Burglary Dataset
Populate PostgreSQL and project the analytical graph into Neo4j:
```bash
python scripts/load_agent3_dataset.py \
    data/agent3/raw/israel_lea_inp_burglary_offender_id_network.json \
    data/agent3/raw/israel_lea_inp_burglary_v2_crime_id_network.json
```
This script is idempotent (using UUIDv5 and `MERGE`). You can run it multiple times.

### 5. Validate Analytics
Verify that NetworkX and PyTorch Geometric adapters function flawlessly on the actual dataset:
```bash
pytest tests/integration/test_agent3_dataset.py
```

## Resetting Data
If you need to wipe *only* the demo data (CASE-A and CASE-B) without destroying the entire database:
```bash
python scripts/reset_demo.py
```

## Important Development Rules
- **No Global Operations**: Never run `MATCH (n) DETACH DELETE n` in your code. Always scope queries to a dataset_id or case_id.
- **Idempotency**: Analytical queries should use `MERGE` and avoid overwriting source-backed evidence.
- **Authoritative Source**: Neo4j is a rebuildable projection. If a conflict occurs, PostgreSQL is the source of truth.
- **Model Storage**: Store GATv2 predictions in the `predictions` table, and model metadata in `model_runs`. Do not just change a relationship state from `false` to `true`.
