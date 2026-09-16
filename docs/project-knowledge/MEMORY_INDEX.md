# Project Memory & Knowledge Index Manifest

**Project:** SIH26189 — AI-Powered Criminal Network Analysis System  
**Namespace:** `criminal-network-analysis`  
**Supermemory Server:** `http://localhost:6767` (`.supermemory/knowledge.json`)  
**Total Documents Indexed:** 23 Markdown Files (268 Search Chunks)  

---

## Document Taxonomy & Classification

| File Name | Category | Authority | Status | Purpose & Description |
|---|---|---|---|---|
| [`01_SHARED_TYPES.md`](file:///d:/AI-criminal-Network/Useful/01_SHARED_TYPES.md) | `SCHEMA` / `API_CONTRACT` | Canonical | Active | Common TS/Python data contracts, enums, lifecycle states, confidence semantics |
| [`02_DATABASE_SCHEMA.md`](file:///d:/AI-criminal-Network/Useful/02_DATABASE_SCHEMA.md) | `SCHEMA` | Canonical | Active | PostgreSQL relational tables, foreign keys, audit logs, case boundaries |
| [`03_GRAPH_SCHEMA.md`](file:///d:/AI-criminal-Network/Useful/03_GRAPH_SCHEMA.md) | `SCHEMA` | Canonical | Active | Neo4j graph nodes (Person, Case, Evidence), edges, projection rules |
| [`04_API_SPEC.md`](file:///d:/AI-criminal-Network/Useful/04_API_SPEC.md) | `API_CONTRACT` | Canonical | Active | REST/FastAPI endpoints, request/response models, error handling |
| [`05_AI_CONTRACTS.md`](file:///d:/AI-criminal-Network/Useful/05_AI_CONTRACTS.md) | `API_CONTRACT` / `ARCHITECTURE` | Canonical | Active | Agent 1 (Extraction), Agent 2 (Evidence/Graph), Agent 3 (Analytics) contracts |
| [`06_WORKFLOWS.md`](file:///d:/AI-criminal-Network/Useful/06_WORKFLOWS.md) | `IMPLEMENTATION_GUIDANCE` | Supporting | Active | Step-by-step ingestion, entity resolution, SNA & link prediction execution |
| [`07_AUTH_SECURITY.md`](file:///d:/AI-criminal-Network/Useful/07_AUTH_SECURITY.md) | `CORE_RULE` / `CANONICAL_SPEC` | Canonical | Active | Authentication, RBAC, case authorization boundaries, token rules |
| [`08_UI_DATA_CONTRACT.md`](file:///d:/AI-criminal-Network/Useful/08_UI_DATA_CONTRACT.md) | `API_CONTRACT` / `SCHEMA` | Supporting | Active | Frontend Cytoscape.js UI graph data formats & payload schemas |
| [`09_NAMING_CONVENTIONS.md`](file:///d:/AI-criminal-Network/Useful/09_NAMING_CONVENTIONS.md) | `CORE_RULE` / `GUIDANCE` | Canonical | Active | Code, DB table, graph label, and API route naming rules |
| [`10_CROSS_TEAM_DEPENDENCIES.md`](file:///d:/AI-criminal-Network/Useful/10_CROSS_TEAM_DEPENDENCIES.md) | `IMPLEMENTATION_GUIDANCE` | Supporting | Active | Team interfaces, module delivery contracts, integration touchpoints |
| [`README-10files.md`](file:///d:/AI-criminal-Network/Useful/README-10files.md) | `REFERENCE` | Supporting | Active | Manifest and overview for the 10 canonical contract files |
| [`prd.md`](file:///d:/AI-criminal-Network/Useful/prd.md) | `CANONICAL_SPEC` | Canonical | Active | Product Requirements Document, user personas, functional scope |
| [`design.md`](file:///d:/AI-criminal-Network/Useful/design.md) | `ARCHITECTURE` | Supporting | Active | System design, UI/UX interaction models, component layout specs |
| [`trd.md`](file:///d:/AI-criminal-Network/Useful/trd.md) | `CANONICAL_SPEC` | Canonical | Active | Technical Requirements Document, stack choices, performance metrics |
| [`appflow.md`](file:///d:/AI-criminal-Network/Useful/appflow.md) | `DOMAIN_KNOWLEDGE` | Supporting | Active | User flow, UI state diagrams, navigation maps, screen transitions |
| [`backend-schema.md`](file:///d:/AI-criminal-Network/Useful/backend-schema.md) | `SCHEMA` / `ARCHITECTURE` | Canonical | Active | Detailed backend DB & graph schema, indices, relational foreign keys |
| [`implementation-plan.md`](file:///d:/AI-criminal-Network/Useful/implementation-plan.md) | `IMPLEMENTATION_GUIDANCE` | Supporting | Active | Implementation phase roadmap, milestones, and tasks |
| [`tracker.md`](file:///d:/AI-criminal-Network/Useful/tracker.md) | `DECISION` / `HISTORICAL` | Supporting | Active | Progress tracker, decision log, open bugs, active work streams |
| [`rules.md`](file:///d:/AI-criminal-Network/Useful/rules.md) | `CORE_RULE` | Canonical | Active | AI Coding Agent Rules & Engineering Constraints |
| [`security.md`](file:///d:/AI-criminal-Network/Useful/security.md) | `CORE_RULE` / `CANONICAL_SPEC` | Canonical | Active | Detailed security specifications, privacy, data isolation rules |
| [`system-architecture.md`](file:///d:/AI-criminal-Network/Useful/system-architecture.md) | `ARCHITECTURE` | Canonical | Active | High-level system architecture & component interactions |
| [`DOCUMENT_CONSISTENCY_REPORT.md`](file:///d:/AI-criminal-Network/Useful/DOCUMENT_CONSISTENCY_REPORT.md) | `DECISION` / `HISTORICAL` | Supporting | Active | Audit report detailing resolved past document contradictions |
| [`README.md`](file:///d:/AI-criminal-Network/Useful/README.md) | `REFERENCE` | Supporting | Active | Documentation Pack overview, dataset stance, and setup roadmap |
| [`RESEARCH_KNOWLEDGE_BASE.md`](file:///d:/AI-criminal-Network/docs/project-knowledge/RESEARCH_KNOWLEDGE_BASE.md) | `DOMAIN_KNOWLEDGE` / `REFERENCE` | Supporting | Active | Academic research knowledge base: CrimeGraphNet, CrimeGNN, Street-Level Crime GRL |

---

## Authority & Conflict Precedence

```text
Canonical Specifications (01-05, PRD, TRD, Rules, Security)
                     ↓
Supporting Specifications (06, 08, 10, Design, Appflow)
                     ↓
Historical Decisions & Persistent Agent Memory
```
