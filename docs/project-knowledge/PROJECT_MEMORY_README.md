# SIH26189 Persistent AI Project-Memory Architecture

This directory documents the persistent AI project-memory architecture designed for the **SIH26189 AI-Powered Criminal Network Analysis System**.

---

## 1. Context Hierarchy Architecture

To optimize token efficiency and prevent large system prompts, knowledge is separated into 3 tiers:

```text
                    ANTIGRAVITY
                         |
          +--------------+--------------+
          |              |              |
        RULES          SKILLS          MCP
          |              |              |
      hard rules    task-specific   Supermemory Server
                                     |
                           +---------+---------+
                           |                   |
                     Project Knowledge    Persistent Memory
```

1. **Antigravity Rules** ([`.agents/rules/core-project-rules.md`](file:///d:/AI-criminal-Network/.agents/rules/core-project-rules.md)): High-priority non-negotiable invariants (hierarchy of truth, zero schema fabrication, inferred edge isolation, security scope).
2. **Antigravity Skills** ([`.agents/skills/project-memory/SKILL.md`](file:///d:/AI-criminal-Network/.agents/skills/project-memory/SKILL.md)): Instructs the agent on how and when to retrieve context, budgeting queries (top 1-3 chunks), and memory write policies.
3. **Local Supermemory Engine** ([`scripts/supermemory_server.py`](file:///d:/AI-criminal-Network/scripts/supermemory_server.py)): Standalone local server listening on `http://localhost:6767` with vector/TF-IDF indexing stored in `.supermemory/`.
4. **Antigravity MCP Integration** ([`.agents/mcp_config.json`](file:///d:/AI-criminal-Network/.agents/mcp_config.json)): Exposes tools for semantic knowledge search and memory persistence.

---

## 2. MCP Tools Overview

- `search_project_knowledge(query, category=None, limit=3)`: Returns top relevant chunks from indexed project specification documents.
- `get_canonical_document(filename)`: Returns full canonical document content.
- `store_project_memory(content, tags=[])`: Saves durable architectural decisions or engineering findings to `.supermemory/persistent_memory.json`.
- `search_project_memory(query)`: Queries persistent developer memories.

---

## 3. Operating Commands

### Ingest Documents
Re-index all 23 Markdown files into `.supermemory/knowledge.json`:
```bash
python scripts/supermemory_server.py --init
```

### Run HTTP Server
Start local REST server at `http://localhost:6767`:
```bash
python scripts/supermemory_server.py --server
```

### Health & Search Check
```bash
python scripts/supermemory_server.py --health
python scripts/supermemory_server.py --query "database schema case boundary"
```
