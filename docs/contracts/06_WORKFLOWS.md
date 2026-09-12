# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 6: SYSTEM WORKFLOW STATE MACHINES [CURRENT/FINAL]

```
+------------+     +-----------+     +------------+     +-------------+
|  RECEIVED  | --> | VALIDATED | --> | PROCESSING | --> |  EXTRACTED  |
+------------+     +-----------+     +------------+     +-------------+
                                                               |
                                                               v
                                                      +-----------------+
                                                      | REVIEW_REQUIRED |
                                                      +-----------------+
                                                               |
                                             +-----------------+-----------------+
                                             |                                   |
                                             v                                   v
                                        +----------+                        +----------+
                                        | ACCEPTED |                        | REJECTED |
                                        +----------+                        +----------+

```

#### 6.1 Unstructured Ingestion Workflow

1. **Ingestion Intake:** Relational database entry created for document; status set to `RECEIVED`.
2. **Sanitization Check:** Security checks validate filename paths, file size boundaries, and exact MIME signatures. State transitions to `VALIDATED`.
3. **Parsing & OCR:** Parsing background tasks parse document streams. State transitions to `PROCESSING`.
4. **Agent 1 NLP Extraction:** The text parser extracts mentions, temporary entities, and metadata mappings, shifting the document state to `EXTRACTED`.
5. **Agent 2 Resolution Staging:** Compares temporary variables against existing Case entities. 
   - *High-Confidence Match (>0.85):* Mentions are merged with existing canonical entities, and status transitions to `ACCEPTED`.
   - *Ambiguous Match (0.50 - 0.85):* Entities are staged, and status transitions to `REVIEW_REQUIRED`.
   - *Fail / Collision:* Status transitions to `FAILED` or `REJECTED`.
6. **Graph Generation:** Committed entities and relationships in PostgreSQL are synced to Neo4j using idempotent `MERGE` projections.

#### 6.2 Case Isolation Verification Workflow

This sequence must be executed server-side for every domain request:

1. Verify that the active user's authorization token contains an active case membership row mapping to `requested_case_id`.
2. If the user does not possess active case authorization, the backend must return a generic `404 Not Found` response, rather than a `403 Forbidden` response, to prevent unauthorized users from discovering the existence of sensitive cases.
3. All dynamic SQL and Cypher query parameters must explicitly append a `case_id` clause (e.g., `WHERE node.case_id = $case_id`) to maintain case isolation boundaries.

#### 6.3 Recovery and Degraded Operations Workflow

Subsystem failures must be handled gracefully to preserve core functionality:

- **Neo4j Offline:** API graph routes return `503 Service Unavailable`, but PostgreSQL relational queries, case listings, and document searches remain functional.
- **LLM Provider Offline:** Shunts natural-language extraction or explanation tasks to a queue and falls back to deterministic parsing and template explanations. System remains functional under a `DEGRADED — Provider Offline` status.
- **GNN Offline:** Prediction features are disabled while SNA features and alert motifs remain active.

---
