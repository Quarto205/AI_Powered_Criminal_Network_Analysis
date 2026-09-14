# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 4: API CATALOG [CURRENT/FINAL]

All API communication must flow through the designated, versioned paths. Unstructured custom database queries from the frontend are prohibited.

#### 4.1 Invariant API Response Conventions

All API endpoints must utilize the following structured JSON envelopes:

- **Success Response Structure:** 
  ```
  {
    "success": true,
    "data": { ... },
    "request_id": "UUID-v4-string"
  }

  ```
- **Error Response Structure:** 
  ```
  {
    "success": false,
    "error": {
      "code": "ERR_INVALID_PAYLOAD",
      "message": "Detailed developer-hardened reason string.",
      "details": {}
    },
    "request_id": "UUID-v4-string"
  }

  ```

#### 4.2 Endpoint Contract List

##### POST /api/v1/cases

- **Auth/Scope:** Authenticated + `CASE_CREATE` Permission
- **Request Schema:** `{ "title": "string", "jurisdiction": "string", "description": "string", "case_code": "string" }`
- **Response Schema:** `{ "case_id": "UUID", "case_code": "string", "created_at": "datetime" }`
- **Status Codes:** `201 Created` on success; `400 Bad Request` if `case_code` is duplicated.

##### GET /api/v1/cases

- **Auth/Scope:** Authenticated; returns only cases where user has membership.
- **Request Params:** `limit` (integer), `offset` (integer) [cursor pagination supported but not specified]
- **Response Schema:** `{ "cases": [ { "case_id": "UUID", "title": "string", "case_code": "string", "member_role": "string" } ] }`
- **Status Codes:** `200 OK`

##### GET /api/v1/cases/{case\_id}

- **Auth/Scope:** Case Member
- **Response Schema:** Case details, document counts, entity counts, status.
- **Status Codes:** `200 OK`; `404 Not Found` if unauthorized (to prevent case enumeration).

##### POST /api/v1/cases/{case\_id}/documents

- **Auth/Scope:** Case Member + `DOCUMENT_UPLOAD` Permission
- **Request:** Multipart form-data containing raw document stream.
- **Response Schema:** `{ "document_id": "UUID", "job_id": "UUID", "status": "RECEIVED" }`
- **Status Codes:** `202 Accepted` (triggers async ingestion worker job); `413 Payload Too Large` if exceeds size limits.

##### POST /api/v1/cases/{case\_id}/imports

- **Auth/Scope:** Case Member + `IMPORT_DATA` Permission
- **Request Schema:** `{ "format": "CSV/JSON", "import_mapping": {}, "payload": "string" }`
- **Response Schema:** `{ "job_id": "UUID", "status": "PROCESSING", "accepted_rows": 0, "rejected_rows": 0 }`
- **Status Codes:** `202 Accepted`

##### GET /api/v1/cases/{case\_id}/entities

- **Auth/Scope:** Case Member
- **Request Params:** `type` (string), `normalized_name` (string), `limit` (integer)
- **Response Schema:** List of entity objects with canonical attributes.
- **Status Codes:** `200 OK`

##### GET /api/v1/cases/{case\_id}/graph

- **Auth/Scope:** Case Member + `GRAPH_READ` Permission
- **Request Params:** `pivot_entity_id` (UUID), `hop_depth` (integer, max limit enforced), `filters` (JSON string)
- **Response Schema:** `{ "nodes": [ ... ], "edges": [ ... ] }` (Format compatible with Cytoscape.js)
- **Status Codes:** `200 OK`; `404 Not Found` if pivot node is outside of case boundary.

##### POST /api/v1/cases/{case\_id}/analysis

- **Auth/Scope:** Case Member + `ANALYSIS_TRIGGER` Permission
- **Request Schema:** `{ "run_type": "SNA" | "PATTERNS" | "GAT_INFERENCE", "parameters": {} }`
- **Response Schema:** `{ "run_id": "UUID", "status": "PENDING" }`
- **Status Codes:** `202 Accepted`

##### GET /api/v1/cases/{case\_id}/analysis/{run\_id}

- **Auth/Scope:** Case Member
- **Response Schema:** Returns run progress, output indices, metrics features, and calculation logs.
- **Status Codes:** `200 OK`

##### GET /api/v1/cases/{case\_id}/alerts

- **Auth/Scope:** Case Member
- **Request Params:** `severity` (string), `status` (string)
- **Response Schema:** `{ "alerts": [ { "alert_id": "UUID", "alert_type": "string", "severity": "string", "contributing_entities": [] } ] }`
- **Status Codes:** `200 OK`

##### GET /api/v1/cases/{case\_id}/evidence/{evidence\_id}

- **Auth/Scope:** Case Member
- **Response Schema:** Evidence source origin, characters offsets, timestamping, upload reference.
- **Status Codes:** `200 OK`

##### POST /api/v1/cases/{case\_id}/reviews

- **Auth/Scope:** Case Supervisor / Reviewer Roles
- **Request Schema:** `{ "target_id": "UUID", "target_type": "ENTITY_RESOLUTION" | "PREDICTION" | "EXTRACTION", "action": "CONFIRM" | "REJECT", "override_notes": "string" }`
- **Response Schema:** `{ "review_id": "UUID", "status": "REVIEWED", "applied_at": "TIMESTAMP" }`
- **Status Codes:** `200 OK`

##### GET /api/v1/cases/{case\_id}/audit

- **Auth/Scope:** Supervisor or Security Auditor Permissions
- **Request Params:** `user_id` (UUID), `timestamp_start` (TIMESTAMP), `timestamp_end` (TIMESTAMP)
- **Response Schema:** `{ "audit_logs": [ { "audit_id": "UUID", "actor": "string", "action": "string", "timestamp": "TIMESTAMP" } ] }`
- **Status Codes:** `200 OK`

##### POST /api/v1/cases/{case\_id}/exports

- **Auth/Scope:** Case Member + `EXPORT_REPORT` Permission
- **Request Schema:** `{ "export_format": "PDF" | "CSV", "include_audit_trail": boolean }`
- **Response Schema:** `{ "export_id": "UUID", "download_url": "string", "hash": "string" }`
- **Status Codes:** `202 Accepted`

##### GET /api/v1/search

- **Auth/Scope:** System Administrator Only (Cross-case lookup)
- **Request Params:** `query_string` (string)
- **Response Schema:** Case mapping and entity pointers matching credentials.
- **Status Codes:** `200 OK`; returns restricted array empty if standard user.

---
