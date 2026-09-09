# Product Requirements Document

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

## 1. Document purpose

This PRD is the product contract for the prototype. It defines what the investigator can accomplish, what the system must not claim, and how success is evaluated. It is intentionally narrower than the earlier military-grade concept document because the team has a short SIH execution window. The objective is a credible investigation-support workflow that can be demonstrated end-to-end and defended technically.

## 2. Product overview

The product is a case-centric investigative intelligence workspace. An investigator creates a case, imports public/synthetic/demo evidence, reviews extraction, inspects an entity-centric graph, runs network analysis, investigates suspicious patterns, reviews inferred relationships, and follows evidence back to source records. The product unifies fragmented information instead of requiring an investigator to mentally reconcile separate lists and spreadsheets. The graph is an analytical representation of evidence, not a replacement for the source material.

## 3. Problem statement and SIH context

SIH26189 is publicly listed as “AI-Powered Criminal Network Analysis System.” The recovered project history consistently frames the problem as linking fragmented investigative data, extracting entities and relationships, building a network, identifying influential actors, discovering suspicious patterns, and supporting investigators. The product must therefore demonstrate the chain: fragmented inputs -> normalized evidence -> graph -> analytics -> explainable investigative lead. The demo should not depend on live government systems.

## 4. Target users and personas

Primary persona: an authorized investigator who needs to connect people, phones, accounts, vehicles, organizations, locations, incidents, and evidence. Secondary persona: an intelligence analyst who explores communities, timelines, and centrality. Supervisor persona: a reviewer who needs auditability, case-level permissions, and reproducible reasoning. Technical persona: the development team and AI coding agent that need the documentation and tracker to remain synchronized. The product does not assume that every user can see every case.

## 5. Goals

| ID | Goal | Priority | Success signal |
| --- | --- | --- | --- |
| G-001 | Create a case-centric investigative workspace | P0 | Investigator can create/open a case and see only authorized cases. |
| G-002 | Ingest heterogeneous structured and unstructured inputs | P0 | Supported demo inputs become validated records. |
| G-003 | Construct a provenance-aware graph | P0 | Every displayed relationship has source/inference metadata. |
| G-004 | Provide useful graph analytics | P0 | Centrality, communities, paths and patterns are reproducible. |
| G-005 | Demonstrate measurable ML value | P1 | GATv2 link prediction beats or complements classical baselines on held-out data. |
| G-006 | Provide explainable investigative prioritization | P0 | Every ranking has reasons and evidence links. |
| G-007 | Protect sensitive case data | P0 | Case isolation, auth, audit and input validation are enforced server-side. |

## 6. Non-goals

The MVP will not provide autonomous accusation, conviction, suspect guilt classification, unrestricted government-data access, live telecom interception, live banking integration, covert collection capabilities, arbitrary Cypher execution by an LLM, or a multi-cloud enterprise deployment. Kubernetes, Kafka, SPIFFE/SPIRE, formal distributed transaction protocols, advanced temporal/heterogeneous GNNs, and a full command-and-control voice interface are deferred. A future product may add them only after a clear requirement and capacity check.

## 7. Functional requirements

| ID | Requirement | Priority | Acceptance criteria |
| --- | --- | --- | --- |
| FR-001 | Create and manage investigation cases | P0 | Authorized user can create, open, rename, archive and list cases within permission scope. |
| FR-002 | Upload supported evidence files | P0 | PDF/text/CSV/JSON files are type/size validated and linked to a case. |
| FR-003 | Process unstructured text | P0 | Extraction returns schema-valid entities/relations plus provenance and confidence type. |
| FR-004 | Normalize and resolve entities | P0 | Aliases/identifiers can be grouped without overwriting source mentions. |
| FR-005 | Materialize graph | P0 | Graph contains canonical nodes and typed relationships with evidence references. |
| FR-006 | Explore graph | P0 | Investigator can select nodes, inspect neighbors, filter types and open evidence. |
| FR-007 | Run SNA analytics | P0 | Degree, betweenness, eigenvector/PageRank, K-core, communities and paths are available. |
| FR-008 | Detect suspicious motifs | P0 | Fan-in/out, cycles, bursts and temporal patterns can produce explainable alerts. |
| FR-009 | Run GATv2 link prediction | P1 | Candidate associations are generated only for eligible node pairs and labeled inferred. |
| FR-010 | Generate investigative priority | P1 | Ranking combines defined features and shows reasons. |
| FR-011 | Inspect provenance | P0 | Every important edge/insight links to source records or model run metadata. |
| FR-012 | Audit sensitive actions | P0 | Case access, exports, overrides and model-trigger actions create audit events. |
| FR-013 | Export investigator report | P1 | Authorized users can export a concise report containing evidence and analysis context. |

## 8. Non-functional requirements

Security: server-side authorization, case isolation, secure secrets, safe file handling, audit logging, rate limits on expensive operations, and no raw secrets in logs. Reliability: failed processing must result in an explicit status and retriable job rather than a false success. Performance: interactive graph/search/filter operations should feel responsive for the canonical demo graph; heavy extraction and ML are asynchronous. Reproducibility: demo data, model versions and ranking inputs must be fixed and traceable. Maintainability: types, schemas and architecture docs must remain aligned. Explainability: every AI-derived result includes provenance and limitations. Accessibility: keyboard access, readable contrast, text alternatives for status indicators, and non-color-only distinctions for evidence states.

## 9. Core user journeys

Journey A: create case -> upload FIR-like documents -> validate -> extract entities/relations -> review -> graph -> analyze. Journey B: open case -> search entity -> inspect neighborhood -> run shortest path/community analysis -> open evidence. Journey C: receive inferred relationship -> inspect why it was predicted -> compare classical heuristics and model signal -> accept as investigative lead or reject. Journey D: detect suspicious transaction fan-out -> open contributing transactions -> inspect source records -> record a note. Journey E: supervisor reviews audit history and confirms that case isolation and evidence provenance remain intact.

## 10. Data inputs and outputs

Inputs are divided into four categories: real Indian public data; public research benchmarks; synthetic Indian operational data; deterministic demo data. NCRB crime datasets provide aggregate crime context and geographic/temporal dimensions, not person-to-person operational relationships. Indian FIR/legal corpora support extraction and Indian language/legal context. Synthetic CDR, financial, vehicle and relationship data provide ground truth where sensitive operational data are unavailable. Outputs are case records, canonical entities, relationships, evidence references, analytics metrics, pattern alerts, model predictions, investigative-priority explanations, and reports.

## 11. AI and graph capabilities

Agent 1 performs extraction and normalization support. Agent 2 maintains evidence-aware graph state. Agent 3 answers network-level questions. Classical graph analytics are the explainable baseline. GATv2 is a supervised/validated link-prediction component, not a truth engine. The system can show “potential unobserved association,” not “confirmed hidden criminal relationship.” GAT training uses meaningful numerical/categorical features such as entity type, activity/temporal features, centrality, relationship type, frequency, recency, belief/disbelief/uncertainty and projected confidence; raw phone/account IDs are identifiers, not features.

## 12. Investigation workflow

The investigation workflow is deliberately human-in-the-loop: ingest -> validate -> extract -> normalize -> resolve -> graph -> analyze -> review -> act. A source-backed fact and an AI inference remain visually and structurally distinct. An investigator can correct an entity match or reject a prediction, but those actions create new audit/provenance records rather than silently mutating history. The system should show what changed and why.

## 13. Alerts, patterns, search and reporting

Alerts are analytical leads, not criminal findings. Patterns include transaction cycles, fan-in/fan-out, rapid bursts, unexpected co-occurrence, and cross-community bridges. Search should support entity identifiers, names/aliases, case IDs, evidence IDs, and common filter dimensions. Reporting should include case metadata, key entities, important relationships, leading metrics, notable patterns, evidence references, and explicit AI/model limitations.

## 14. Scope by implementation priority

| Scope | Included |
| --- | --- |
| MVP / P0 | Case management; safe ingestion; document parsing; structured extraction; basic entity resolution; Neo4j graph; Cytoscape explorer; centrality/community/path analysis; provenance; audit; deterministic suspicious patterns. |
| P1 enhancement | GATv2 link prediction; investigative ranking; timeline visualization; richer exports; constrained natural-language/voice command intents. |
| Future | Temporal/heterogeneous GNN; live agency integrations; production PKI; advanced data-sharing controls; larger-scale streaming; mobile/tactical clients. |

## 15. Evaluation and success metrics

Product metrics are task completion and reliability metrics: successful case creation, successful ingestion, valid extraction rate, provenance coverage, graph query success, median interactive latency on the demo graph, and reproducible report generation. ML metrics are task-specific: extraction precision/recall/F1 where labels exist; entity-resolution precision/recall; link-prediction PR-AUC, Hits@K or MRR; ranking precision@K when ground truth labels exist; calibration for probabilities. Acceptance thresholds must be measured rather than invented. If the GATv2 model does not beat a strong classical baseline, the feature is still acceptable as a research experiment but must not be marketed as superior AI.

## 16. SIH demo requirements

The canonical demo should run offline or with only local dependencies and a pre-seeded database. It should start from a deterministic set of Indian-context synthetic incidents and public-context enrichment, then show: case creation; ingestion; entity extraction; graph materialization; network visualization; a suspicious pattern; classical SNA; an inferred association; explanation/provenance; investigator rejection or confirmation; and audit history. The demo story should show a decision-support loop, not an autonomous policing narrative.

## 17. Risks, assumptions and open questions

Major risks are data scarcity, entity-resolution errors, false positives, model leakage, ambiguous confidence semantics, visual overload, security mistakes, and scope creep. Assumptions include local/synthetic data for the prototype and authorized users. Open questions that require later validation include the exact final SIH statement wording from the official portal, the legally approved data-access model for any real deployment, the preferred OCR engine for selected Indian scripts, the target benchmark composition for GATv2, and whether a voice interface is worth the demo risk. These must remain visible as open decisions.

## 18. Decision status summary

| Decision | Status | Rationale |
| --- | --- | --- |
| Neo4j + Cytoscape.js | FINAL | Already working and fits graph exploration. |
| PostgreSQL system-of-record | FINAL | Strong case/audit/metadata consistency; graph is not the whole application state. |
| Three agents | PROVISIONAL/FINAL boundary | Keep three conceptual responsibilities but implement ordinary deterministic services where LLM reasoning is unnecessary. |
| Agent 3 = SNA + patterns + GATv2 + ranking | FINAL | Matches recovered reasoning and separates explainable analytics from ML. |
| GATv2 as kingpin detector | REJECTED | Scientifically too strong; use for link prediction/embeddings. |
| Kafka everywhere | DEFERRED | Not justified for six people and a short SIH prototype. |
| Synthetic Indian CDR/financial graph | FINAL for prototype | Sensitive public operational data are not available at required granularity. |
| External LLM direct access to case data | DEFERRED / controlled | Security and provider trust require abstraction and minimization. |

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.
