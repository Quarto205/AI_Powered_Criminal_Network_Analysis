# Project History and Structure

## 1. Creation History Till Now

This project, **SIH26189 — AI-Powered Criminal Network Analysis System**, is an AI-powered criminal network analysis system designed for investigation support.

### Completed Work

- **DONE-001**: Recovered project architecture and 3-agent concept from the initial project history.
- **DONE-002**: Confirmed the Neo4j + FastAPI + Cytoscape prototype path.
- **DONE-003**: Identified GATv2 as a link-prediction component (not a kingpin detector) and recorded this architecture correction.
- **DONE-004**: Established an Indian-first dataset strategy, incorporating public, synthetic, and international benchmark tiers.
- **DONE-005**: Identified overengineering risks, successfully deferring Kafka, microservices, and complex enterprise security stacks in favor of a modular monolith.

### System Verification History

Phase 1 Functional UI & Backend Baseline is currently complete. Core pipelines have been built and tested successfully:

- **DB-001**: PostgreSQL relational schema & migrations (22 unit tests passing).
- **AUTH-001**: Authentication, RBAC & Server-Side Case Isolation (30 tests passing).
- **API-001**: Core API Shell & Case Management (23 tests passing).
- **ING-001**: Document Ingestion API & Worker Task Bridge (19 tests passing).
- **OCR-001** & **NLP-001**: OCR preprocessor and Agent 1 structured extraction workflows (56 unit tests passing).
- **DOC-PIPELINE-001**: Document Task Pipeline & E2E Integration.
- **GRAPH-001**: Neo4j projections rebuilt safely with parameterized Cypher and idempotent MERGEs.
- **UI-001**: Phase 1 Functional UI Integration completely verified (199/199 frontend tests passing).
- **INT-001**: Testing Branch Full Integration verified (225 backend tests + 199 frontend tests passing).

The project is currently proceeding into **Phase 2 Visual Styling** and finalizing the predictive ranking functionalities (**Agent 3**).

---

## 2. Folder and File Structure

Below is the complete current architecture layout of the project, including backend, frontend (apps/web), machine learning components, schemas, and configurations:

```text
AI-criminal-Network
|-- .agents
|   |-- mcp_config.json
|   |-- rules
|   |   `-- core-project-rules.md
|   `-- skills
|       `-- project-memory
|           `-- SKILL.md
|-- .dockerignore
|-- .env.example
|-- .gitignore
|-- AGENTS.md
|-- Dockerfile
|-- Json
|-- README.md
|-- Useful
|   |-- 01_SHARED_TYPES.md
|   |-- 02_DATABASE_SCHEMA.md
|   |-- 03_GRAPH_SCHEMA.md
|   |-- 04_API_SPEC.md
|   |-- 05_AI_CONTRACTS.md
|   |-- 06_WORKFLOWS.md
|   |-- 07_AUTH_SECURITY.md
|   |-- 08_UI_DATA_CONTRACT.md
|   |-- 09_NAMING_CONVENTIONS.md
|   |-- 10_CROSS_TEAM_DEPENDENCIES.md
|   |-- DOCUMENT_CONSISTENCY_REPORT.md
|   |-- README-10files.md
|   |-- README.md
|   |-- appflow.md
|   |-- backend-schema.md
|   |-- design.md
|   |-- implementation-plan.md
|   |-- prd.md
|   |-- rules.md
|   |-- security.md
|   |-- system-architecture.md
|   |-- tracker.md
|   |-- trd.md
|   `-- word_counts.json
|-- agents
|   |-- __init__.py
|   |-- evidence
|   |   `-- .gitkeep
|   |-- extraction
|   |   |-- .gitkeep
|   |   |-- __init__.py
|   |   |-- exceptions.py
|   |   |-- fallback.py
|   |   |-- ocr
|   |   |   |-- __init__.py
|   |   |   |-- exceptions.py
|   |   |   |-- preprocessor.py
|   |   |   |-- providers.py
|   |   |   |-- schemas.py
|   |   |   `-- security.py
|   |   |-- parser.py
|   |   |-- providers.py
|   |   `-- schemas.py
|   `-- intelligence
|       |-- .gitkeep
|       `-- dataset_adapter.py
|-- alembic
|   |-- env.py
|   |-- script.py.mako
|   `-- versions
|       |-- 0001_initial_schema.py
|       `-- 0002_add_agent3_datasets.py
|-- alembic.ini
|-- apps
|   |-- __init__.py
|   |-- api
|   |   |-- .gitkeep
|   |   |-- __init__.py
|   |   |-- deps.py
|   |   |-- errors.py
|   |   |-- main.py
|   |   |-- routers
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- cases.py
|   |   |   |-- documents.py
|   |   |   |-- evidence_analysis.py
|   |   |   |-- graph.py
|   |   |   `-- v1.py
|   |   |-- routes
|   |   |   `-- health.py
|   |   `-- tracking.py
|   `-- web
|       |-- .gitkeep
|       |-- index.html
|       |-- package-lock.json
|       |-- package.json
|       |-- src
|       |   |-- App.tsx
|       |   |-- api
|       |   |   |-- clientInterface.ts
|       |   |   |-- index.ts
|       |   |   |-- mockApiClient.ts
|       |   |   `-- realApiClient.ts
|       |   |-- components
|       |   |   |-- common
|       |   |   |   |-- Badge.tsx
|       |   |   |   |-- Button.tsx
|       |   |   |   |-- PermissionGate.tsx
|       |   |   |   `-- States.tsx
|       |   |   |-- drawers
|       |   |   |   |-- EntityDrawer.tsx
|       |   |   |   `-- EvidencePanel.tsx
|       |   |   |-- graph
|       |   |   |   |-- GraphCanvas.test.tsx
|       |   |   |   |-- GraphCanvas.tsx
|       |   |   |   |-- GraphToolbar.test.tsx
|       |   |   |   |-- GraphToolbar.tsx
|       |   |   |   `-- graphFilter.ts
|       |   |   |-- panels
|       |   |   |   |-- AIExplanationPanel.tsx
|       |   |   |   |-- AlertsPanel.tsx
|       |   |   |   `-- AuditPanel.tsx
|       |   |   |-- search
|       |   |   |   |-- CaseSearchInput.test.tsx
|       |   |   |   |-- CaseSearchInput.tsx
|       |   |   |   |-- GlobalSearchModal.test.tsx
|       |   |   |   `-- GlobalSearchModal.tsx
|       |   |   |-- shell
|       |   |   |   |-- AppShell.tsx
|       |   |   |   |-- AppShellHeader.tsx
|       |   |   |   |-- AppShellSidebar.tsx
|       |   |   |   |-- CaseNotFound.tsx
|       |   |   |   |-- CaseShell.tsx
|       |   |   |   |-- CaseShellTabs.tsx
|       |   |   |   |-- PermissionGate.tsx
|       |   |   |   `-- shell.test.tsx
|       |   |   |-- tabs
|       |   |   |   |-- AlertsTab.tsx
|       |   |   |   |-- AuditTab.tsx
|       |   |   |   |-- GraphCanvas.tsx
|       |   |   |   |-- GraphToolbar.tsx
|       |   |   |   |-- OverviewTab.tsx
|       |   |   |   `-- TimelineTab.tsx
|       |   |   |-- timeline
|       |   |   |   |-- Timeline.test.tsx
|       |   |   |   |-- TimelineScrubber.tsx
|       |   |   |   |-- TimelineView.tsx
|       |   |   |   `-- timelineUtils.ts
|       |   |   `-- triage
|       |   |       `-- EntityReviewQueue.tsx
|       |   |-- context
|       |   |   |-- CaseContext.tsx
|       |   |   `-- SelectionContext.tsx
|       |   |-- contracts
|       |   |   |-- analysis.ts
|       |   |   |-- api.ts
|       |   |   |-- audit.ts
|       |   |   |-- cases.ts
|       |   |   |-- common.ts
|       |   |   |-- entities.ts
|       |   |   |-- evidence.ts
|       |   |   |-- graph.ts
|       |   |   `-- index.ts
|       |   |-- fixtures
|       |   |   |-- demoAlerts.ts
|       |   |   |-- demoAudit.ts
|       |   |   |-- demoCase.ts
|       |   |   |-- demoEvidence.ts
|       |   |   |-- demoGraph.ts
|       |   |   |-- demoTimeline.ts
|       |   |   |-- graphFixture.ts
|       |   |   `-- index.ts
|       |   |-- index.css
|       |   |-- main.tsx
|       |   |-- mocks
|       |   |   |-- caseMock.ts
|       |   |   |-- evidenceMock.ts
|       |   |   |-- graphMock.ts
|       |   |   |-- index.ts
|       |   |   |-- mockEnvelope.ts
|       |   |   |-- searchMock.ts
|       |   |   `-- timelineMock.ts
|       |   |-- styles
|       |   |   `-- graphStyles.ts
|       |   |-- test
|       |   |   `-- setup.ts
|       |   |-- tests
|       |   |   |-- AIExplanationPanel.test.tsx
|       |   |   |-- AlertsPanel.test.tsx
|       |   |   |-- AppShell.test.tsx
|       |   |   |-- AuditPanel.test.tsx
|       |   |   |-- Drawers.test.tsx
|       |   |   |-- EntityDrawer.test.tsx
|       |   |   |-- EntityReviewQueue.test.tsx
|       |   |   |-- EvidencePanel.test.tsx
|       |   |   |-- GraphCanvas.test.tsx
|       |   |   |-- contracts.test.ts
|       |   |   |-- mockApi.test.ts
|       |   |   |-- mocksAndContracts.test.ts
|       |   |   `-- setup.ts
|       |   |-- types
|       |   |   |-- contracts.ts
|       |   |   |-- graph.ts
|       |   |   |-- search.ts
|       |   |   |-- shell.ts
|       |   |   `-- timeline.ts
|       |   `-- vite-env.d.ts
|       |-- tsconfig.json
|       |-- vercel.json
|       |-- vite.config.ts
|       `-- vitest.config.ts
|-- backend
|   |-- __init__.py
|   |-- config
|   |   |-- .gitkeep
|   |   |-- __init__.py
|   |   |-- database.py
|   |   |-- neo4j.py
|   |   |-- security.py
|   |   `-- settings.py
|   |-- db
|   |   |-- __init__.py
|   |   |-- base.py
|   |   |-- models
|   |   |   |-- __init__.py
|   |   |   |-- analytics.py
|   |   |   |-- entities.py
|   |   |   |-- identity.py
|   |   |   `-- ingestion.py
|   |   |-- session.py
|   |   |-- triggers.py
|   |   `-- types.py
|   |-- domain
|   |   |-- .gitkeep
|   |   |-- __init__.py
|   |   |-- errors.py
|   |   `-- redaction.py
|   |-- graph
|   |   |-- connection.py
|   |   |-- cypher_builder.py
|   |   |-- mock_driver.py
|   |   `-- schema_init.py
|   |-- jobs
|   |   |-- .gitkeep
|   |   |-- __init__.py
|   |   |-- document_worker.py
|   |   `-- worker_bridge.py
|   |-- repositories
|   |   |-- .gitkeep
|   |   |-- __init__.py
|   |   |-- audit_repository.py
|   |   |-- document_repository.py
|   |   |-- evidence_repository.py
|   |   |-- export_repository.py
|   |   |-- neo4j_driver.py
|   |   |-- postgres_session.py
|   |   |-- review_repository.py
|   |   `-- storage.py
|   |-- schemas
|   |   |-- .gitkeep
|   |   |-- __init__.py
|   |   |-- audit.py
|   |   |-- cases.py
|   |   |-- document_jobs.py
|   |   |-- documents.py
|   |   |-- envelope.py
|   |   |-- evidence_analysis.py
|   |   |-- export.py
|   |   `-- graph.py
|   |-- security
|   |   |-- __init__.py
|   |   |-- audit.py
|   |   |-- password.py
|   |   |-- rbac.py
|   |   `-- tokens.py
|   `-- services
|       |-- .gitkeep
|       |-- __init__.py
|       |-- analysis_service.py
|       |-- case_service.py
|       |-- document_pipeline.py
|       |-- document_service.py
|       |-- evidence_review.py
|       |-- graph_projection.py
|       `-- graph_query.py
|-- data
|   |-- agent3
|   |   `-- raw
|   |       |-- israel_lea_inp_burglary_offender_id_network.json
|   |       `-- israel_lea_inp_burglary_v2_crime_id_network.json
|   |-- demo
|   |   `-- .gitkeep
|   `-- schemas
|       `-- .gitkeep
|-- docker-compose.yml
|-- docs
|   |-- DOCUMENT_CONSISTENCY_REPORT.md
|   |-- agent3
|   |   `-- README.md
|   |-- appflow.md
|   |-- backend-schema.md
|   |-- contracts
|   |   |-- 01_SHARED_TYPES.md
|   |   |-- 02_DATABASE_SCHEMA.md
|   |   |-- 03_GRAPH_SCHEMA.md
|   |   |-- 04_API_SPEC.md
|   |   |-- 05_AI_CONTRACTS.md
|   |   |-- 06_WORKFLOWS.md
|   |   |-- 07_AUTH_SECURITY.md
|   |   |-- 08_UI_DATA_CONTRACT.md
|   |   |-- 09_NAMING_CONVENTIONS.md
|   |   `-- 10_CROSS_TEAM_DEPENDENCIES.md
|   |-- design.md
|   |-- implementation-plan.md
|   |-- prd.md
|   |-- project-knowledge
|   |   |-- MEMORY_INDEX.md
|   |   |-- PROJECT_MEMORY_README.md
|   |   `-- RESEARCH_KNOWLEDGE_BASE.md
|   |-- rules.md
|   |-- security.md
|   |-- system-architecture.md
|   |-- tracker.md
|   `-- trd.md
|-- implementation_plan.md
|-- ml
|   |-- datasets
|   |   `-- .gitkeep
|   |-- evaluation
|   |   `-- .gitkeep
|   |-- models
|   |   `-- .gitkeep
|   |-- preprocessing
|   |   `-- .gitkeep
|   `-- training
|       `-- .gitkeep
|-- pytest.ini
|-- render.yaml
|-- requirements.txt
|-- scripts
|   |-- load_agent3_dataset.py
|   |-- rebuild_graph.py
|   |-- reset_demo.py
|   |-- run_evaluation.py
|   |-- seed_demo.py
|   |-- supermemory_server.py
|   `-- validate_agent3_analytics.py
`-- tests
    |-- conftest.py
    |-- e2e
    |   `-- .gitkeep
    |-- integration
    |   |-- .gitkeep
    |   |-- test_agent3_dataset.py
    |   |-- test_analysis_pipeline.py
    |   |-- test_case_isolation.py
    |   |-- test_case_management.py
    |   |-- test_doc_ingestion_pipeline.py
    |   |-- test_doc_pipeline.py
    |   `-- test_graph_api.py
    |-- security
    |   `-- .gitkeep
    |-- test_agent3_env.py
    |-- test_contracts.py
    `-- unit
        |-- .gitkeep
        |-- test_agent1_extraction.py
        |-- test_api_shell.py
        |-- test_auth_rbac.py
        |-- test_db_schema.py
        |-- test_domain_repositories.py
        |-- test_evidence_review_api.py
        |-- test_graph_sync.py
        |-- test_ingestion_api.py
        `-- test_ocr_preprocessor.py
```
