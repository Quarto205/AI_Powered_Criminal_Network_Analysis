---
name: project-memory
description: Instructs the agent on how and when to retrieve context and write persistent memory.
---
# Project Memory & Context Retrieval Guide

## Retrieval Policy
- Execute targeted queries using `search_project_knowledge` or `search_project_memory` only when context is required for architecture, API schemas, or workflows.
- Set `limit=3` for targeted chunk retrieval to save tokens.
- Rely on the retrieved knowledge chunks rather than assuming standard templates.

## Memory Write Policy
- Use `store_project_memory` to store durable architectural decisions, verified lessons, or stability conventions.
- Never store transient chat, speculative ideas, or actual case data (PII) in memory.

## Conflict Resolution Protocol
- If there is a discrepancy between retrieved memory and canonical project documents, canonical project documents take precedence.
- Report any discrepancies to the user.
