# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

#### 1.1 Identifiers & Formats [CURRENT/FINAL]
- **External Raw Identifiers:** Human-readable values (such as FIR Numbers, Bank Account Numbers, UPI VPAs, Vehicle License Plates, and Mobile Phone IMSIs/MSISDNs) must never serve as primary keys. They are treated as sensitive data and are stored as typed fields within an auxiliary schema table, with values normalized and masked or hashed.

## Repository/dependency naming and boundaries

### SECTION 9: REPOSITORY SPECIFICATIONS & DEV DIRECTION

#### 9.1 Repository Layout [CURRENT/FINAL]

```
project-root/
├── apps/
│   ├── web/                 # Frontend presentation (React/TS + Cytoscape.js)
│   └── api/                 # FastAPI routes and payload schema adapters
├── backend/
│   ├── domain/              # Case models, entity schemas, logic
│   ├── repositories/        # SQL parameters & Neo4j query parameters
│   ├── services/            # Ingestion, validation, overrides, and permission controls
│   ├── jobs/                # Asynchronous task pipelines
│   └── config/              # Runtime environment variables (no raw secrets)
├── agents/
│   ├── extraction/          # Agent 1 NLP pipelines & OCR abstractions
│   ├── evidence/            # Agent 2 entity resolution & validation utilities
│   └── intelligence/        # Agent 3 SNA calculations & pattern checking
├── ml/
│   └── models/              # GATv2 PyG architecture configurations
├── data/
│   └── demo/                # Seed files containing deterministic mock CDR graphs

```

#### 9.2 Technical Constraints & Boundaries [CURRENT/FINAL]

- **Local-First Design:** The application must run locally using Docker Compose, containing standard PostgreSQL, Neo4j, and Python workers.
- **Clean Dependency Boundaries:** Frontend modules cannot import database drivers. Model-provider SDKs must be isolated behind domain provider interfaces to prevent vendor lock-in.
- **No Dual-Phase Commits:** Database transactions are strictly isolated. Neo4j graph projections must run asynchronously via background jobs, rather than attempting distributed SQL-to-NoSQL transactions.

---
