# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 2: POSTGRESQL DATABASE SCHEMA [CURRENT/FINAL]

PostgreSQL is the authoritative transactional system of record. Every table, primary key, foreign key constraint, nullability constraint, and database invariant is defined below.

#### 2.1 Table Definitions & Fields

##### users (Identity Data)

- `user_id` (PK, UUID-v4, Required)
- `email` / `username` (VARCHAR, Unique, Required)
- `password_hash` (VARCHAR, Required)
- `account_status` (VARCHAR, Required, e.g., 'ACTIVE', 'SUSPENDED')
- `created_at` (TIMESTAMP, Default: NOW(), Required)
- `updated_at` (TIMESTAMP, Default: NOW())

##### roles (RBAC Roles)

- `role_id` (PK, UUID-v4, Required)
- `name` (VARCHAR, Unique, Required, e.g., 'INVESTIGATOR', 'ANALYST', 'SUPERVISOR')
- `created_at` (TIMESTAMP, Default: NOW())

##### permissions (RBAC Actions)

- `permission_id` (PK, UUID-v4, Required)
- `permission_code` (VARCHAR, Unique, Required, e.g., 'CASE\_CREATE', 'EXPORT\_REPORT')
- `description` (VARCHAR)

##### user\_roles (Join Table) [MISSING/NOT SPECIFIED]

- *Table implicit but schemas/structures not detailed in docs. Do not assume fields beyond standard joins.*

##### cases (Multi-Tenant Boundaries)

- `case_id` (PK, UUID-v4, Required)
- `case_code` (VARCHAR, Unique, Required)
- `title` (VARCHAR, Required)
- `description` (TEXT)
- `status` (VARCHAR, Required)
- `jurisdiction` (VARCHAR, Required)
- `created_by` (FK to `users.user_id`, Required)
- `created_at` (TIMESTAMP, Default: NOW(), Required)

##### case\_members (Authorization Map)

- `case_member_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `user_id` (FK to `users.user_id`, Required)
- `role_in_case` (VARCHAR, Required)
- *Constraint:* Unique combination of (`case_id`, `user_id`)

##### documents (Source Artifact Metadata)

- `document_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `file_type` (VARCHAR, Required)
- `file_hash` (VARCHAR, Required)
- `storage_key` (VARCHAR, Required)
- `status` (VARCHAR, Required, e.g., 'RECEIVED', 'PROCESSING')
- `created_at` (TIMESTAMP, Default: NOW(), Required)
- *Constraint:* Unique `file_hash` within a single `case_id` (prevents double-uploading)

##### document\_versions (Traceability Versions)

- `version_id` (PK, UUID-v4, Required)
- `document_id` (FK to `documents.document_id`, Required)
- `version_hash` (VARCHAR, Required)
- `metadata` (JSONB)
- `created_at` (TIMESTAMP, Default: NOW(), Required)

##### document\_chunks (Parsed Chunks)

- `chunk_id` (PK, UUID-v4, Required)
- `version_id` (FK to `document_versions.version_id`, Required)
- `page_number` (INTEGER)
- `character_span` (VARCHAR)
- `text_hash` (VARCHAR, Required)
- `storage_ref` (VARCHAR, Required)

##### entities (Domain Objects)

- `entity_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `entity_type` (VARCHAR, Required, e.g., 'PERSON', 'PHONE', 'BANK\_ACCOUNT', 'VEHICLE', 'ORGANIZATION', 'LOCATION')
- `canonical_name` (VARCHAR, Required)
- `status` (VARCHAR, Required)
- `created_at` (TIMESTAMP, Default: NOW())

##### entity\_aliases (Alias Log)

- `alias_id` (PK, UUID-v4, Required)
- `entity_id` (FK to `entities.entity_id`, Required)
- `alias_text` (VARCHAR, Required)
- `source_ref` (VARCHAR)

##### entity\_identifiers (Masked Target Values)

- `identifier_id` (PK, UUID-v4, Required)
- `entity_id` (FK to `entities.entity_id`, Required)
- `type` (VARCHAR, Required, e.g., 'PHONE\_NUMBER', 'BANK\_ACCOUNT\_NUM', 'UPI\_VPA', 'VEHICLE\_PLATE')
- `normalized_value_hash` (VARCHAR, Required)
- `value_policy` (VARCHAR)

##### relationships (Authoritative Associations)

- `relationship_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `source_entity_uuid` (FK to `entities.entity_id`, Required)
- `target_entity_uuid` (FK to `entities.entity_id`, Required)
- `type` (VARCHAR, Required, e.g., 'CONTACTED', 'OWNS', 'TRANSFERRED\_TO')
- `status` (VARCHAR, Required, e.g., 'OBSERVED', 'CORROBORATED', 'CONFIRMED', 'REJECTED')
- `created_at` (TIMESTAMP, Default: NOW())

##### relationship\_evidence (Provenance Chain)

- `evidence_id` (PK, UUID-v4, Required)
- `relationship_id` (FK to `relationships.relationship_id`, Required)
- `source_ref` (VARCHAR, Required)
- `support_type` (VARCHAR, Required, e.g., 'FIR\_PARAGRAPH', 'CDR\_ROW')

##### events (Temporal Log)

- `event_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `event_type` (VARCHAR, Required)
- `timestamp` (TIMESTAMP, Required)
- `entity_refs` (JSONB)
- `source` (VARCHAR)

##### communications (CDR Rows)

- `communication_id` (PK, UUID-v4, Required)
- `caller_ref` (FK to `entities.entity_id`, Required)
- `receiver_ref` (FK to `entities.entity_id`, Required)
- `duration` (INTEGER)
- `timestamps` (TIMESTAMP, Required)
- `channel` (VARCHAR, Required, e.g., 'SMS', 'CALL', 'WHATSAPP')

##### transactions (Financial Transactions)

- `transaction_id` (PK, UUID-v4, Required)
- `sender_ref` (FK to `entities.entity_id`, Required)
- `receiver_ref` (FK to `entities.entity_id`, Required)
- `amount` (NUMERIC/DECIMAL, Required) - *Invariant:* Absolute decimals only; binary float types are forbidden.
- `currency` (VARCHAR, Required)
- `channel` (VARCHAR, Required)
- `time` (TIMESTAMP, Required)

##### locations (Coordinates Data)

- `location_id` (PK, UUID-v4, Required)
- `normalized_label` (VARCHAR, Required)
- `geography` (VARCHAR)
- `lat_lon_policy` (VARCHAR)

##### vehicles (Transport Objects)

- `vehicle_id` (PK, UUID-v4, Required)
- `masked_plate` (VARCHAR, Required)
- `type` (VARCHAR)
- `source_refs` (JSONB)

##### organizations (Corporate Records)

- `organization_id` (PK, UUID-v4, Required)
- `name` (VARCHAR, Required)
- `registry_type` (VARCHAR)
- `identifiers` (JSONB)

##### phones (Sim Card Records)

- `phone_id` (PK, UUID-v4, Required)
- `normalized_number` (VARCHAR, Required)
- `active_status` (VARCHAR, Required)

##### accounts (Payment Profiles)

- `account_id` (PK, UUID-v4, Required)
- `masked_identifier` (VARCHAR, Required)
- `bank_type` (VARCHAR)
- `provider` (VARCHAR)

##### investigation\_notes (Investigator Workspace)

- `note_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `author_uuid` (FK to `users.user_id`, Required)
- `notes_text` (TEXT, Required)
- `entity_refs` (JSONB)

##### model\_runs (Execution Logs)

- `run_id` (PK, UUID-v4, Required)
- `model_name` (VARCHAR, Required)
- `version` (VARCHAR, Required)
- `task_type` (VARCHAR, Required, e.g., 'SNA\_CALCULATION', 'GAT\_LINK\_PREDICTION')
- `input_snapshot_checksum` (VARCHAR, Required)
- `status` (VARCHAR, Required)
- `created_at` (TIMESTAMP, Default: NOW())

##### predictions (AI Output Projection)

- `prediction_id` (PK, UUID-v4, Required)
- `run_id` (FK to `model_runs.run_id`, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `source_ref` (FK to `entities.entity_id`, Required)
- `target_ref` (FK to `entities.entity_id`, Required)
- `score` (DOUBLE PRECISION, Required)
- `calibration` (VARCHAR, Required)

##### risk\_scores (Priorities Output)

- `score_id` (PK, UUID-v4, Required)
- `target_entity_uuid` (FK to `entities.entity_id`, Required)
- `run_id` (FK to `model_runs.run_id`, Required)
- `score_type` (VARCHAR, Required)
- `value` (DOUBLE PRECISION, Required)
- `features_summary` (JSONB)

##### graph\_snapshots (Graph Sync Ledger)

- `snapshot_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `source_migration_version` (VARCHAR, Required)
- `checksum` (VARCHAR, Required)
- `created_at` (TIMESTAMP, Default: NOW())

##### audit\_logs (Operations Ledger)

- `audit_id` (PK, UUID-v4, Required)
- `actor_uuid` (FK to `users.user_id`, Required)
- `action_code` (VARCHAR, Required)
- `case_id` (FK to `cases.case_id`) - *Note:* Nullable only for cross-case actions.
- `target_item` (VARCHAR)
- `timestamp` (TIMESTAMP, Default: NOW(), Required)
- `outcome` (VARCHAR, Required)

##### alerts (Pattern Alerter)

- `alert_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `alert_type` (VARCHAR, Required)
- `severity` (VARCHAR, Required)
- `rule_id` (VARCHAR, Required)
- `contributing_entities` (JSONB, Required)
- `status` (VARCHAR, Required, e.g., 'NEW', 'REVIEWED')

##### saved\_queries (Search Templates)

- `query_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `user_uuid` (FK to `users.user_id`, Required)
- `filters_json` (JSONB, Required)

##### search\_history (Telemetry)

- `search_id` (PK, UUID-v4, Required)
- `user_uuid` (FK to `users.user_id`, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `query_metadata` (JSONB, Required)
- `timestamp` (TIMESTAMP, Default: NOW())

##### exports (Report Index)

- `export_id` (PK, UUID-v4, Required)
- `case_id` (FK to `cases.case_id`, Required)
- `user_uuid` (FK to `users.user_id`, Required)
- `artifact_ref` (VARCHAR, Required)
- `version_hash` (VARCHAR, Required)
- `created_at` (TIMESTAMP, Default: NOW())

#### 2.2 Security, Integrity & Mutability Rules

- **Case Tenant Integrity:** Every lookup on any case asset must explicitly include an query filter checking `case_id` membership against the requester's authorized `case_members` map.
- **Immutable Historical Sources:** Raw source tables (`documents`, `document_versions`, `document_chunks`, `events`, `communications`, `transactions`) are strictly append-only. They must never be edited, deleted, or mutated.
- **Traceable Deletions:** Node deletion or entity merge actions are soft deletes. They archive relationships or canonical mappings in the relational tables and update Neo4j projections accordingly, leaving the source records intact.
- **Audit Trail Retention:** The `audit_logs` table is strictly append-only. Modification operations on this table are blocked at the database execution level.

---
