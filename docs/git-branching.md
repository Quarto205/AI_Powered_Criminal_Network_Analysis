# SIH26189 Git Branching Strategy and Repository State

## 1. Branching Strategy

The repository follows a streamlined environment-based branching strategy:

- **`main`**: The pristine base repository. Main remains untouched by daily feature development. All code reaching main must be thoroughly vetted.
- **`testing`**: The canonical integration branch. All feature branches, including full agent milestones, integrate into `testing` to verify end-to-end compatibility before future deployments.
- **`feature/*`**: Short-lived, capability-based branches.

## 2. Agent 2 Finalization State

Agent 2 (Evidence & Graph Maintenance) was developed iteratively through Phases 1–7.
Because the intermediate phase states were not separated into individual historical commits at the time of development (all Agent 2 features were developed linearly on a single local state), the canonical and final verified state of Agent 2 has been preserved as a single integration branch.

- **Authoritative Branch**: `feature/integration-e2e` contains the complete, tested, and verified state for Agent 2 (Phases 1-7).
- **Tag**: `agent2-v1.0-final` points to the exact commit representing the completed Agent 2 milestone.
- **Integration**: `feature/integration-e2e` has been successfully merged into `testing`.

### Agent 2 Feature Branches

The following branches act as pointers to the `feature/integration-e2e` final state for organizational reference, as true historical snapshots were unavailable:
- `feature/entity-resolution`
- `feature/provenance-engine`
- `feature/graph-projection`
- `feature/security-hardening`

Previously merged historical branches for the foundational work still exist:
- `feature/contracts`
- `feature/postgres`
- `feature/ingestion`

## 3. Future Work

When Agent 3 development begins, it MUST branch from `testing` or follow the established canonical branching rules, ensuring Agent 2's verified functionality is inherited appropriately without disturbing `main`.
