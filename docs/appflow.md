# Application Flow Specification

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

## 1. Master state machine

The canonical lifecycle is: UNAUTHENTICATED -> AUTHENTICATED -> CASE_SELECTED -> INGESTION -> PROCESSING -> REVIEW -> GRAPH_READY -> ANALYSIS -> INVESTIGATOR_REVIEW -> REPORTING/AUDIT. Document processing is asynchronous and can fail without invalidating the case. Each job records status, start/end times, actor, model version if applicable, and error category. No UI state can substitute for backend state.

## 2. First-time user flow

Actor: new authorized investigator. Input: credentials/session challenge. Processing: authentication and role resolution. Output: user session and permitted case list. Database changes: none for ordinary login; audit event created. Security checks: session validation, account state, rate limits. Next state: dashboard. If no cases exist, show an empty state with create-case action. Failure: authentication failure provides generic error, not account enumeration.

## 3. Returning investigator flow

Actor: returning user. Input: valid session. Processing: refresh/validate session and load authorized cases. Output: dashboard with case work queue. Database reads are strictly scoped to permitted case memberships. Recent jobs and alerts show only allowed data. Expired sessions require re-authentication. An investigator cannot deep-link directly into an unauthorized case; backend returns a generic authorization failure.

## 4. Create case flow

Actor: Investigator. Input: case title, identifier/metadata, optional description. Processing: validation and authorization. Output: case record and membership. Database: insert case, membership and audit event. AI: none. Security: role and tenancy/case policy. Next state: case workspace. Failure: duplicate case identifier or insufficient permission results in a controlled error. The frontend cannot create an “admin” role or bypass required metadata.

## 5. Document upload flow

Actor: Investigator. Input: PDF/text/document. Processing: file size/type validation, safe storage, hash calculation, document metadata creation, optional malware scan, then asynchronous parsing. Output: document status RECEIVED/VALIDATED/PROCESSING. Database: document and version record; file storage object. AI: OCR/parser only when needed. Security: path traversal prevention, content-type validation, case authorization. Failure states include invalid type, corrupted document, oversized file, scanner failure and worker timeout.

## 6. Structured data upload flow

Input: CSV/JSON with explicit schema declaration. Processing: schema validation, field normalization, identifier validation, row-level error report, then staged ingestion. Output: accepted/rejected counts and job ID. Graph changes occur only after validation. The system should never infer that an arbitrary column named “confidence” has the same semantics as relationship confidence; field mappings must be explicit.

## 7. NLP extraction flow

Actor: background extraction worker. Input: validated text chunk + source metadata. Processing: OCR if required, chunking, entity/relation extraction, schema validation, normalization hints. Output: extraction result with temporary entity IDs and source spans. Database: extraction job and evidence links. Model: configured LLM/NER engine. Failure: provider outage, malformed JSON, extraction timeout or low quality. Retry policy is bounded; repeated failure transitions to REVIEW_REQUIRED or FAILED rather than looping forever.

## 8. Entity normalization and resolution flow

Input: extracted mentions. Processing: canonicalization of names, aliases, phone formats, account identifiers, locations and organizations; candidate matching; thresholding; deterministic rules before probabilistic similarity. Output: accepted canonical match, unresolved candidate set, or new entity. Database: source mention remains immutable; alias/identifier mappings are stored separately. Security: entity matches are case-scoped. Low-confidence matches require review. A bad match must never merge two entities silently.

## 9. Relationship and confidence flow

Input: relationship mentions/events plus source metadata. Processing: relationship normalization, evidence attachment, confidence classification, optional multi-source combination. Output: observed or inferred relationship record. The system distinguishes extraction confidence, entity-match confidence, relationship confidence, model confidence, anomaly score and investigation-priority score. These are not interchangeable. The graph representation references the evidence record and status. Conflicting evidence produces a review condition, not silent overwriting.

## 10. Graph creation and enrichment

Input: canonical entities, relationships, evidence. Processing: idempotent MERGE by stable IDs; create/update graph projection. Output: graph snapshot/version. Database: Neo4j changes plus graph-version metadata in PostgreSQL. Graph query scope is case-aware. A graph rebuild should be safe to rerun. Enrichment may add centrality or community attributes to analytics output, but derived fields should not overwrite raw entity properties.

## 11. Graph exploration flow

Actor: investigator. Input: selected entity/filter/hops/time range. Processing: backend builds a bounded subgraph query, applies case authorization, returns nodes/edges plus evidence status. Frontend renders Cytoscape. Selecting an edge fetches provenance details. Failure: graph database unavailable -> show cached last-known state if explicitly supported, otherwise controlled error; never show stale data as current. Large graph requests are limited and paginated/aggregated.

## 12. Agent 3 SNA flow

Input: case graph. Processing order: components -> centrality -> communities -> paths/bridges -> patterns. Output: metrics and structured analytical findings. Database: model/analysis run record and optional cached metrics. SNA metrics are deterministic and explainable. If network direction matters, the implementation must specify directed/undirected treatment by analysis type. The system should not apply one global graph interpretation to all relationship types.

## 13. Pattern detection flow

Input: time-stamped events/relationships. Processing: motif rules such as transaction fan-in/out, cycles, rapid communication bursts, bridge behavior and movement sequences. Output: pattern alert with rule ID, parameters, affected nodes/edges and time window. This is a rules engine, not necessarily an LLM agent. Failure: incomplete timestamps should produce “insufficient data” rather than a false anomaly.

## 14. GATv2 link-prediction flow

Input: case graph snapshot, node features, edge features, candidate edge set. Processing: encode graph, produce embeddings, score candidate relationships. Output: prediction candidates with model version, score, calibration status and eligible explanation fields. Predictions are stored separately from observed relationships. Inference does not change source evidence. Model unavailable -> analysis status is DEGRADED; other SNA features continue to work.

## 15. Investigative ranking flow

Input: SNA metrics, pattern findings, GAT embeddings/predictions, temporal activity and evidence signals. Processing: defined ranking function with versioned weights. Output: investigative-priority ranking. Each ranking entry contains feature contributions. The score is not “crime probability” unless a validated supervised task actually defines it. Human review is required before operational action.

## 16. AI explanation flow

Input: selected insight/alert/prediction. Processing: gather supporting structured facts and source references; optionally call a provider for natural-language rendering. Output: explanation with evidence and limitations. The LLM is not allowed to invent missing support. The UI shows the structured evidence beneath the prose. If the provider is unavailable, a deterministic template explanation is used.

## 17. Investigator review and correction

Actor: Investigator/Supervisor. Input: accept/reject/correct action and optional reason. Processing: permission check, validation, append review record. Output: new current status and audit event. The original raw source stays unchanged. Corrections affect canonical mappings or derived views rather than the historical source record. High-impact merges require elevated permission.

## 18. Timeline, evidence drill-down, export

Timeline queries combine events with case filters. Evidence drill-down opens the source record or secure preview. Export generates a versioned report from current authorized state. Every export is audited. Export content includes analysis provenance and a statement that model outputs are investigative leads, not determinations of guilt.

## 19. Failure and degraded-mode flows

| Failure | System response | User-visible state |
| --- | --- | --- |
| LLM unavailable | Continue deterministic graph/SNA; mark extraction/explanation job failed or queued for retry. | DEGRADED — AI provider unavailable. |
| Neo4j unavailable | Fail graph queries safely; preserve source/application state. | GRAPH UNAVAILABLE; retry option. |
| Malformed model output | Schema validation rejects response; retry or route to alternate provider if approved. | MODEL OUTPUT REJECTED. |
| Entity conflict | Keep both source mentions; require resolution. | REVIEW REQUIRED. |
| Unauthorized access | Do not leak case existence beyond policy. | ACCESS DENIED. |
| Oversized/invalid file | Reject before processing. | UPLOAD REJECTED with reason. |
| Worker timeout | Mark job timed out; allow bounded retry. | PROCESSING TIMEOUT. |
| Provider rate limit | Backoff/fallback if configured; otherwise queue. | RATE LIMITED / QUEUED. |

## 20. Complete flow invariant

At every stage, the invariant is: raw source remains immutable; derived records are linked to sources; case authorization is enforced server-side; model output is schema-validated; failures are explicit; and no inference is represented as fact. This invariant is more important than any individual library choice.

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.
