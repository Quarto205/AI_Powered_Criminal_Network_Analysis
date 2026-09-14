# SIH26189 — AI-Powered Criminal Network Analysis System

An investigation-support and decision-support platform designed for authorized investigators to perform provenance-aware, case-centric criminal network analysis.

---

## ⚠️ Important Synthetic Data Disclaimer

This system is demonstrated using **deterministic synthetic data**. 
- Synthetic data is **NEVER** presented as live operational police CDR, IPDR, or banking records.
- Research benchmark results (e.g., AMLSim, Elliptic) serve solely for algorithmic validation and are **NEVER** claimed as proprietary operational results.
- AI predictions and graph analytics provide investigative leads; they **DO NOT** independently determine guilt, criminality, or replace judicial standards of evidence.

---

## 🏛 System Architecture

The project follows a **modular monolith + asynchronous background worker** architecture:
- **PostgreSQL**: Authoritative relational system-of-record (cases, entities, physical evidence, audit logs).
- **Neo4j**: Analytical graph projection (idempotent projection of PostgreSQL state for graph traversal).
- **Frontend**: React + TypeScript + Cytoscape.js (interactive bounded neighborhood exploration).
- **AI/ML Engine**:
  - **Agent 1**: Extraction engine for unstructured text.
  - **Agent 2**: Entity resolution and normalization.
  - **Agent 3**: Social Network Analysis (SNA) metrics + GATv2 link-prediction / association scoring.

---

## 📁 Repository Structure

```text
.
├── apps/
│   ├── api/                 # FastAPI HTTP application (/api/v1/)
│   └── web/                 # React + TypeScript + Cytoscape.js frontend
├── backend/
│   ├── config/              # Centralized environment configuration
│   ├── domain/              # Core business entities and domain models
│   ├── jobs/                # Asynchronous Celery/worker tasks
│   ├── repositories/        # PostgreSQL and Neo4j data access layer
│   ├── schemas/             # Pydantic schemas and serialization models
│   └── services/            # Domain service workflows
├── agents/
│   ├── extraction/          # Agent 1: NLP and entity extraction
│   ├── evidence/            # Agent 2: Resolution & evidence corroboration
│   └── intelligence/        # Agent 3: SNA and link prediction
├── ml/
│   ├── datasets/            # Synthetic training and evaluation datasets
│   ├── models/              # GATv2 PyG model definitions
│   └── training/            # Link prediction training scripts
├── docs/
│   ├── contracts/           # Canonical shared contracts (01-10)
│   ├── DOCUMENT_CONSISTENCY_REPORT.md
│   └── system-architecture.md
├── scripts/                 # Maintenance, seeding, and graph projection scripts
├── tests/                   # Contract, unit, integration, and security tests
├── AGENTS.md                # AI coding agent constitution and strict rules
├── .env.example             # Environment configuration template (SEC-001)
└── .gitignore               # Secret and artifact exclusion rules
```

---

## 📜 Canonical Contracts (`docs/contracts/`)

All development across Frontend, Backend, and AI/ML is governed by the 10 canonical contracts:
1. [`01_SHARED_TYPES.md`](docs/contracts/01_SHARED_TYPES.md): Master UUIDv4, lifecycle states, confidence semantics.
2. [`02_DATABASE_SCHEMA.md`](docs/contracts/02_DATABASE_SCHEMA.md): Authoritative PostgreSQL schema.
3. [`03_GRAPH_SCHEMA.md`](docs/contracts/03_GRAPH_SCHEMA.md): Neo4j graph vocabulary and projection rules.
4. [`04_API_SPEC.md`](docs/contracts/04_API_SPEC.md): REST API endpoints and envelope format `{ success, data, error, request_id }`.
5. [`05_AI_CONTRACTS.md`](docs/contracts/05_AI_CONTRACTS.md): Extraction, resolution, and link prediction interfaces.
6. [`06_WORKFLOWS.md`](docs/contracts/06_WORKFLOWS.md): Asynchronous ingestion, validation, and degraded modes.
7. [`07_AUTH_SECURITY.md`](docs/contracts/07_AUTH_SECURITY.md): RBAC, JWT format, and case isolation.
8. [`08_UI_DATA_CONTRACT.md`](docs/contracts/08_UI_DATA_CONTRACT.md): Cytoscape.js visual invariants (solid vs dashed).
9. [`09_NAMING_CONVENTIONS.md`](docs/contracts/09_NAMING_CONVENTIONS.md): Casing, layering, and boundary rules.
10. [`10_CROSS_TEAM_DEPENDENCIES.md`](docs/contracts/10_CROSS_TEAM_DEPENDENCIES.md): Cross-team integration matrix.

---

## 🚀 Development Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm / pnpm
- Git

### 2. Environment Configuration
Copy the example environment file and configure local credentials:
```bash
cp .env.example .env
```

### 3. Running Contract Tests
```bash
python tests/test_contracts.py
```

### 4. Branch Strategy
- `main`: Stable releases (baseline tagged `v0.1-foundation`).
- `feature/contracts`: Active Phase 0 foundation branch.
- Team branches: `feature/<team>-<task>` branching off `feature/contracts`.

---

## 🚦 Phase Status

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | **Foundation & Contract Freeze** | **COMPLETED (`feature/contracts`)** |
| Phase 1 | PostgreSQL Migrations & Repository Layer | Planned |
| Phase 2 | Safe Ingestion & Deterministic Demo Seeding | Planned |
| Phase 3 | Agent 1 Extraction Engine | Planned |
| Phase 4 | Agent 2 Entity Resolution Pipeline | Planned |
| Phase 5 | Neo4j Projection & Classical SNA | Planned |
| Phase 6 | Frontend Investigation Workflows | Planned |
| Phase 7 | GATv2 Link Prediction Benchmark | Planned |
