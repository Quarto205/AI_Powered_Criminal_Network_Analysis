# AI Coding Agent Constitution & Rules (SIH26189)

This document defines the non-negotiable rules, constraints, and operational protocol for all AI coding agents contributing to the **SIH26189 — AI-Powered Criminal Network Analysis System**.

**Operational Philosophy**: *Contracts before implementation. Freeze interfaces, not internal optimizations.*

---

## 1. Absolute Domain & Architectural Invariants

1. **System Architecture**: Modular Monolith with PostgreSQL as the authoritative relational system-of-record, Neo4j as an analytical graph projection, and a lightweight asynchronous background worker.
2. **GATv2 Purpose**:
   - GATv2 is **NOT** a kingpin detector.
   - GATv2 is **NOT** a guilt classifier.
   - GATv2 is **NOT** a crime-probability oracle.
   - GATv2 is exclusively intended for **link prediction / association scoring** and learned graph representations.
3. **Classical Social Network Analysis (SNA)**: SNA metrics (Degree, Betweenness, PageRank, Community Detection) handle explainable structural influence analysis.
4. **Physical Evidence vs. AI Inference**:
   - Source-backed evidence and AI-inferred relationships must remain strictly separated.
   - Evidence edges (`OBSERVED`, `CORROBORATED`, `CONFIRMED`) render as **solid lines**.
   - Inferred edges (`INFERRED`) render as **dashed lines**. Status must never rely solely on color.
   - AI predictions must **NEVER** overwrite physical/source evidence.
5. **Provenance & Case Scoping**:
   - All nodes, edges, alerts, and predictions require provenance metadata (source document ID, extractor agent ID, timestamp, confidence breakdown).
   - Case authorization is enforced server-side. Unauthorized case access returns `404 Not Found` (to avoid leaking case existence).
6. **Synthetic vs. Live Data**:
   - The demo must be reproducible with deterministic synthetic data.
   - Synthetic data must **NEVER** be labeled or presented as live operational police CDR/IPDR/banking records.
   - Academic benchmark results (Elliptic, AMLSim) must **NEVER** be presented as this project's results.
7. **Input & Model Trust Boundary**:
   - Model output is untrusted until schema validation.
   - Uploaded text is untrusted and must be isolated against prompt injection.
   - Client-supplied raw Cypher queries are strictly prohibited.

---

## 2. Mandatory Workflow for Coding Agents

Before touching code, every agent must:
1. **Read `docs/tracker.md`** to confirm task status and dependencies.
2. **Read relevant canonical contracts** under `docs/contracts/`:
   - `01_SHARED_TYPES.md` for shared data structures and lifecycle states.
   - `02_DATABASE_SCHEMA.md` for PostgreSQL tables, column types, and constraints.
   - `03_GRAPH_SCHEMA.md` for Neo4j node labels, edge types, and properties.
   - `04_API_SPEC.md` for HTTP routes, envelopes, and error codes.
   - `05_AI_CONTRACTS.md` for Agent 1, 2, and 3 payload contracts.
   - `06_WORKFLOWS.md` for state transitions and degraded operation policies.
   - `07_AUTH_SECURITY.md` for RBAC, JWT claims, and security boundaries.
   - `08_UI_DATA_CONTRACT.md` for frontend state and Cytoscape.js payloads.
   - `09_NAMING_CONVENTIONS.md` for casing, directory boundaries, and import rules.
   - `10_CROSS_TEAM_DEPENDENCIES.md` for inter-team boundaries and contract change processes.
3. **Inspect current code** to understand existing patterns before proposing edits.
4. **Propose the smallest safe change**.
5. **Run relevant tests, typechecks, and linters** before completing tasks.
6. **Update `docs/tracker.md`** and relevant contract documentation if interfaces legitimately evolve through review.

---

## 3. Strict Prohibitions

Agents must **NEVER**:
- ❌ Invent undocumented fields, tables, API endpoints, or graph relationship types.
- ❌ Silently rename public API fields or database columns.
- ❌ Expose arbitrary Cypher execution interfaces to clients.
- ❌ Hardcode passwords, API keys, JWT secrets, or connection strings.
- ❌ Expose LLM provider SDKs (OpenAI, Gemini) directly into the domain logic layer.
- ❌ Present inferred relationships as established facts.
- ❌ Silently alter shared contracts without cross-team review.
- ❌ Execute destructive global graph wipes (`MATCH (n) DETACH DELETE n`) in production code paths.
- ❌ Pretend mocked or prototype features are production-ready.

---

## 4. Contract Change Protocol

If a cross-team contract must change:
```text
Propose Change → Update Canonical Contract in docs/contracts/ → Cross-Team Review → Merge Contract → Implement Code
```
Implementation must never precede contract approval.
