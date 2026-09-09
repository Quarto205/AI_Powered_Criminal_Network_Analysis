# Technical Requirements Document

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

## 1. Technical goals and constraints

The technical architecture must be implementable by six people on an SIH schedule while remaining credible enough to scale conceptually. Primary constraint: the prototype must be demonstrable on a developer machine or simple controlled deployment. Avoid infrastructure that cannot be explained. Prefer a modular monolith for API/domain logic with separate worker processes only where asynchronous or ML execution genuinely benefits from isolation.

## 2. Proposed stack

| Layer | Chosen technology | Why | Alternative not chosen |
| --- | --- | --- | --- |
| Frontend | React + TypeScript + Cytoscape.js | Strong interactive graph ecosystem and type safety. | D3-only would require more graph interaction work; a heavier 3D stack is unnecessary. |
| API | FastAPI + Pydantic | Python aligns with ML and gives typed request/response validation. | Node backend would split language/tooling across teams. |
| System of record | PostgreSQL | Reliable relational case, membership, audit, job and metadata storage. | MongoDB adds schema flexibility where consistency is more valuable. |
| Graph | Neo4j | Efficient traversal, path and relationship modeling; already prototyped. | Only PostgreSQL would make graph queries less natural; switching graph engines adds risk. |
| ML | PyTorch + PyG + GATv2 | Research-friendly graph ML with native GATv2 support for link prediction. | TensorFlow is possible but adds no project benefit here. |
| NLP & Parsing Stack | PaddleOCR + IndicNER + InLegalBERT + Qwen3-4B-Instruct-2507 + E5/IndicSBERT | PaddleOCR handles document OCR; IndicNER/InLegalBERT parse legal entity mentions; Qwen3 handles generative extraction/explanations; E5/IndicSBERT produce text embeddings. | Bespoke end-to-end model fine-tuning is not justified for the SIH timeframe. |
| Entity Resolution | Dedupe + deterministic rules + embeddings | Combines exact identifier rules, fuzzy heuristics, and vector distance. | Pure manual linking or pure fuzzy matching alone. |
| File storage | Local object-like storage for prototype, S3-compatible later | Original files need durable bytes separate from relational metadata. | Storing large binaries directly in graph nodes is wrong. |
| Async jobs | Database-backed worker queue or Redis-backed queue if needed | Enough for document/ML tasks without Kafka overhead. | Kafka is deferred because distributed streaming is not a current blocker. |

## 3. Frontend/backend/ML separation

Frontend owns presentation, interaction, graph rendering, local client state and request orchestration. Backend owns authorization, case isolation, validation, graph access, AI orchestration, audit logging and business rules. ML worker owns training, inference, feature construction and evaluation. No frontend code contains authoritative authorization logic. No ML worker directly writes arbitrary application tables; it reports model-run outputs through typed APIs or controlled persistence interfaces.

## 4. Database strategy

PostgreSQL is the canonical application system-of-record. Neo4j is the analytical graph store and may be rebuilt from canonical relational evidence if needed. Original documents live in object/file storage; metadata lives in PostgreSQL. A single application transaction should not attempt a distributed two-phase commit between PostgreSQL and Neo4j. Instead, graph materialization uses idempotent jobs with a version/status model and can be replayed. A graph snapshot/version records which evidence state it represents.

## 5. Graph database strategy

Neo4j stores canonical entity nodes plus typed relationships. Node identity uses UUID-style stable IDs generated by the application, not raw phone/account strings. Relationships contain source/provenance identifiers, evidence status, confidence fields, timestamps and relationship-specific attributes. Source evidence and inferred predictions are separate relationship states. Graph queries must always be scoped to the current case unless an explicitly privileged cross-case analytical function is added later.

## 6. AI infrastructure and provider abstraction

Application code calls an internal AI service interface such as `extract_entities()`, `summarize_case()`, or `explain_prediction()`. A provider adapter chooses Gemini, OpenAI, a local model, or another approved provider. OmniRoute can sit behind the adapter during development but is not part of the domain contract. gemini-web2api is development experimentation only and is not an approved production dependency. External prompts must be minimized, redacted where possible, logged without case content, and subject to retention/provider policy.

## 7. Agent 1 technical requirements

Input is a validated document chunk or text record plus source metadata. Output is schema-validated entities, aliases, relationships and extraction metadata. OCR (PaddleOCR) is a preprocessor where image/PDF content is required; it is not itself an agent. Agent 1 must not create final graph nodes. Entity IDs are temporary until normalization/resolution. Structured output is validated with Pydantic/JSON Schema. Invalid model output is rejected or repaired under a bounded policy; it is never trusted by default.

## 8. Agent 2 technical requirements

Agent 2 is mostly deterministic domain logic rather than a general-purpose LLM agent. It validates normalized records, manages evidence/provenance, applies confidence semantics, resolves or proposes canonical entities (using deterministic rules, fuzzy heuristics, and Dedupe embedding distances), writes graph state through repository functions, and manages reprocessing. Subjective Logic / Dempster-Shafer `(b,d,u)` consensus math is part of the PLANNED ARCHITECTURE alongside traditional multi-signal confidences; it requires dedicated mathematical validation testing before being trusted for production evidence fusion.

## 9. Agent 3 technical requirements

Agent 3 is a Network Intelligence & Prediction Engine. Pipeline: graph extraction -> SNA -> communities -> deterministic pattern engine -> GATv2 link prediction -> ranking. SNA baseline includes degree, betweenness, eigenvector/PageRank, K-core, components and paths. Community detection uses explainable classical SNA (Louvain / Label Propagation) as the primary operational path; CrimeGNN (`2311.17479v1`) provides research rationale for GNN-derived community representations in criminal networks, maintained as an optional experimental benchmark. Pattern engine detects fan-in/out, cycles, bursts and temporal anomalies. GATv2 operates on feature-rich graph inputs and produces candidate association scores and embeddings. Ranking is a separate function combining defined signals. Every score has a type and calibration status.

## 10. GATv2 model design

Use GATv2 as the primary planned candidate for relational graph learning, informed by domain-specific criminal network link-prediction research (*CrimeGraphNet*, `2311.18543v1`). Architecture choice remains an empirical engineering decision; GATv2 is a planned/core research capability whose final production role is subject to empirical validation against baselines. Node features should include entity-type encoding, activity frequency, temporal aggregates, spatial/jurisdictional features (combining structural, temporal, and spatial signals inspired by graph representation literature `ijgi-13-00229`), selected centrality features and evidence statistics. Edge side information should include relationship classification type, frequency, recency, belief, disbelief, uncertainty and projected confidence. If amount or duration are used, they are normalized by domain. Class imbalance is handled via weighted loss functions and negative sampling (*CrimeGraphNet*). Candidate edges must be generated with negative sampling and leakage-aware time/case splits. Evaluate against common-neighbor/Jaccard/Adamic-Adar/preferential-attachment baselines and simple MLP or GraphSAGE/GCN baselines where capacity allows.

## 11. Search, vector search and embeddings

Do not add a vector database merely because an architecture document lists one. Exact entity search is sufficient for MVP. Semantic retrieval is justified for document explanation/RAG only if a real workflow needs it. If embeddings are used, document the model, vector dimensions, index, case isolation strategy, retention, and evaluation. The graph should remain the authoritative structured representation; vector search is an auxiliary retrieval mechanism.

## 12. Security and auth

Use secure session/token authentication appropriate to deployment. MVP RBAC includes roles such as Investigator, Analyst and Supervisor; case membership provides the primary object-level authorization boundary. An ABAC layer can be added for jurisdiction/clearance attributes if demonstrable. Secrets come from environment/secret storage, never source files. All sensitive endpoints validate case access server-side. CORS is allowlisted. File uploads are type/size validated and scanned. Audit events are append-oriented. Graph-query endpoints expose structured parameters, never raw user-supplied Cypher.

## 13. Observability, testing and deployment

Every async job has an ID and structured status. Logs contain request IDs and non-sensitive identifiers, not document bodies or tokens. Tests cover unit logic, graph repositories, API authorization, entity resolution, pattern detection, ML feature construction, model regression, frontend critical paths and end-to-end demo replay. Deployment should have separate dev/demo/prod-like configurations. CI runs formatting, linting, type checks, tests and dependency/security checks. Docker is optional but useful for reproducible demo packaging.

## 14. Performance and reliability

| Operation class | Expected behavior | Design |
| --- | --- | --- |
| Interactive | Case navigation, bounded graph queries, search | Synchronous API; paginate and limit subgraphs. |
| Short async | Small document extraction, graph rebuild | Background job; visible progress/status. |
| Heavy | Large document sets, GAT inference/training | Worker process; never block browser request. |
| Offline | Model training/evaluation, benchmark generation | Reproducible scripts with versioned configs and seeds. |

## 15. Technology decision status

| Technology/Pattern | Status | Trigger to revisit |
| --- | --- | --- |
| Neo4j | FINAL | Only if graph scale or licensing changes the project economics. |
| PostgreSQL | FINAL | Only if the final use case becomes purely graph and relational state disappears. |
| Kafka | DEFERRED | Revisit only for a real multi-stream demo with concurrent producers. |
| Redis | PROVISIONAL | Use only if job/query load shows value. |
| Full Subjective Logic | PLANNED / VALIDATION REQUIRED | Require a mathematically correct implementation and test suite before production evidence fusion. |
| GATv2 GNN Model | PLANNED / BENCHMARK REQUIRED | Retained as core planned model; benchmark against classical heuristics and MLP to confirm production role. |
| Temporal GNN | DEFERRED | Add only if temporal benchmark shows material improvement. |
| Vector DB | DEFERRED | Add only for a tested semantic retrieval workflow. |
| OmniRoute | OPTIONAL DEV | Remove without application code changes by using provider adapter. |

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.
