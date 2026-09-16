# AI Project-Memory Architecture Implementation Plan

This plan establishes a token-efficient, local-first persistent AI memory & context architecture for the **SIH26189 AI-Powered Criminal Network Analysis System**.

## System Overview & Objectives

The goal is to provide Antigravity with instant access to project constraints while keeping token usage minimal. The 23 existing project specification files (~170 KB total text) will **not** be dumped into the system prompt. Instead, we establish a strict 3-tier hierarchy:

1. **Antigravity Rules** (`.agents/rules/core-project-rules.md`): Small (<4 KB), always-on, non-negotiable constraints.
2. **Antigravity Skills** (`.agents/skills/project-memory/SKILL.md`): Workflow instructions teaching the agent when, what, and how to retrieve context or write memory.
3. **Self-hosted Supermemory Engine & MCP** (`.agents/mcp_config.json`): Local server (`http://localhost:6767`) and tool interface for targeted semantic search over project knowledge and persistent agent memories.

```text
                    ANTIGRAVITY
                         |
          +--------------+--------------+
          |              |              |
        RULES          SKILLS          MCP
          |              |              |
      hard rules    task-specific   Supermemory
                                     |
                           +---------+---------+
                           |                   |
                     Project Knowledge    Persistent Memory
```

---

## User Review Required

> [!IMPORTANT]
> **Source-of-Truth Preservation**: The 23 original Markdown files in `Useful/` will remain untouched as source-of-truth reference material. Copies/references are organized under `docs/project-knowledge/`.

> [!IMPORTANT]
> **Network/Offline Note**: The official remote shell installer (`curl -fsSL https://supermemory.ai/install`) requires external host resolution. To ensure a 100% reliable, zero-dependency, local-first environment, we implement a lightweight local Supermemory Python server and MCP adapter storing data locally in `.supermemory/` on `http://localhost:6767`.

---

## Document Taxonomy & Classification (23 Files)

Every project Markdown file is classified with metadata (`authority`, `status`, `category`):

| File Name | Category | Authority | Status | Purpose |
|---|---|---|---|---|
| `01_SHARED_TYPES.md` | `SCHEMA` / `API_CONTRACT` | Canonical | Active | Shared TS/Python data contracts |
| `02_DATABASE_SCHEMA.md` | `SCHEMA` | Canonical | Active | PostgreSQL relational tables & constraints |
| `03_GRAPH_SCHEMA.md` | `SCHEMA` | Canonical | Active | Neo4j graph nodes, edges & projection rules |
| `04_API_SPEC.md` | `API_CONTRACT` | Canonical | Active | REST/FastAPI endpoints & schemas |
| `05_AI_CONTRACTS.md` | `API_CONTRACT` / `ARCHITECTURE` | Canonical | Active | Agent 1, Agent 2, Agent 3 contract specs |
| `06_WORKFLOWS.md` | `IMPLEMENTATION_GUIDANCE` | Supporting | Active | Ingestion, Entity Resolution & SNA workflows |
| `07_AUTH_SECURITY.md` | `CORE_RULE` / `CANONICAL_SPEC` | Canonical | Active | Security, RBAC & case authorization boundaries |
| `08_UI_DATA_CONTRACT.md` | `API_CONTRACT` / `SCHEMA` | Supporting | Active | Cytoscape.js UI graph data formats |
| `09_NAMING_CONVENTIONS.md` | `CORE_RULE` / `GUIDANCE` | Canonical | Active | Code, DB, Graph & API naming rules |
| `10_CROSS_TEAM_DEPENDENCIES.md` | `IMPLEMENTATION_GUIDANCE` | Supporting | Active | Team interfaces & module delivery contracts |
| `README-10files.md` | `REFERENCE` | Supporting | Active | Overview/manifest of 10 contract files |
| `prd.md` | `CANONICAL_SPEC` | Canonical | Active | Product Requirements Document |
| `design.md` | `ARCHITECTURE` | Supporting | Active | System design & UI/UX interaction models |
| `trd.md` | `CANONICAL_SPEC` | Canonical | Active | Technical Requirements Document & stack specs |
| `appflow.md` | `DOMAIN_KNOWLEDGE` | Supporting | Active | User flow & screen state transitions |
| `backend-schema.md` | `SCHEMA` / `ARCHITECTURE` | Canonical | Active | Backend DB/Graph schema & index details |
| `implementation-plan.md` | `IMPLEMENTATION_GUIDANCE` | Supporting | Active | Implementation phase roadmap & tasks |
| `tracker.md` | `DECISION` / `HISTORICAL` | Supporting | Active | Progress tracker & decision log |
| `rules.md` | `CORE_RULE` | Canonical | Active | AI Coding Agent Rules & Engineering Constraints |
| `security.md` | `CORE_RULE` / `CANONICAL_SPEC` | Canonical | Active | Data isolation, security & privacy rules |
| `system-architecture.md` | `ARCHITECTURE` | Canonical | Active | High-level system architecture & diagrams |
| `DOCUMENT_CONSISTENCY_REPORT.md` | `DECISION` / `HISTORICAL` | Supporting | Active | Audit report of resolved spec contradictions |
| `README.md` | `REFERENCE` | Supporting | Active | Documentation Pack overview & dataset stance |

---

## Proposed Changes

### Component 1: Antigravity Core Rules

#### [NEW] [.agents/rules/core-project-rules.md](file:///d:/AI-criminal-Network/.agents/rules/core-project-rules.md)
- Contains non-negotiable core invariants (< 4,000 characters):
  1. **Hierarchy of Truth**: `canonical > supporting > historical`. Memory must never override canonical specs.
  2. **Zero Schema Fabrication**: Never invent DB/Graph fields or endpoint parameters.
  3. **Inferred Edge Isolation**: Inferred relationships/predictions must never overwrite source-backed evidence.
  4. **Security & Scope**: Server-side case scope enforcement; case data is strictly isolated from AI memory.
  5. **No Fake Completeness**: Clearly label synthetic data, research benchmarks, and future integrations.
  6. **Selective Memory Retrieval**: Use Supermemory search and Skills for targeted context loading.

---

### Component 2: Memory Retrieval & Write Skill

#### [NEW] [.agents/skills/project-memory/SKILL.md](file:///d:/AI-criminal-Network/.agents/skills/project-memory/SKILL.md)
- Guides Antigravity on interacting with the Supermemory layer:
  - **Retrieval Policy**: Execute targeted queries only when context is required; set top-k to 1-3 chunks.
  - **Memory Write Policy**: Store only durable architectural decisions, verified lessons, or stability conventions. Never store transient chat, speculative ideas, or case data.
  - **Conflict Resolution Protocol**: Report discrepancies between memory and canonical documents.

---

### Component 3: Local Supermemory Engine & MCP Server

#### [NEW] [scripts/supermemory_server.py](file:///d:/AI-criminal-Network/scripts/supermemory_server.py)
- Standalone Python service providing:
  - Local HTTP server running at `http://localhost:6767`.
  - JSON vector & BM25 indexing engine saved in `.supermemory/`.
  - Indexing runner that ingests all 23 documents into the `criminal-network-analysis` namespace with full metadata.
  - Search & Retrieval API endpoints (`/search`, `/documents`, `/memory`).
  - MCP stdio integration for Antigravity tool binding.

#### [NEW] [.agents/mcp_config.json](file:///d:/AI-criminal-Network/.agents/mcp_config.json)
- Configures Antigravity's MCP connection to Supermemory:
  - `search_project_knowledge`: Search project specification docs.
  - `get_canonical_document`: Fetch specific canonical documents by path/name.
  - `store_project_memory`: Save durable architectural decisions or insights.
  - `search_project_memory`: Query persistent project memories.

---

### Component 4: Project Documentation & Index Manifest

#### [NEW] [docs/project-knowledge/MEMORY_INDEX.md](file:///d:/AI-criminal-Network/docs/project-knowledge/MEMORY_INDEX.md)
- Complete manifest mapping all 23 files, categories, authority, and Supermemory index status.

#### [NEW] [docs/project-knowledge/PROJECT_MEMORY_README.md](file:///d:/AI-criminal-Network/docs/project-knowledge/PROJECT_MEMORY_README.md)
- Developer guide explaining the 3-tier memory architecture, tool usage, and maintenance.

---

## Verification Plan

### Automated Verification
1. **Rule Size Check**: Verify `.agents/rules/core-project-rules.md` is well below the 12,000 character limit.
2. **Supermemory Server Health**: Execute `python scripts/supermemory_server.py --health` and verify HTTP response on `http://localhost:6767`.
3. **Indexing Verification**: Run document ingestion script to verify all 23 files are indexed under `criminal-network-analysis`.
4. **Search Quality Verification**: Perform test queries (Architecture, Schema, Graph, API, Security, Workflows) and verify top-3 returned document precision.
5. **MCP Connectivity Check**: Verify JSON-RPC MCP responses for `search_project_knowledge` and `store_project_memory`.

### Manual Verification
- Test query resolution for domain-specific questions to confirm token efficiency (< 2 KB injected context per query vs 170 KB full dump).
