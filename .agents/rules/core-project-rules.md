# Core Project Rules: SIH26189 AI-Powered Criminal Network Analysis

These are the non-negotiable core invariants for this project.

1. **Hierarchy of Truth**: `canonical > supporting > historical`. Memory and chat context must never override canonical specifications.
2. **Zero Schema Fabrication**: Never invent Database/Graph fields, relationships, or API endpoint parameters that do not exist in the canonical schemas.
3. **Inferred Edge Isolation**: Inferred relationships and machine learning predictions must never overwrite source-backed evidence.
4. **Security & Scope**: Always enforce server-side case scope. Case data is strictly isolated from AI memory.
5. **No Fake Completeness**: Clearly label synthetic data, research benchmarks, and future integrations. Do not pretend mocked features are fully operational.
6. **Selective Memory Retrieval**: Use Supermemory search and MCP Skills for targeted context loading instead of dumping large files.
