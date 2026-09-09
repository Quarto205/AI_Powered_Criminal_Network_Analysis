# Living Project Tracker

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

## 1. Last known system state

The project already has a prototype concept and a working graph plumbing path from Neo4j through FastAPI to Cytoscape. The prototype supports basic graph loading and degree/betweenness calculation. It is not security-complete, not production-ready, and not yet the full investigation workflow. The current documentation phase is now authoritative. Next implementation work should start from schema and safety cleanup rather than adding more architecture buzzwords.

## 2. Current phase

**PHASE: Documentation consolidation -> repository bootstrap.** The immediate goal is to transform the recovered architecture into a controlled implementation contract. Do not begin broad feature work until the schema, folder structure, API contract and tracker are committed.

## 3. Completed work

| ID | Completed | Status | Evidence/state |
| --- | --- | --- | --- |
| DONE-001 | Recovered project architecture and 3-agent concept | DONE | Conversation history reviewed. |
| DONE-002 | Confirmed Neo4j + FastAPI + Cytoscape prototype path | DONE | Existing prototype referenced in recovered chat. |
| DONE-003 | Identified GATv2 as link-prediction component, not kingpin detector | DONE | Architecture correction recorded. |
| DONE-004 | Established Indian-first dataset strategy | DONE | Public + synthetic + international benchmark tiers. |
| DONE-005 | Identified overengineering risks | DONE | Kafka/microservices/enterprise security stack deferred. |

## 4. Active task board

| Task ID | Task | Status | Owner | Priority | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BOOT-001 | Create docs/ and commit canonical specifications | PLANNED | Lead | P0 | None | Must happen first. |
| BOOT-002 | Freeze working prototype/tag | PLANNED | Backend | P0 | None | Create rollback point. |
| SEC-001 | Move credentials to env/secret config | PLANNED | Backend | P0 | BOOT-002 | No hardcoded secrets. |
| DB-001 | Implement PostgreSQL migrations | PLANNED | Backend | P0 | BOOT-001 | Follow backend-schema.md. |
| ING-001 | Implement safe document/CSV ingestion | PLANNED | Data+Backend | P0 | DB-001 | Deterministic demo first. |
| OCR-001 | Implement OCR preprocessor & text extraction | VERIFIED | ML | P0 | ING-001 | 22 unit tests passing, magic bytes, digital/scanned PDF, provenance offsets, Agent 1 handoff. |
| NLP-001 | Implement Agent 1 structured extraction | VERIFIED | ML | P0 | ING-001 | 34 unit tests passing, schemas, fallback, offset verification. |
| DOC-PIPELINE-001 | Implement Document Task Pipeline & E2E Integration | VERIFIED | Backend+ML | P0 | OCR-001,NLP-001 | 17 integration tests passing (73/73 full suite), RECEIVED->VALIDATED->PROCESSING->EXTRACTED lifecycle, case isolation, storage abstraction, FastAPI endpoint. |
| ER-001 | Implement entity normalization/resolution | PLANNED | ML+Graph | P0 | NLP-001 | Review low confidence. |
| GRAPH-001 | Rebuild Neo4j projection safely | PLANNED | Graph | P0 | ER-001 | Idempotent MERGE. |
| SNA-001 | Implement analytics baseline | PLANNED | Graph | P0 | GRAPH-001 | Reference-test against NetworkX. |
| UI-001 | Integrate graph explorer and evidence drawer | PLANNED | Frontend | P0 | GRAPH-001 | Case-scoped APIs only. |
| ML-001 | Benchmark GATv2 against classical baselines | PLANNED | ML | P1 | GRAPH-001 | Leakage checks mandatory. |
| RANK-001 | Implement investigative ranking + explanations | PLANNED | ML+Backend | P1 | SNA-001,ML-001 | Non-accusatory wording. |
| DEMO-001 | Create deterministic canonical SIH scenario | PLANNED | All | P0 | SNA-001,UI-001 | Replay twice. |

## 5. Known bugs / technical debt from prototype

Known prototype debt includes hardcoded Neo4j credentials, permissive `allow_origins="*"`, destructive graph purge during loader startup, CREATE-based writes that can duplicate records, limited graph API validation, and graph metrics computed in an in-memory NetworkX projection for every request. These are documented prototype limitations and should be addressed before any claim of secure or production-like behavior. Do not blindly delete the old prototype until its behavior is captured by regression tests.

## 6. Dataset status

| Dataset/source | Tier | Use | Status |
| --- | --- | --- | --- |
| NCRB Crime in India | Indian public | Crime context + spatial/temporal enrichment | PLANNED |
| ICDAR Indian FIR dataset | Indian target-domain | OCR/document extraction benchmark | PLANNED / validate exact current access/licensing |
| KING Indian legal corpus | Indian target-domain | Legal NER/entity context | PLANNED |
| Indian court corpus subset | Indian target-domain | Legal language/retrieval context | DEFERRED unless needed |
| Indian ANPR/plate datasets | Indian-adjacent | Plate recognition benchmark | DEFERRED |
| Synthetic Indian CDR/financial/vehicle graph | Synthetic | Graph/GNN ground truth | P0 |
| AMLSim | International benchmark | AML graph validation | P1 |
| Elliptic | International benchmark | Illicit transaction graph ML | P1 |
| Sicilian Mafia network | International benchmark | Covert-network topology validation | P1 |
| Telecom Italia/Reality Mining | International benchmark | Temporal interaction experiments | DEFERRED unless useful |

## 7. Model-training and evaluation status

Agent 1: no fine-tuning assumed; structured extraction benchmark required. Entity resolution: deterministic + similarity benchmark required. Agent 3 SNA: deterministic reference calculations required. GATv2: experimental until held-out evaluation is complete. Ranking: not a “guilt model”; evaluation must focus on prioritization usefulness and calibration on labelled synthetic scenarios where available.

## 8. Architecture decisions

| Decision | Status | Date/trigger |
| --- | --- | --- |
| Use modular monolith + ML worker | FINAL | Current SIH scope |
| Neo4j for graph | FINAL | Existing working prototype |
| PostgreSQL for system-of-record | FINAL | Canonical schema decision |
| Three conceptual agents, deterministic services underneath | FINAL | Agent critique |
| GATv2 for association prediction only | FINAL | Architecture correction |
| Kafka | DEFERRED | Scale need not demonstrated |
| Voice console | DEFERRED/P1 | Only after core workflow works |
| Full Dempster-Shafer/Subjective Logic | PLANNED / VALIDATION REQUIRED | Implement with mathematical test suite before evidence fusion |

## 9. Rejected approaches

Rejected: “GATv2 detects kingpins” as a core scientific claim; “NCRB trains the whole criminal graph model”; treating Kaggle crime rows as law-enforcement CDR; arbitrary raw Cypher generated by an LLM; frontend-only authorization; global destructive graph reloads; and an enterprise architecture requiring many services for a student team. These decisions should not be re-litigated unless new evidence changes the constraints.

## 10. Open questions

| Question | Owner | Status | Decision trigger |
| --- | --- | --- | --- |
| Exact final official SIH problem statement wording | Lead | OPEN | Verify on official portal before final presentation. |
| Which Indian FIR dataset can be downloaded under current terms? | Data | OPEN | Validate source, license, size. |
| Does GATv2 beat classical link prediction? | ML | OPEN | Benchmark report. |
| What confidence model is simplest and correct? | ML/Graph | OPEN | Mathematical test suite. |
| Is voice worth demo risk? | Frontend | OPEN | Only if core flow is stable. |
| Need Redis job queue? | Backend | OPEN | Measure workload first. |

## 11. Demo readiness checklist

The demo is ready only when the team can perform the complete scripted investigation from a clean environment, with no manual Neo4j edits, no hidden external service, and no undeclared fake data. The demo package must include deterministic seed files, environment instructions, seeded database loader, API startup, frontend startup, model artifact/config, test command, known-limits note and a short fallback procedure.

## 12. Update rules for future sessions

Every meaningful change updates this tracker. “DONE” requires evidence. “IN PROGRESS” requires a current owner and next action. “BLOCKED” requires the blocker. “REJECTED” records why. “DEFERRED” records when it can be revisited. After a coding session, append the last known system state and list tests actually run. Never write “works” without verification.

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.

## 13. Known prototype security exceptions to remove
The recovered prototype contains several shortcuts that are explicitly not acceptable as the final baseline: hardcoded Neo4j credentials; permissive CORS; destructive global graph deletion during loading; unscoped graph endpoints; and direct graph/database usage from application code without a clean repository boundary. These items are not “nice-to-have” cleanup. They are blockers for a credible secure prototype because they can cause data loss, cross-case exposure or accidental secret leakage.

## 14. Evidence and provenance progress ledger
Track provenance maturity separately from graph volume. The target is not “more nodes.” The target is that each important edge can answer: what source created this, what extraction or normalization step created it, when was it observed, what confidence type was assigned, whether another source corroborated or refuted it, and whether an investigator reviewed it. A graph with 10,000 nodes and weak provenance is less useful than a smaller graph where each important conclusion can be audited.

## 15. ML experiment ledger template
Every ML experiment added to the project must create a row with experiment ID, task, dataset/version, positive/negative construction, train/validation/test policy, baseline, model configuration, random seed, metrics, observed result, interpretation, and decision. Example: `EXP-GAT-001` can compare Common Neighbors, Jaccard and GATv2 for missing-edge prediction on a synthetic Indian criminal graph. The decision is not “GATv2 is better” unless the measured result supports it across the chosen evaluation protocol.

## 16. Dataset validation checklist
Before a dataset becomes a dependency, record its original source, retrieval date, exact version, license/usage terms, file format, fields, approximate size, labels, geographic/context fit, known preprocessing, graph-conversion method, and whether it is public, de-identified, synthetic or research-only. A Kaggle reupload is not automatically equivalent to an official source. When an original source can be used, prefer it and preserve the provenance chain. Never describe international benchmark data as Indian operational evidence.

## 17. Reproducibility checklist
A clean-room demo run should be possible from a tagged commit. The seed data, schema version, model artifact/version, configuration and expected result checksums are recorded. The canonical demo must not depend on an investigator manually editing Neo4j. A second run should produce the same case graph counts and the same or explicitly tolerance-bounded analytical ranking. Any intentional nondeterminism must be documented rather than hidden.

## 18. Weekly or milestone review questions
Before a milestone is closed, ask: Is the end-to-end investigator journey usable? Are important relationships traceable to evidence? Are inferred and observed states distinct? Can a user from Case A see Case B? Can the system recover from an unavailable AI provider? Does the graph query remain bounded? Does the ML claim have a baseline? Are synthetic data clearly labelled? Did implementation add infrastructure that the team cannot demonstrate? These questions prevent progress from becoming feature-count inflation.

## 19. “Do not accidentally redo” registry
Do not repeat the following investigations unless new evidence changes their status: public Indian operational CDR availability is limited at the required granularity; NCRB is not a person-to-person criminal graph; GATv2 should not be framed as a kingpin oracle; Kafka is not required for the initial SIH prototype; arbitrary LLM-generated Cypher is unsafe; OmniRoute is optional infrastructure rather than a core dependency; claude-mem is development memory rather than case storage; and the architecture should remain a modular monolith plus small worker boundary unless a measured need forces revision.

## 20. Immediate next session handoff
The next coding session should begin with `BOOT-001`, `BOOT-002`, and `SEC-001`: commit the docs, freeze/tag the existing prototype, and remove hardcoded security-sensitive configuration. After that, implement database migrations and the canonical typed contracts. Only when those contracts are stable should the existing Neo4j/Cytoscape path be migrated to the new repository/API boundaries. This ordering reduces the risk that frontend or ML work will force schema changes later.
