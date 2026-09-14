# Executable Implementation Plan

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

## 1. Planning principles

The recovered project should not be implemented in the earlier “everything at once” order. The critical path is: canonical demo data -> safe schema -> graph projection -> investigator graph UI -> explainable SNA/patterns -> optional ML -> security hardening -> integrated demo. Features that do not improve this path are deferred. Every phase has an exit criterion. A phase is not complete because files exist; it is complete because behavior is tested.

## 2. 6-person allocation

| Person | Primary ownership | Secondary |
| --- | --- | --- |
| Member A | Data schemas + synthetic generators | Ingestion tests |
| Member B | Public dataset preprocessing + document corpus | Provenance/data quality |
| Member C | Backend/API + PostgreSQL | Auth/audit |
| Member D | Graph/Neo4j + Agent 2 logic | SNA/pattern engine |
| Member E | Agent 1/NLP + model evaluation | GATv2 experiments |
| Member F | Frontend/Cytoscape + UX | Integration/demo/security UI |

## 3. Phase 0 — Repository bootstrap

Objective: turn the current prototype into a controlled repo. Tasks: freeze current working code; create docs folder; create tracker and rules; add `.env.example`; remove hardcoded credentials from code; establish tests and formatting; record existing prototype capabilities and known bugs. Exit: repository starts in a documented local environment; existing graph demo still renders; security-sensitive literals are removed. Rollback: keep the last known working prototype tag.

## 4. Phase 1 — Canonical data and schema

Objective: define the minimum relational and graph schema before more code. Tasks: migrations, case/member tables, documents, entities, relationships, evidence, model runs, predictions, alerts, audit. Create JSON schemas for extraction output and synthetic streams. Exit: migrations apply cleanly; fixtures load; schema contract tests pass. Dependency: Phase 0.

## 5. Phase 2 — Ingestion and source management

Objective: safely ingest deterministic demo data plus selected public Indian contextual datasets. Tasks: document upload, structured import, schema validation, hashing, storage metadata, background job. Exit: one FIR-like document and one structured dataset can enter a case and produce tracked processing states. Risks: file parser variability and scope creep. Do not add arbitrary source formats without a reason.

## 6. Phase 3 — Agent 1 extraction

Objective: convert unstructured text into typed extraction objects. Tasks: OCR adapter if required, text normalization, entity and relationship schema, prompt/schema tests, provenance spans, malformed-output handling, provider abstraction. Exit: benchmark sample reaches agreed extraction metrics or, where no labels exist, passes a structured evaluation set reviewed by the team. Failure path is explicit.

## 7. Phase 4 — Entity resolution + Agent 2

Objective: connect mentions safely. Tasks: alias normalization, identifier canonicalization, deterministic matching, fuzzy candidate similarity (Jaro-Winkler, Levenshtein), Dedupe vector embedding distance, review queue for ambiguous matches (< 0.85 configurable threshold), evidence linkage, graph projection. Subjective Logic (b,d,u) consensus operators are implemented as planned features and validated with mathematical test suites before production evidence fusion. Exit: synthetic cases with known aliases resolve to intended canonical entities and false-merge tests fail safely.

## 8. Phase 5 — Graph and analytics

Objective: deliver the core investigative surface before ML. Tasks: Neo4j repositories, bounded neighborhood queries, shortest paths, components, centrality, communities (Louvain / Label Propagation), K-core, deterministic patterns. Exit: canonical demo graph renders and analytics match NetworkX/reference calculations on test fixtures. Risks: graph visual overload and slow unrestricted traversals.

## 9. Phase 6 — Frontend investigation workflow

Objective: make the system usable end-to-end. Tasks: case shell, graph explorer, entity drawer, evidence panel, timeline, alerts, analysis run status, search, filters. Exit: an investigator can execute the canonical demo journey without developer intervention. The UI never performs data authorization itself.

## 10. Phase 7 — Agent 3 ML experiment & GNN Benchmarking

Objective: evaluate GATv2 link-prediction performance against classical baselines using criminal network research methodologies (*CrimeGraphNet*, *CrimeGNN*, spatial/temporal representation literature). Tasks:
1. *Dataset & Feature Pipeline:* Construct node and edge feature matrices incorporating side information (relationship types, observation frequency, recency indicators, evidence logic scores `b,d,u`, spatial/jurisdictional attributes, and temporal activity profiles).
2. *Imbalance & Sampling:* Apply weighted loss functions and negative edge sampling to handle class imbalance (*CrimeGraphNet*).
3. *Baselines Comparison:* Benchmark GATv2 against classical graph heuristics (*Common Neighbors*, *Jaccard Index*, *Adamic-Adar*, *Preferential Attachment*) and a simple Multi-Layer Perceptron (MLP).
4. *Leakage Prevention:* Enforce chronological partitioning for train, validation, and test datasets.
5. *Community Detection Experiment (Optional):* Compare operational SNA community detection (Louvain/Label Propagation) with a GNN-based community detection experiment (*CrimeGNN*) as time/data permit.
6. *Metrics & Reporting:* Measure PR-AUC, Hits@K, and MRR. Exit: documented benchmark report determining whether GATv2 is retained as primary production analytical model or kept as research/experimental component. This is a critical anti-hype gate.

## 11. Phase 8 — Investigative ranking and explanations

Objective: combine analytics into a useful but non-accusatory ranking. Tasks: define ranking feature schema, weight/version config, explanation generator, evidence links, model metadata. Exit: every displayed ranking entry has a reproducible feature breakdown and provenance. No single score is labelled probability of guilt.

## 12. Phase 9 — Security hardening

Objective: remove prototype security shortcuts. Tasks: authentication, role and case authorization, CORS, CSRF/session controls as applicable, secure upload handling, path safety, dependency review, secret management, audit logs, log redaction, graph query allowlists, LLM prompt-injection defenses, case isolation tests. Exit: adversarial test suite passes key security invariants.

## 13. Phase 10 — Integration and regression

Objective: prove the pieces work together. Test: case creation -> upload -> extraction -> resolution -> graph -> analysis -> review -> export. Run deterministic demo twice and compare key outputs. Verify failure paths for Neo4j, LLM provider, malformed output, invalid file and unauthorized case. Exit: integrated demo passes without manual database edits.

## 14. Phase 11 — Demo preparation

Objective: package a compelling, honest SIH demonstration. Create a canonical seeded case, a scripted sequence of investigator questions, fallback screenshots or local snapshots, architecture diagram, ML evaluation table, dataset provenance note and known-limits slide. Do not claim live government integration or real police CDR. The demo should be reproducible by another team member from the repo.

## 15. Critical path and parallelization

Critical path: schema -> data -> extraction -> entity resolution -> graph -> analytics -> UI -> security -> demo. Parallel work: frontend shell can start once API contracts are stable; synthetic generator and public-data preprocessing can proceed alongside schema; GAT experiment can run once a stable graph fixture exists. Security starts at bootstrap for secret handling and input validation, then hardens later. The biggest blocker is not model training; it is getting a reliable evidence-to-graph path.

## 16. AI coding agent workflow

Every implementation session begins by reading tracker.md, the relevant requirement, design.md, trd.md, system-architecture.md, and backend-schema.md as needed. The agent inspects current code, tests, and dependencies, proposes the smallest safe change, implements it, runs tests/type checks, checks security implications, updates tracker.md and records an ADR if architecture changed. It never invents an endpoint or schema field because it is convenient. It must report unverified assumptions.

## 17. Phase exit-criteria matrix

| Phase | Exit criterion | Do not proceed when |
| --- | --- | --- |
| Bootstrap | Prototype starts with documented config | Secrets still hardcoded or tests unavailable |
| Schema | Migrations + schema fixtures pass | Entity/relationship semantics still ambiguous |
| Ingestion | Validated demo sources tracked end-to-end | Upload can bypass case ownership |
| Extraction | Structured output is schema-valid | Malformed model output enters DB |
| Graph | Reference metrics match | Graph is rebuilt by destructive global delete |
| UI | Canonical workflow is usable | Core interactions depend on hidden developer steps |
| ML | Benchmark report exists | Claim of improvement is based on one anecdotal example |
| Security | Case-isolation tests pass | Frontend-only authorization remains |
| Demo | Second machine can replay | Live external service is a hidden dependency |

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.
