# Canonical Backend & Data Schema

**Project:** SIH26189 — AI-Powered Criminal Network Analysis System  
**Status:** Consolidated implementation-ready specification  
**Source basis:** Reconstructed project history plus verified external repository/data context  

SIH26189 is an AI-powered criminal network analysis system for investigation support. The target problem is not generic graph visualization. The product should help authorized investigators ingest fragmented case information, extract and normalize entities and relationships, construct a case-centric knowledge graph, analyze network structure and suspicious patterns, identify influential nodes, surface potentially missing associations, trace every conclusion back to evidence, and present explainable investigative leads. The design is Indian-context first, while acknowledging that many operational CDR, IPDR, banking, identity, and surveillance datasets are not publicly available at the necessary granularity. The prototype therefore combines real Indian public sources where appropriate, synthetic Indian operational data for unavailable streams, and clearly labeled international research benchmarks for algorithmic validation.

The recovered project history has a working prototype path of Neo4j -> FastAPI -> Cytoscape.js. The prototype already demonstrated graph loading and basic degree/betweenness analysis, but its current code has important weaknesses: hardcoded credentials, permissive CORS, destructive graph reset behavior, simple CREATE instead of idempotent MERGE, and insufficient separation between evidence, inferred relationships, and presentation. Those are prototype limitations, not production architecture. The final documentation therefore preserves the useful existing work while explicitly requiring safer interfaces and clearer boundaries.

The three-agent concept is retained but narrowed. Agent 1 is an intelligence extraction component for unstructured content: OCR/parsing where required, named-entity and relationship extraction, normalization, and structured output. Agent 2 is the evidence and graph-maintenance component: validation, entity resolution assistance, provenance, relationship/evidence records, confidence representation, graph materialization, and temporal relevance. Agent 3 is the Network Intelligence & Prediction Engine. It runs explainable SNA (degree, betweenness, eigenvector/PageRank, K-core and communities), deterministic suspicious-pattern detection, optional/validated GATv2 link prediction, and an investigative-priority ranking layer. GATv2 does not prove criminality and does not by itself identify a kingpin.

The product is decision support, not an autonomous law-enforcement decision-maker. Scores must never be presented as guilt. AI outputs must include the score, confidence semantics, explanation, contributing features, supporting evidence, model/version, timestamp, and limitations. Inferred edges must never overwrite source-backed evidence. Every important graph assertion must have provenance. Human investigators remain responsible for review, correction, rejection, and action.

The architecture should be a modular monolith plus a small ML worker boundary rather than a microservice zoo. PostgreSQL is the system-of-record for application state and audit metadata; Neo4j is the graph analytical store; object/file storage is for original documents and derived artifacts; a lightweight job/worker mechanism handles asynchronous document processing and ML tasks. Kafka, Kubernetes, SPIFFE/SPIRE, TLA+, distributed sagas, and similar enterprise mechanisms are deferred unless a later validated need appears. The system should be sophisticated enough to demonstrate real engineering but simple enough for a six-person student team to finish and explain.

### Decision-status legend
- **FINAL** — the project should implement this unless an explicit architecture decision record changes it.
- **PROVISIONAL** — chosen for the SIH prototype, but may be revised after measurement.
- **NEEDS VALIDATION** — not safe to treat as fact until a benchmark, dataset inspection, or prototype test confirms it.
- **DEFERRED** — intentionally excluded from the current implementation window.
- **REJECTED** — previously considered and explicitly rejected because the complexity or claim is not justified.

### Non-negotiable engineering truths
1. A dataset that contains crime counts is not automatically a criminal-network dataset.
2. A graph centrality score is not evidence of guilt.
3. A machine-learning prediction is not a source record.
4. A high confidence score must have a defined meaning and provenance.
5. External LLM calls are optional and must be provider-abstracted and privacy-controlled.
6. Frontend authorization is never sufficient; every sensitive backend request must be authorized server-side.
7. Inferred relationships and source-backed relationships are separate evidence states.
8. Demo data must be deterministic and reproducible.
9. Anything not implemented must be described as future, simulated, synthetic, or research-only.
10. The repository documentation is the operating contract for future coding agents.

## 1. Canonical data-model strategy

The backend uses PostgreSQL as the system of record and Neo4j as the analytical graph projection. The relational model captures case ownership, documents, source evidence, entities, jobs, predictions and audit history. The graph model is derived and must remain rebuildable. Stable UUID identifiers are used for application entities. Human-readable external identifiers such as FIR numbers or UPI VPAs are stored as typed identifiers, not primary keys.

## 2. Core relational entities

| Entity | Purpose | Key | Important fields | Security/retention |
| --- | --- | --- | --- | --- |
| users | Identity and account state | user_id UUID | email/username, status, role refs, timestamps | Sensitive; retain per policy. |
| roles | Role definitions | role_id UUID | name, permissions | Low/medium sensitivity. |
| permissions | Action grants | permission_id UUID | code, description | Reference data. |
| cases | Investigation boundary | case_id UUID | case_code, title, status, jurisdiction, created_by | Sensitive; case retention applies. |
| case_members | User-to-case authorization | case_member_id UUID | case_id, user_id, role_in_case | Critical for isolation. |
| documents | Source artifact metadata | document_id UUID | case_id, type, hash, storage_key, status | Highly sensitive. |
| document_versions | Immutable document versions | version_id UUID | document_id, hash, created_at, source metadata | Highly sensitive. |
| document_chunks | Parsed chunks/source spans | chunk_id UUID | version_id, page/span, text_hash, storage ref | Highly sensitive; redact logs. |
| entities | Canonical graph entities | entity_id UUID | case_id, type, canonical_name, status | Sensitive; scoped. |
| entity_aliases | Observed names/aliases | alias_id UUID | entity_id, alias_text, source reference | Sensitive. |
| entity_identifiers | Typed identifiers | identifier_id UUID | entity_id, type, normalized_value_hash/value policy | Highly sensitive. |
| relationships | Canonical relationship state | relationship_id UUID | case_id, source_entity, target_entity, type, status | Sensitive. |
| relationship_evidence | Evidence supporting relationship | evidence_id UUID | relationship_id, source_ref, support_type | Critical provenance. |
| events | Temporal events | event_id UUID | case_id, event_type, timestamp, entity refs, source | Sensitive. |
| communications | Structured communication events | communication_id UUID | caller/receiver entities, time, duration, channel | Highly sensitive. |
| transactions | Financial events | transaction_id UUID | sender/receiver, amount, currency, time, channel | Highly sensitive. |
| locations | Canonical locations | location_id UUID | normalized label, lat/lon policy, jurisdiction | Sensitive/PII as applicable. |
| vehicles | Vehicle metadata | vehicle_id UUID | plate hash/masked label, type, source refs | Sensitive. |
| organizations | Organization entities | organization_id UUID | name, type, identifiers | Sensitive. |
| phones | Phone entities | phone_id UUID | identifier ref, active status | Highly sensitive. |
| accounts | Bank/payment accounts | account_id UUID | masked identifier, type, provider | Highly sensitive. |
| investigation_notes | Human notes | note_id UUID | case_id, author, text, entity refs | Highly sensitive. |
| model_runs | Every ML/LLM execution | run_id UUID | model, version, task, input snapshot, status | Sensitive; long retention only when justified. |
| predictions | Inferred associations/results | prediction_id UUID | run_id, case, source/target, score, calibration | Derived; never evidence. |
| risk_scores | Versioned priority scores | score_id UUID | entity, run_id, score type, value, feature summary | Derived/sensitive. |
| graph_snapshots | Projection versions | snapshot_id UUID | case, source version, created_at, checksum | Operational metadata. |
| audit_logs | Security/action trail | audit_id UUID | actor, action, case, target, timestamp, outcome | High integrity; append-only preferred. |
| alerts | Pattern findings | alert_id UUID | case, type, severity, rule/run, entities, status | Sensitive derived data. |
| saved_queries | Structured investigator searches | query_id UUID | case, owner, filter JSON | Sensitive. |
| search_history | Recent searches | search_id UUID | user, case, query metadata | Short retention. |
| exports | Generated reports | export_id UUID | case, requester, artifact ref, version, hash | Highly sensitive; audit access. |

## 3. Required relationships and constraints

Cases own documents, entities, events, relationships, alerts, notes and analysis runs. Case membership is the authorization join. Documents own versions; versions own chunks. Entities own aliases and identifiers. Relationships own evidence references. Model runs own predictions and score outputs. Audit logs reference actor, action, case and target but do not require every target to remain available forever. Unique constraints should exist on case code, document hash within case, external source reference within a case where appropriate, canonical entity UUID, and model-run identifiers. Sensitive identifiers should be normalized and optionally hashed/masked based on retention policy.

## 4. Graph schema

| Node label | Examples of properties | Key edges |
| --- | --- | --- |
| Person | entity_id, display_name, status, alias_count | ACCUSED_IN, KNOWS, CONTACTED, LOCATED_AT, OWNS |
| Phone | entity_id, masked_identifier | USED_BY, COMMUNICATED_WITH, PINGED_TOWER |
| BankAccount | entity_id, masked_identifier, provider | OWNED_BY, TRANSFERRED_TO |
| Vehicle | entity_id, masked_plate, type | REGISTERED_TO, SCANNED_AT |
| Organization | entity_id, name, type | AFFILIATED_WITH, OWNS, ASSOCIATED_WITH |
| Location | entity_id, normalized_name, geography | OCCURRED_AT, LOCATED_AT, SCANNED_AT |
| Case | case_id, case_code | CONTAINS |
| Evidence | evidence_id, source_type | SUPPORTS, REFUTES |
| Offense | offense_id, category, code | HAS_INCIDENT, ACCUSED_IN |

## 5. Relationship properties

Every graph relationship that represents evidence has: relationship_id, status (OBSERVED/CORROBORATED/INFERRED/CONFIRMED/REJECTED), source_ref_count, relationship_confidence where defined, confidence_type, belief/disbelief/uncertainty only if the chosen confidence model is active, observed_at or event-time fields, created_at, source_system, evidence_ids or a provenance reference, and analysis metadata when derived. Predicted edges are separate and contain prediction_id, model_run_id, score, calibration status and expiry/review status. Do not use one numeric `confidence` field for every semantics.

## 6. API response conventions

All APIs use versioned `/api/v1` paths. List endpoints paginate with cursor or page/limit depending on implementation. Errors use a structured shape such as `{code, message, request_id, details?}` without secrets. Authorization failure is 403 when the resource is known and accessible but disallowed, and 404 can be used to avoid resource enumeration when policy requires it. Long-running jobs return 202 with a job/run identifier. Idempotency keys are used for create/ingest actions where retries could duplicate data.

## 7. Representative API catalog

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| POST | /api/v1/cases | Create case | Authenticated + create permission |
| GET | /api/v1/cases | List cases | Authenticated; filtered by membership |
| GET | /api/v1/cases/{case_id} | Case details | Case member |
| POST | /api/v1/cases/{case_id}/documents | Upload document | Case member + upload |
| POST | /api/v1/cases/{case_id}/imports | Import structured data | Case member + import |
| GET | /api/v1/cases/{case_id}/entities | Search/list entities | Case member |
| GET | /api/v1/cases/{case_id}/graph | Bounded graph query | Case member + graph_read |
| POST | /api/v1/cases/{case_id}/analysis | Start analysis run | Case member + analysis |
| GET | /api/v1/cases/{case_id}/analysis/{run_id} | Analysis status/results | Case member |
| GET | /api/v1/cases/{case_id}/alerts | List analytical alerts | Case member |
| GET | /api/v1/cases/{case_id}/evidence/{evidence_id} | Evidence detail | Case member |
| POST | /api/v1/cases/{case_id}/reviews | Record review decision | Reviewer permission |
| GET | /api/v1/cases/{case_id}/audit | Audit trail | Supervisor/audit permission |
| POST | /api/v1/cases/{case_id}/exports | Generate report | Export permission |
| GET | /api/v1/search | Cross-case structured search | Only privileged scope; otherwise case-scoped |

## 8. Schema lifecycle and migrations

Relational schema changes use versioned migrations. Graph schema changes are handled through explicit projection/migration jobs and documented compatibility notes. Backward-compatible API additions are preferred. Breaking changes require a new API version or a documented migration period. Dataset schemas are versioned independently from application schema because upstream data fields can change. Synthetic generators must emit schema version metadata.

## 9. Provenance model

Every source-backed relationship points to one or more evidence records. Evidence records point to a source document, transaction, communication, event, or investigator action. An inferred relationship points to a model run and the graph snapshot used. A graph-derived metric points to the analysis run and snapshot. This creates a trace chain such as: insight -> ranking -> features/prediction -> graph relation -> evidence -> source artifact. The chain must survive reprocessing.

## 10. Data-quality invariants

No duplicate canonical ID. No relationship may reference an entity outside its case scope. No prediction may overwrite a source-backed relationship. All required timestamps must be parseable or explicitly unknown. Enumerations are validated. Amounts use a fixed decimal/numeric representation rather than binary float in persistent transaction state. Sensitive values are masked in logs. Invalid model output never enters canonical tables. Source hashes detect accidental file changes.

## 11. Security classification and retention

Case content, identifiers, source documents, notes, transactions, communications and audit records are sensitive by default. The prototype may use local files, but the schema still models storage keys rather than embedding full documents in rows. Retention is policy-driven. Search history can have shorter retention than evidence. Export artifacts inherit case sensitivity. Deletion must be explicit, audited, and safe against orphaning provenance unexpectedly.

## 12. Decision status

| Item | Status |
| --- | --- |
| UUID-style stable application IDs | FINAL |
| PostgreSQL + Neo4j split | FINAL |
| Case-level authorization in relational state | FINAL |
| Inference/evidence separation | FINAL |
| Full subjective-logic tuple on every edge | PLANNED / VALIDATION REQUIRED |
| Raw phone/account value in model features | REJECTED |
| Arbitrary Cypher API | REJECTED |
| Cross-case global graph for standard users | REJECTED |
| Prediction stored as source evidence | REJECTED |

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.
