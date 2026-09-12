# DOCUMENT CONSISTENCY & AUDIT REPORT

**Project:** SIH26189 — AI-Powered Criminal Network Analysis System  
**Phase:** Phase 0 — Foundation & Contract Freeze  
**Branch:** `feature/contracts`  
**Status:** Canonical Contracts Frozen  

---

## 1. Canonical Documents (`docs/contracts/`)

The operational baseline for all development teams consists of the 10 canonical contracts:
1. `01_SHARED_TYPES.md`: Master UUIDv4 IDs, application lifecycle states, relationship evidence states, confidence metrics.
2. `02_DATABASE_SCHEMA.md`: PostgreSQL authoritative system of record, relational schemas, audit logs.
3. `03_GRAPH_SCHEMA.md`: Neo4j analytical graph projection, node/relationship vocabulary, provenance rules.
4. `04_API_SPEC.md`: REST API specification (`/api/v1/`), standard response envelopes, error structures.
5. `05_AI_CONTRACTS.md`: AI/ML agent interfaces (Agent 1 Extraction, Agent 2 Resolution, Agent 3 SNA & GATv2).
6. `06_WORKFLOWS.md`: Ingestion, validation, review, graph projection, and degraded modes.
7. `07_AUTH_SECURITY.md`: RBAC (Investigator, Analyst, Supervisor), JWT, audit logging, case isolation.
8. `08_UI_DATA_CONTRACT.md`: CaseShell, Cytoscape.js canvas formatting, solid vs dashed visual invariant.
9. `09_NAMING_CONVENTIONS.md`: Modular monolith boundaries, casing conventions, import boundaries.
10. `10_CROSS_TEAM_DEPENDENCIES.md`: Cross-team integration matrix and contract change protocol.

---

## 2. Supporting Documents (`docs/`)

- `prd.md`: Product Requirements Document (Problem context, target users).
- `trd.md`: Technical Requirements Document (Latency SLA, tech stack).
- `system-architecture.md`: Canonical system architecture (Modular monolith + background worker).
- `appflow.md`: Complete application user/system navigation journeys.
- `backend-schema.md`: Extended backend relational schema details.
- `design.md`: Product & UX design specifications.
- `security.md`: Threat model & vulnerability mitigations.
- `rules.md`: Coding agent guidelines.
- `implementation-plan.md`: Sprint execution roadmap.
- `tracker.md`: Living task tracking sheet.

---

## 3. Resolved Contradictions

1. **GATv2 Role Clarified**: Earlier notes positioned GATv2 as a "kingpin detector" or "guilt oracle." The canonical contracts firmly reject this. GATv2 is exclusively for link prediction, association scoring, and graph representation learning. SNA handles structural node centrality and bridge detection.
2. **Architecture Scope**: Rejected enterprise microservice complexity (Kafka, Kubernetes, multi-repo sprawl) in favor of a lean, reliable modular monolith with PostgreSQL + Neo4j + Celery/Redis background worker.
3. **Evidence vs Inference Visualization**: Resolved that physical evidence (`OBSERVED`, `CORROBORATED`, `CONFIRMED`) renders as **solid lines**, while AI predictions (`INFERRED`) render as **dashed lines** with redundant text labels for accessibility.
4. **Data Realism & Disclaimers**: Live police CDR/IPDR is not accessible; operational demo uses deterministic synthetic data with clear disclaimers.

---

## 4. Unresolved / Deferred Architectural Decisions

The following items are intentionally marked `[PROVISIONAL]` or `[DEFERRED]` and must NOT be fabricated:
1. **Malware Scanning Engine**: Exact antivirus/malware scanning library for file uploads.
2. **SNA Cache Invalidation Cadence**: Exact TTL / trigger mechanism for graph metric recalculation.
3. **Voice Command Allowlist**: Exact phrase lexicon if audio input is integrated into the demo.
4. **Final OCR Provider**: Final cloud vs local OCR engine selection depending on runtime constraints.
5. **Subjective Logic Tuple Math Suite**: Mathematical validation suite for $(b, d, u, a)$ Dempster-Shafer consensus operations before claims are made.

---

## 5. Deprecated Historical Concepts

- ❌ Kafka message bus (Replaced by Redis / Celery lightweight background worker).
- ❌ Kubernetes cluster orchestrations (Replaced by Docker Compose / local modular services).
- ❌ Direct client-supplied Cypher queries (Replaced by case-scoped parameterized repository methods).
- ❌ Global destructive graph resets (`MATCH (n) DETACH DELETE n`).

---

## 6. Phase 0 Changes & Deliverables

1. **Git Repository Setup**:
   - Baseline prototype tagged `v0.1-foundation` on `main` (commit `a37864b`).
   - Active foundation branch `feature/contracts` created and checked out.
2. **Canonical Contracts Directory**:
   - Deployed all 10 canonical files into `docs/contracts/`.
3. **Repository Constitution**:
   - Established root `AGENTS.md` defining mandatory agent workflow and strict prohibitions.
4. **Security Hardening (SEC-001)**:
   - Created root `.env.example` with sanitized placeholders.
   - Created comprehensive `.gitignore` preventing secrets and artifacts from being tracked.
5. **Frontend Lead Foundation**:
   - `apps/web/src/types/contracts.ts`: Canonical TypeScript type definitions.
   - `apps/web/src/mocks/mockEnvelope.ts`: Standard API response envelope helpers.
   - `apps/web/src/styles/graphStyles.ts`: Cytoscape.js styling enforcing solid (evidence) and dashed (inferred) lines.
   - `apps/web/src/fixtures/graphFixture.ts`: Deterministic synthetic graph fixture.
6. **Automated Verification**:
   - Created `tests/test_contracts.py` ensuring contract presence, envelope validation, and secret prevention.

---

## 7. Security Findings (SEC-001)

- **Hardcoded Secrets Found**: 0 hardcoded credentials found in active codebase.
- **Environment Variables**: Centralized in `.env.example`.
- **Git Ignore**: Protected against `.env`, `*.pem`, `*.key`, and local database files.

---

## 8. Cross-Team Contract Risks

1. **Frontend / API Mismatch**: Frontend must strictly consume `{ success, data, error, request_id }` envelopes.
2. **Schema Invariants**: PostgreSQL fields must remain snake_case; API JSON payloads must remain camelCase.
3. **Provenance Required**: Frontend must not display orphan nodes or edges without case and provenance linkage.

---

## 9. Next Steps

- **Phase 0 Status**: `PHASE 0 READY`
- **Next Recommended Phase**: Phase 1 — PostgreSQL migrations, database seeders, and backend repository integration.
