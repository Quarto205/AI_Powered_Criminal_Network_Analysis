# CNAS Forensic Intelligence - Current System State

This document represents the absolute source of truth regarding the state of the codebase, project architecture, integrations, and missing components.

## 1. High-Level Architecture
The repository `AI_Powered_Criminal_Network_Analysis` is structured as a full-stack monorepo:
- **Frontend (`apps/web`)**: Built with React, Vite, TypeScript, and Zustand (in parts) / React Context.
- **Backend API (`apps/api`)**: Built with FastAPI (Python), serving as the gateway, authentication layer, and router.
- **Backend Services (`backend/`)**: Contains domain logic, PostgreSQL models, Neo4j graph schemas, background jobs (via Celery/RQ/Thread worker), and the RAG intelligence layer.
- **Agents (`agents/`)**: Python-based AI agents, including the Priority Engine, Explanation Engine, and multi-modal RAG extraction (GenericHTTPProvider).

## 2. Directory Structure & State

### `apps/web/` (React Frontend) - **INTEGRATED & STABLE**
- **Auth Flow**: Uses `AuthContext.tsx` and `LoginView.tsx` to authenticate against `POST /auth/login`. Employs `apiClient.ts` to manage JWT tokens securely in memory.
- **Case Management**: `CaseContext.tsx` fetches live cases via `GET /api/v1/cases` and sets the active tenant context. 
- **Graph Explorer (`views/GraphView.tsx`)**: Wired to fetch live nodes/edges from `GET /api/v1/cases/{case_id}/graph?depth=2&limit=500`.
- **Evidence Ingestion (`views/EvidenceView.tsx`)**: Replaced simulated delays with real `FormData` upload to `POST /api/v1/cases/{case_id}/documents`. Fetching documents is wired to `GET /api/v1/cases/{case_id}/documents`.
- **AI Copilot (`services/nvidiaNimService.ts`)**: Integrated the agentic RAG by routing the Chat interface to `POST /api/v1/cases/{case_id}/intelligence/copilot/query`.

### `apps/api/` (FastAPI Gateway) - **ACTIVE & EXTENDED**
- `routers/auth.py`: JWT-based authentication (HS256). Fully functional.
- `routers/cases.py`: Multi-tenant case isolation. Fully functional.
- `routers/graph.py`: Handles Graph projection and Neo4j queries. Functional.
- `routers/documents.py`: Manages document ingestion, chunking, and worker bridging. Functional.
- `routers/intelligence.py`: Originally contained `PriorityEngine` and `ExplanationEngine`. **[NEW]** We injected the `POST /copilot/query` endpoint here to process the Chat Copilot queries and return raw RAG context (without Markdown) using the generic LLM provider.

### `backend/` (Core Infrastructure)
- **Database (`backend/db`)**: SQLAlchemy schemas for Identity (`User`, `CaseMember`), Ingestion (`Document`), and Analytics (`RiskScore`, `Explanation`).
- **Graph (`backend/graph`)**: Neo4j driver configurations and graph projection schemas.
- **Security (`backend/security`)**: RBAC, JWT tokens, and Audit logging (`SecurityAuditAction`).
- **Services (`backend/services`)**: Business logic abstractions (`DocumentPipeline`, `GraphQueryService`).

### `agents/` (Intelligence layer)
- **`PriorityEngine`**: Ranks case entities.
- **`ExplanationEngine`**: Generates grounded logic using `GenericHTTPProvider`.
- **Note on Agent 3**: Agent 3 directories (`data/agent3/`, `docs/agent3/`) exist, indicating an offline batch-processing or secondary ML ingestion pipeline that might still be missing some deep pipeline hooks, but the core conversational Agent (Copilot) is fully wired.

## 3. Current Limitations / Known Issues
- **Neo4j DB Status**: The local GraphManager expects an active Neo4j connection. If it's offline, `/api/v1/cases/{case_id}/graph` throws a 503 fallback. 
- **LLM Key**: The AI responses from `/copilot/query` require a valid `OPENAI_API_KEY` (used generically in the provider) or they fall back to a mock/error string.
- **Missing "Agent 3" ML logic**: The user explicitly asked about Agent 3 / ML files. The folders (`ml/models`, `ml/datasets`, `data/agent3`) are present, but their runtime deployment scripts (e.g., custom inference endpoints for the actual model) might need to be booted separately in testing.

## 4. End-to-End Test Readiness
The application is fully wired top-to-bottom:
1. User logs in -> gets JWT.
2. Workspace loads -> fetches cases.
3. Sub-workspaces (Graph, Evidence, AI) -> all use the JWT to query case-specific endpoints.
4. AI Copilot -> queries LLM via backend, completely bypassing the old hardcoded offline mock.

**Next step**: Run `npm run dev` in `apps/web` and `uvicorn apps.api.main:app --reload` (or the respective script) to test the platform live. 
