# Security Architecture & Threat Model

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

## 1. Security objective

The application handles investigative data. The design target is not “NSA-grade” marketing language; it is a concrete threat model suitable for a student prototype that can mature later. The most important properties are case isolation, controlled access, provenance integrity, secure handling of uploaded artifacts, prevention of prompt/data injection, and auditability. The security plan must distinguish implemented prototype controls from production-grade controls that would require additional infrastructure.

## 2. Assets

| Asset | Sensitivity | Primary protection |
| --- | --- | --- |
| Case metadata | High | Authorization + audit |
| FIR/report documents | Critical | Encrypted/secure storage + access checks |
| Phone/account identifiers | Critical | Masking/minimization + case scope |
| Graph relationships | High/Critical | Case-scoped queries + provenance |
| Predictions/rankings | High | Model metadata + role access |
| Audit logs | High integrity | Append-oriented storage + restricted write |
| Credentials/tokens | Critical | Secret storage + redaction |
| Model artifacts/config | Medium/High | Versioning + integrity checks |

## 3. Threat model

Threats include unauthorized investigator access, insider overreach, compromised credentials, malicious uploaded documents, prompt injection, data poisoning, fabricated relationships, provider data leakage, SSRF through integrations, path traversal in uploads, SQL/graph injection, XSS/CSRF, dependency supply-chain risk, accidental cross-case queries, and log leakage. The most dangerous domain-specific failure is a system that turns an unverified model inference into a source-backed-looking relationship.

## 4. Trust boundaries

Boundaries exist between browser and API, API and PostgreSQL, API and Neo4j, API/worker and file storage, extraction service and external model provider, and ML worker and stored datasets. Each boundary validates data and identity. The browser is untrusted. Uploaded documents are untrusted. LLM output is untrusted until schema validation. Provider responses are untrusted until content and schema checks pass.

## 5. Authentication and authorization

Authentication can be JWT/session based depending on deployment, but authorization is the critical requirement. Roles define allowed actions; case membership defines object access. Supervisor actions such as case membership changes, entity merges or high-impact exports require elevated permission. ABAC attributes such as jurisdiction or clearance can be added as a second layer. Every sensitive API request checks authorization on the backend, not just at route registration or UI rendering.

## 6. Case isolation

Every domain query accepts or derives a case scope. Repositories should make case filtering difficult to bypass. Graph queries use case constraints, not merely frontend filter settings. Cross-case search is disabled for ordinary users. Test fixtures explicitly attempt to read case B from a user authorized only for case A and must fail. A cached graph result cannot be served across cases without a scoped key.

## 7. Uploaded-document security

Uploads are validated by extension plus MIME/content sniffing where available, stored under generated keys, and never used as executable files. Path traversal is prevented because user file names do not define storage paths. Large files are rejected early. Corrupted PDFs are isolated. If malware scanning is not available in the prototype, document this as a limitation and keep the storage boundary controlled. Extracted text is tagged as untrusted content so it cannot override system instructions.

## 8. AI/LLM threats

Prompt injection may appear inside FIR text, reports, scraped pages or model-retrieved context. Defenses: separate system instructions from source text, delimit source content, minimize tools, use allowlisted structured functions, validate output, refuse unsupported fields, and require authorization outside the model. Data poisoning is mitigated through source quality metadata, dataset versioning, review, and split isolation. Hallucinations are controlled by requiring source references for factual statements and generating from structured evidence rather than free-form memory.

## 9. External provider and OmniRoute/gemini-web2api risk

The application should never depend on a gateway or adapter simply because it is convenient. Use an internal AI provider interface. Before sending a document externally, apply data-minimization and approved-provider policy. OmniRoute can be development infrastructure behind the adapter, not a domain dependency. gemini-web2api is untrusted experimentation and should not receive protected investigative data. Provider logs and retention policies must be treated as external data-processing risks.

## 10. Graph-query security

Do not expose raw Cypher. Use named analytical operations: get_neighbors, shortest_path, community, timeline, pattern_query, candidate_links. Each operation validates parameters, scope and limits. Graph queries have maximum hop counts and result sizes. Dynamic relationship types are allowlisted. Errors returned from Neo4j are sanitized.

## 11. API/web security

Use secure headers, strict CORS, secure cookie/token practices where applicable, CSRF protection for cookie-authenticated sessions, output encoding, XSS-safe rendering, dependency updates, request-size limits, rate limiting and structured error handling. SQL uses parameterization. NoSQL injection defenses are not needed unless a NoSQL database is introduced. SSRF is relevant only if the server fetches URLs; those endpoints should be disabled in MVP or use a strict destination allowlist.

## 12. Logging and audit

Operational logs exclude content and secrets. Audit logs record who did what, to which case/resource, when, result, and request ID. Actions such as login, case creation, upload, export, entity merge, review decision, model execution and permission changes are audited. Model run records support analytical reproducibility. Audit history itself is protected from ordinary edits.

## 13. Encryption and secrets

Use TLS in deployed environments and encryption at rest where supported. Secret values are stored in environment/secret managers, not source control. Developer `.env` files are ignored. A leaked secret must be revocable. Database backups are protected to the same sensitivity class as source data. The prototype may use local services, but production documentation should not imply local passwords are acceptable.

## 14. Risk matrix

| Threat | Likelihood | Impact | Risk | Mitigation | Detection/response |
| --- | --- | --- | --- | --- | --- |
| Cross-case data leak | Medium | Critical | Critical | Case-scoped repositories + tests | Authorization test failures; incident review |
| Prompt injection | High | High | High | Untrusted-data delimiting + tool allowlists | Prompt/output validation logs |
| Hardcoded credential leak | High in prototype | Critical | Critical | Env/secrets + secret scan | CI secret scan; rotate |
| Fabricated relationship | Medium | Critical | Critical | Evidence/provenance separation | Model regression + provenance audit |
| Malicious upload | Medium | High | High | Validation + scanning strategy | Upload rejection/alert |
| Graph injection | Medium | High | High | Structured query builders | Input fuzzing |
| Provider data exposure | Medium | High | High | Provider abstraction + minimization | Provider config review |
| XSS/CSRF | Medium | High | High | Framework protections + CSP/CSRF strategy | Security tests |
| Dependency supply-chain | Medium | High | High | Pinned versions + updates | Dependency scanning |

## 15. Security testing plan

Tests cover unauthorized case access, privilege escalation, malformed uploads, path traversal strings, oversized requests, invalid tokens, stale sessions, XSS payloads in entity names/notes, graph parameter fuzzing, prompt injection content, malformed model JSON, provider failure, audit integrity, and export access. Security testing should happen before the demo; a beautiful graph is irrelevant if the team cannot explain how it prevents cross-case leakage.

## 16. Compliance and ethics stance

The prototype should avoid claiming legal compliance it has not demonstrated. The product is an investigative decision-support tool. Human review remains mandatory. The documentation should state that sensitive identifiers are minimized, access is case-scoped, and outputs are investigative leads. Any real deployment would require agency policy, data-sharing authority, lawful access, retention schedules, and formal security assessment.

## 17. Production uplift path

A future production deployment can add managed identity, stronger device posture, mutual TLS, centralized secret management, HSM-backed keys, security information/event management, immutable audit storage, isolated model inference, hardened object storage, formal incident response and continuous access review. These are future controls, not claims about the current SIH prototype.

## Additional implementation notes and edge cases

## Additional implementation notes and edge cases
The team should prefer explicit states over ambiguous booleans. For example, a document should move through RECEIVED, VALIDATED, PROCESSING, EXTRACTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, or FAILED rather than a single processed=true field. The same principle applies to model runs, predictions, graph snapshots, and investigator overrides. This makes the system easier to debug and prevents a partially completed operation from looking complete.

A relationship also needs more than a confidence number. The application should be able to distinguish an observed relationship, a normalized relationship derived from multiple observations, an investigator-confirmed relationship, and an AI-inferred relationship. Evidence records point back to the source artifact and, where possible, the source location such as a document page, record identifier, or event timestamp. A prediction should carry model version and feature-set version, and should be removable or superseded without deleting the underlying evidence.

The prototype should be intentionally deterministic. Synthetic generators use a fixed seed for the canonical SIH demo scenario, while an alternate seed can be used for stress testing. A regression test should verify that the same demo input produces the same entity counts, expected graph motifs, and stable ranking within a defined tolerance. This is more valuable during judging than a claim of live production intelligence.

Where an LLM is used, the application should send only the minimum necessary content, mark source text as untrusted data, validate structured output against a strict schema, and reject unknown actions or fields. A natural-language request must never become arbitrary database access. Voice features, if demonstrated, should map to a finite set of allowlisted analytical intents rather than free-form Cypher execution.

The team should record architecture decisions in small ADRs. Each ADR states the problem, decision, alternatives, consequences, and review trigger. Examples include choosing Neo4j for graph traversal, using PostgreSQL for case/audit state, retaining GATv2 only behind measurable evaluation gates, deferring Kafka, and using synthetic Indian CDR/financial data because public operational equivalents are not available.
