# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 12: CROSS-TEAM DEPENDENCY MATRIX

To maintain alignment, data exchanged across boundaries must use stable Pydantic and TypeScript interfaces.

| Boundary StateData ExchangedContract OwnerConsumer SystemStability Constraint |                                                      |                          |                             |                                               |
| ----------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------ | --------------------------- | --------------------------------------------- |
| **Frontend ↔ API**                                                            | Bounded Subgraph JSON, Case Authorization Tokens     | API schemas (`Pydantic`) | Web Client                  | API routes and return schemas are frozen.     |
| **API ↔ PostgreSQL**                                                          | Entity & User Relational Models                      | Relational Repositories  | PostgreSQL DB               | Schema changes must use versioned migrations. |
| **API ↔ Neo4j**                                                               | Graph Node & Idempotent Edge Queries                 | Neo4j Repositories       | Neo4j DB                    | Dynamic queries must use parameterization.    |
| **API ↔ ML Worker**                                                           | Task Payloads (`job_id`, `case_id`, snapshot hashes, node/edge side info) | Job Queue Schema         | PyG/PyTorch ML Runtime      | Worker task structures are frozen.            |
| **ML Worker ↔ DB**                                                            | Predictions Output Matrix (IDs, weights)             | Prediction schema        | PostgreSQL System of Record | Results must pass schema validation check.    |

---

## Unresolved / missing contract items that affect team boundaries

### SECTION 11: SPECIFICATION ANALYSIS & REMAINING UNRESOLVED ISSUES

#### 11.1 Document Contradictions & Reconciliations

1. **The GATv2 Role Shift:** Earlier conceptual documents described the GATv2 GNN model as a "kingpin oracle." This was rejected as scientifically unsupportable. The current architecture strictly limits GATv2 to **link prediction and node representation**, utilizing explainable SNA (Degree, Betweenness, Centrality) and a separate ranking function to identify influential nodes.
2. **Subjective Logic vs. Multi-Signal Confidences:** Subjective Logic `(b, d, u)` tuples exist on relationship edges alongside traditional, distinct confidence attributes (`extraction_confidence`, `similarity_score`, `relationship_confidence`). 
   - *Authoritative Decision:* Subjective Logic `(b, d, u)` is part of the planned system architecture alongside traditional multi-signal confidences. Both exist in parallel; Subjective Logic requires mathematical validation testing before being trusted for production evidence fusion, while traditional explicit confidence metrics serve as immediate operational inputs.
3. **OmniRoute and gemini-web2api Risk:** Early development documentation references `OmniRoute` and `gemini-web2api` for API gateway routing. 
   - *Authoritative Decision:* These services are restricted to development use only, and must be abstracted behind clean internal provider interfaces to protect sensitive case data.

#### 11.2 Missing/Unspecified Details (Do Not Assume)

- **Malware Scanner Implementation:** The exact library and service for scanning file uploads are **[NOT SPECIFIED / DO NOT ASSUME]**.
- **User Role Join Details:** The schema mapping for `user_roles` is **[NOT SPECIFIED / DO NOT ASSUME]**.
- **Voice Command Allowlist:** The explicit list of commands for the P1 voice interface is **[NOT SPECIFIED / DO NOT ASSUME]**.
- **SNA Cache Update Recency:** The cache invalidate schedule or sync interval for SNA values is **[NOT SPECIFIED / DO NOT ASSUME]**.
- **OCR / Model Provider Stack:** The planned technology stack is finalized as: **PaddleOCR** (primary OCR), **IndicNER** (NER), **InLegalBERT** (legal domain parsing), **multilingual-E5-large-instruct / IndicSBERT** (embeddings), **Qwen3-4B-Instruct-2507** (generative extraction & explanation), **Dedupe + deterministic rules + embeddings** (entity resolution), and **PyTorch Geometric + GATv2** (supervised link prediction GNN). Exact hyperparameters and fine-tuning details remain implementation tasks.

---
