# Phase 5 Verification Report — Live Analytical Neo4j Graph Projection

**Date:** September 15, 2026  
**Component:** Agent 2 Phase 5 — Idempotent Analytical Graph Projection & Rebuild  
**Status:** **VERIFIED & COMPLETE**

---

## 1. Verified Environment & Configuration

All Phase 5 verifications were executed directly against real, live database services with zero mocking during integration checks.

- **Authoritative System of Record (PostgreSQL)**:
  - Host: `localhost:5432`
  - Database: `sih_criminal_network`
  - Driver: `psycopg2` via SQLAlchemy ORM (`SessionLocal`)
  - Migration Head: `ff7ea090b5c4` (`add_dempster_shafer_fields`)
  - Canonical Tables Populated: `users`, `cases`, `case_members`, `documents`, `document_versions`, `document_chunks`, `entities`, `entity_identifiers`, `relationships`, `relationship_evidence`, `graph_snapshots`
- **Analytical Projection Layer (Neo4j Desktop)**:
  - URI: `bolt://127.0.0.1:7687` (configured in `.env` as `bolt://localhost:7687`)
  - Project Database: `sih26189`
  - Connection Driver: Official Python `neo4j` driver pooled via `Neo4jConnectionManager`
  - Driver Session Management: Managed through `Neo4jConnectionManager.get_session()` scoped to database `sih26189`

---

## 2. Deterministic Canonical Dataset

Seeded into PostgreSQL via `scripts/seed_demo.py` using deterministic UUIDs (`uuid.uuid5` with namespace `sih26189.demo.canonical`):

- **Case ID**: `2edcb7df-33ff-5da6-9a02-1d9b8c012eb2` (`DEMO-CASE-2026-0001`)
- **Case Member**: Lead Investigator `demo_investigator` (`42a98e8a-be87-54aa-b778-4395fbdd8f2d`)
- **Document & Provenance Artifacts**:
  - Document ID: `f2c3bf5e-d250-5162-8178-5775f0a71f00` (`cdr_report.pdf`, status: `PARSED`)
  - Version ID: `f048bb01-2fe6-522d-ba32-47daff7ceb92`
  - Chunk ID: `85fcae96-a31c-518b-a0e8-550c4a1e2ba7` (Span: `"0-77"`)
- **Entities**:
  - Entity 1: `b31dd215-8d63-5674-93bb-28c50f600464` | `PERSON` | `"Vikram Singh [DEMO]"` | `ACTIVE`
  - Entity 2: `f0173c52-9f1e-5d23-93e7-72cea5c26f37` | `PHONE` | `"+919876543210"` | `ACTIVE`
- **Identifiers**: 2 hashed canonical identifiers (`PERSON_NAME`, `PHONE`) complying with PII masking invariants
- **Relationship**:
  - Relationship ID: `e20551c0-d6ef-574e-bd69-eefa69299585`
  - Type: `OWNS` (`Person` -> `Phone`)
  - Status: `OBSERVED` (Subjective Logic: `belief=1.0, disbelief=0.0, uncertainty=0.0, conflict_mass=0.0, evidence_count=1, relationship_confidence=1.0`)
- **Relationship Evidence**:
  - Evidence ID: `833d26e5-1764-5bcd-bc6e-9cda1bb8354d`
  - Source Reference: `85fcae96-a31c-518b-a0e8-550c4a1e2ba7` (`DOCUMENT_CHUNK`)

---

## 3. Database Session Defect & Resolution

### Diagnosis
During the initial live projection against Neo4j database `sih26189`, `GraphProjectionService.rebuild_case_graph` failed with:
```
neo4j.exceptions.ClientError: {neo4j_code: Neo.ClientError.Database.DatabaseNotFound} {message: Database does not exist. Database name: 'neo4j'.}
```
Investigation revealed that several services were instantiating raw driver sessions without specifying the configured database:
```python
driver = self.graph_manager.get_driver()
with driver.session() as session:  # Defaults to database 'neo4j'
```

### Applied Fix
All unparameterized `driver.session()` calls were replaced with `Neo4jConnectionManager.get_session()`, which automatically binds sessions to `self._settings.neo4j_database` (`sih26189`):
- `backend/services/graph_projection.py`: Lines 92, 258, 286
- `backend/repositories/neo4j_repository.py`: Line 31
- `backend/services/graph_query.py`: Line 94 (using `access_mode="READ"`)
- `backend/graph/schema_init.py`: Line 54

---

## 4. Live Verification Results

### A. Initial Live Projection
- **Command**: `GraphProjectionService(db).rebuild_case_graph(UUID("2edcb7df-33ff-5da6-9a02-1d9b8c012eb2"))`
- **Nodes Projected**: `2` (`Person`, `Phone`)
- **Edges Projected**: `1` (`OWNS`)
- **Calculated Checksum**: `37a570562a6fc9d7978eefa0ec59edee1dc3efddc1dcb8bddbed36cbf46dee33`
- **Result**: **PASS**

### B. True Idempotency Verification
The exact same projection was re-executed without altering PostgreSQL or Neo4j data:
- **Pre-run vs Post-run Counts**:
  - Nodes: `2` -> `2` (`+0` duplicates)
  - Relationships: `1` -> `1` (`+0` duplicates)
- **Node & Relationship Identifiers**: Exactly stable (`b31dd...`, `f0173...`, `e2055...`)
- **Properties & Provenance**: Preserved without drift (`provenance_count=1`, `status="OBSERVED"`, `confidence_score=1.0`)
- **Result**: **PASS**

### C. Case-Scoped Purge Safety Verification
- **Purge Query**: `MATCH (n {case_id: $case_id}) DETACH DELETE n` with parameter `{"case_id": "2edcb7df-33ff-5da6-9a02-1d9b8c012eb2"}`.
- **Safety**: Strictly parameterized on `case_id`. Does NOT execute global `MATCH (n) DETACH DELETE n`. Preserves all nodes and relationships outside the target case boundary.
- **Result**: **PASS**

### D. Rebuildability Verification
- **Intermediary Purge**: Executed case-scoped purge; verified Neo4j returned `0 nodes` and `0 relationships` for case `2edcb7df-33ff-5da6-9a02-1d9b8c012eb2`.
- **Rebuild Execution**:
  ```bash
  python scripts/rebuild_graph.py --case-id 2edcb7df-33ff-5da6-9a02-1d9b8c012eb2
  ```
- **Post-Rebuild Verification**:
  - Rebuilt Nodes: `2` (both `Person` and `Phone` nodes restored with identical IDs and properties)
  - Rebuilt Relationships: `1` (`OWNS` edge restored with identical provenance and confidence)
  - PostgreSQL Canonical Data: 100% unaltered; all relational row counts remained intact.
- **Result**: **PASS**

---

## 5. Deterministic Checksum & Ledger Invariants

The `GraphProjectionService.compute_case_checksum` method computes an order-invariant SHA-256 digest across active entities and relationships. Across all runs, the checksum remained identical:
```
37a570562a6fc9d7978eefa0ec59edee1dc3efddc1dcb8bddbed36cbf46dee33
```

### `graph_snapshots` Audit Trail in PostgreSQL
Each projection and rebuild operation successfully appended an immutable audit ledger entry:

| Run | Snapshot ID | Case ID | Checksum | Created At |
| :--- | :--- | :--- | :--- | :--- |
| **Initial Projection** | `afb18e09-6341-47ec-9204-64e8d2c22001` | `2edcb7df...` | `37a570562a...` | `2026-09-15 02:43:42` |
| **Idempotency Run** | `707b5dfd-01fa-4f72-ad76-7959cf2016c9` | `2edcb7df...` | `37a570562a...` | `2026-09-15 02:45:16` |
| **Rebuild Run** | `f1aa8b23-4610-42ee-a537-e8a91c79470c` | `2edcb7df...` | `37a570562a...` | `2026-09-15 02:58:58` |

---

## 6. Test Distinction: Mocked Unit Tests vs Live Verification

| Dimension | Mocked Unit Tests (`tests/unit/`) | Live Verification (`scripts/`) |
| :--- | :--- | :--- |
| **Database Engine** | In-memory SQLite (`sqlite:///:memory:`) | PostgreSQL Server (`sih_criminal_network`) |
| **Neo4j Engine** | In-memory `MockNeo4jConnectionManager` / `MockDriver` | Neo4j Desktop DBMS (`sih26189`) via Bolt |
| **Cypher Validation** | Cypher syntax & parameter dictionary checks | Live Neo4j Cypher query execution & execution plan |
| **Schema Constraints** | In-memory dictionary sets | Real Neo4j range indices and unique constraints |
| **Network & Latency** | Synchronous mock calls | Real TCP / Bolt socket connection pooling |
| **Suite Results** | `tests/unit/test_graph_sync.py`: 11/11 PASS<br>`tests/unit/test_phase5_graph_sync.py`: 3/3 PASS | Real Projection, Idempotency, and Rebuild: 100% PASS |

---

## 7. Current Limitations & Scope Boundary

1. **Single-Case Demo Dataset**: The live database currently contains one representative canonical investigation case (`DEMO-CASE-2026-0001`). Multi-case cross-case isolation was verified via unit tests, but full multi-case scale testing will expand in Phase 6.
2. **AI Predictions Baseline**: The baseline demo dataset strictly validates factual evidence links (`OWNS`, `OBSERVED`). Inferred AI links (`is_predicted=True`, dashed edges) are supported in `GraphProjectionService` and covered by unit tests, but no synthetic `Prediction` records were seeded in PostgreSQL.
3. **Stand-Alone CLI Invocations**: `scripts/seed_demo.py` and `scripts/rebuild_graph.py` now include explicit `sys.path` bootstrapping to support direct invocation from shells without requiring `PYTHONPATH=.`.

---

## 8. Conclusion

Agent 2 Phase 5 has achieved complete live verification:
- System of Record integrity is maintained in PostgreSQL.
- Analytical projection in Neo4j database `sih26189` is fully synchronized, idempotent, and rebuildable on demand.
- The project is ready for evaluation against Phase 6 prerequisites.
