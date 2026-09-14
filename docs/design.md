# Product & UX Design

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

## 1. Design goals and principles

The interface should help an investigator reason, not merely display data. Every screen should answer a question, provide traceability, and minimize cognitive overload. Design principles: evidence before inference; case context always visible; progressive disclosure; explicit uncertainty; reversible actions; non-color-only semantics; stable identifiers; predictable navigation; asynchronous work states; and security-aware visibility. The visual language should feel analytical and professional rather than cinematic or militarized.

## 2. Information architecture and navigation

Top-level structure: Cases, Search, Alerts, Analysis, Reports, Administration (permission-dependent). Inside a case: Overview, Graph, Timeline, Entities, Evidence, Patterns, Analysis Runs, Notes, Audit. The user should never accidentally move from one case into another without a clear context change. Case ID and case name remain visible in the header. Every entity page exposes a path back to its case and to source evidence.

## 3. Dashboard

The dashboard summarizes authorized cases, recent analysis jobs, unreviewed alerts, extraction failures, and system status. It should not display a global “most criminal” leaderboard. Instead it surfaces actionable work queues: cases needing review, failed processing, new pattern alerts, and recently updated investigations. Cards should expose counts and links to their supporting lists. A small health section reports graph/database/model service status without revealing operational secrets.

## 4. Case workspace

The case workspace is the primary shell. Header contains case name, identifier, status, jurisdiction/metadata allowed for the user, last updated time, and access level. Main content uses tabs. The Overview tab contains a concise case summary, graph size, evidence counts, recent alerts, and current analysis status. A side panel can show saved investigation notes. All content is permission-filtered on the backend.

## 5. Graph explorer design

The graph view is the central investigative surface. Default mode is a bounded neighborhood around a selected entity, not an unlimited graph dump. Controls: relationship-type filters, evidence-status filters, time range, hop depth, confidence threshold, entity type filters, and layout choice. Nodes show entity type and a stable human-readable label. Edges show relationship type and a small evidence state indicator. Selecting a node opens a detail drawer rather than navigating away immediately. Large graphs are handled through server-side subgraph queries and client-side virtualization/aggregation.

## 6. Evidence and provenance UX

Evidence is first-class. Clicking a relationship reveals: relationship status (observed/inferred/confirmed/rejected), confidence type, provenance count, source records, timestamps, and any investigator notes. A source-backed edge must link to the exact source record. An inferred edge must link to the model run and feature context. The interface must never visually imply that an inferred edge is as authoritative as a source-backed edge. Dashed styling is useful, but a text/label status is also required for accessibility.

## 7. Entity view

An entity page contains canonical identity, aliases, identifiers, associated cases, relationship summary, centrality metrics, detected patterns, predictions involving the entity, timeline activity, and evidence. The page should distinguish “known attributes” from “derived metrics” and “model inferences.” Editing canonical identity is a controlled action and must preserve prior source mentions. Entity merging creates an auditable merge decision rather than silently rewriting source records.

## 8. Timeline and temporal design

Timeline view presents events across communications, transactions, document observations, vehicle sightings, and relationship changes. Users can zoom from case-level periods to individual timestamps. Temporal decay affects analytical relevance, but the original source event timestamp is never altered. The UI should display “observed date” separately from “current relevance” so investigators understand why an old record may have a lower analytical weight.

## 9. Search experience

Search supports exact identifiers, normalized names, aliases, case IDs, evidence IDs and broad entity labels. Search results show type, case, identifier fragment, and confidence/status where appropriate. Search must be case-filtered by default. Query terms never become raw database queries. A saved search stores the normalized query structure, filters, and owner, not arbitrary untrusted Cypher.

## 10. Pattern and alert experience

Alerts are written in investigator language: “Rapid fan-out detected,” “Potential circular fund flow,” “High-betweenness bridge links two communities,” or “Potential unobserved association.” Each alert includes severity, analytical basis, contributing nodes/edges, time window, confidence semantics, and a direct investigation action. Avoid labels such as “criminal mastermind” unless a real evidentiary basis exists; the product should say “potential influential node” or “high-priority investigative lead.”

## 11. AI explanation panel

The explanation panel is mandatory for AI-derived outputs. It contains a conclusion, score, score definition, confidence type, contributing features, relevant graph structures, evidence sources, model/version, timestamp, and limitations. Example: “Priority is high because the entity connects three communities, has high betweenness, and participates in two recent fan-out patterns; the GATv2 candidate association is model-inferred and not directly observed.” The panel must support “show supporting evidence” and “show how this was calculated.”

## 12. Human-in-the-loop and overrides

Investigator actions are review decisions, not edits to history. Accepting an extraction or prediction creates a review record. Rejecting it records the reason. Correcting an entity alias links the new canonical mapping to the original mention. The UI should show status transitions such as NEW -> REVIEWED -> CONFIRMED or REJECTED. High-impact actions require confirmation and are audited.

## 13. Empty/loading/error/accessibility states

Empty graph: explain why no results are visible and offer a suggested next action. Loading: show bounded progress and allow navigation away from long jobs. Error: state what failed, whether data changed, and whether retry is safe. Permission denied: do not disclose hidden case existence beyond policy. Accessibility: keyboard navigation, semantic buttons, focus states, labels, readable error text, and redundant visual encoding for hard/soft/inferred evidence.

## 14. Frontend component strategy

Use a modern TypeScript React-style architecture or the existing chosen frontend stack, but keep domain components separate from raw visualization components. Recommended boundaries: AppShell, CaseShell, GraphCanvas, GraphToolbar, EntityDrawer, EvidencePanel, Timeline, PatternList, AnalysisRunStatus, SearchBar, PermissionGate, AuditPanel, ReportPreview. Visualization components accept typed view models and do not decide authorization or business logic.

## 15. State management and API interaction

Client state is divided into session/auth state, case context, graph view state, query/filter state, async job state, and transient UI state. Server data should be fetched through a typed client. Optimistic updates are restricted to low-risk presentation settings. Case membership, evidence, predictions and audit history should update only after backend confirmation. Long-running jobs return job IDs and status endpoints instead of blocking the browser.

## 16. Demo UX

The SIH demonstration should be a guided investigation. Start with one case and a small set of seeded evidence. Show extraction from a realistic FIR-like text, then a graph with a visible bridge node and a transaction motif. Open the evidence drawer to prove provenance. Run SNA, then show a GATv2 candidate association labelled “inferred.” Finally reject or review the prediction and open audit history. This story is stronger than showing ten disconnected features.

## 17. Visual hierarchy

Primary emphasis is the selected entity and its immediate network. Secondary emphasis is evidence status and actionable analytical findings. Tertiary content includes raw properties and advanced metrics. Avoid giant score cards without context. Use consistent badges for Observed, Corroborated, Inferred, Rejected and Needs Review. The graph should be calm at default zoom and become more detailed only when requested.

## 18. Design acceptance checklist

| Area | Acceptance condition |
| --- | --- |
| Navigation | User can move Cases -> Case -> Graph -> Entity -> Evidence -> back without losing context. |
| Graph | Default graph is bounded; filters are explicit; selection has a stable detail drawer. |
| Evidence | Every important edge/insight exposes provenance and confidence semantics. |
| Patterns | Every alert states what pattern was detected and how. |
| AI | Every AI output exposes model/version/limitations. |
| Security | Unauthorized data are not merely hidden visually; backend excludes them. |
| Accessibility | Status never depends on color alone and keyboard navigation works. |
| Demo | Canonical seeded scenario can be replayed with deterministic results. |

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.
