# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 7: AUTHENTICATION, AUTHORIZATION & SYSTEM HARDENING

Security boundaries are enforced strictly at the API layer, rather than relying on frontend filters.

#### 7.1 Role-Based Access Control (RBAC) [CURRENT/FINAL]

Three core roles are defined:

1. **Investigator:** Authorized to upload documents, search case entities, navigate subgraphs, and read timeline events.
2. **Analyst:** Investigator permissions + authorized to execute SNA calculations, edit notes, and run motif detections.
3. **Supervisor:** Analyst permissions + authorized to modify case memberships, approve entity mergers, override model predictions, and export audit/report ledgers.

#### 7.2 Security Hardening Invariants [CURRENT/FINAL]

- **Upload Boundaries:** File uploads must be restricted to explicitly defined extensions and MIME types. Files are stored under system-generated UUID hashes, rather than the original user filenames, to prevent directory traversal and arbitrary execution.
- **Prompt-Injection Isolation:** To protect the NLP pipeline, all user inputs are wrapped with strict text delimiters (e.g., `"""untrusted_input"""`) to keep them isolated from system execution instructions.
- **Graph Injection Defenses:** Dynamic relationship names or query constructs are checked against strict allowlists before execution. Raw Cypher strings are never accepted from clients.
- **Audit-Trail Integrity:** Every database mutation, export trigger, review override, and access violation must append a record to the `audit_logs` database ledger.
- **Log Redaction:** Full document texts, access tokens, passwords, and raw identifiers (e.g., mobile phone and bank account sequences) must be redacted from system logs.

---

## Related integrity rules from PostgreSQL contract

#### 2.2 Security, Integrity & Mutability Rules

- **Case Tenant Integrity:** Every lookup on any case asset must explicitly include an query filter checking `case_id` membership against the requester's authorized `case_members` map.
- **Immutable Historical Sources:** Raw source tables (`documents`, `document_versions`, `document_chunks`, `events`, `communications`, `transactions`) are strictly append-only. They must never be edited, deleted, or mutated.
- **Traceable Deletions:** Node deletion or entity merge actions are soft deletes. They archive relationships or canonical mappings in the relational tables and update Neo4j projections accordingly, leaving the source records intact.
- **Audit Trail Retention:** The `audit_logs` table is strictly append-only. Modification operations on this table are blocked at the database execution level.
