/**
 * SIH26189 — Shell TypeScript Contracts
 * Source: docs/contracts/01_SHARED_TYPES.md, 04_API_SPEC.md, 07_AUTH_SECURITY.md, 08_UI_DATA_CONTRACT.md
 * 
 * Strict type definitions for AppShell and CaseShell framework.
 * Freeze interfaces, not internal implementations.
 */

import { UUID, SystemMasterState as CanonicalMasterState, APIErrorDetails } from './contracts';

export type { UUID, APIErrorDetails };

// Re-export canonical master state and provide MasterSystemState alias
export type MasterSystemState = CanonicalMasterState;

/**
 * 7.1 Canonical RBAC Roles (07_AUTH_SECURITY.md)
 */
export type SystemRole =
  | 'INVESTIGATOR'
  | 'ANALYST'
  | 'SUPERVISOR';

/**
 * 6.3 Recovery and Degraded Operations Workflow (06_WORKFLOWS.md)
 */
export type SystemHealthStatus =
  | 'NORMAL'
  | 'DEGRADED — Provider Offline'
  | 'GRAPH UNAVAILABLE';

/**
 * 8.1 Case-Centric UI Tabs (08_UI_DATA_CONTRACT.md)
 */
export type CaseShellTabId =
  | 'overview'
  | 'graph'
  | 'timeline'
  | 'entities'
  | 'evidence'
  | 'alerts'
  | 'audit';

/**
 * Global App Navigation Domains (08_UI_DATA_CONTRACT.md Section 8.1)
 */
export type AppDomain =
  | 'cases'
  | 'search'
  | 'jobs'
  | 'settings';

/**
 * 4.1 Invariant API Response Envelope (04_API_SPEC.md)
 * Strict discriminated union modeling success vs error without unsafe casts
 */
export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  error?: null;
  request_id: string;
}

export interface ApiErrorResponse {
  success: false;
  data?: null;
  error: APIErrorDetails;
  request_id: string;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

/**
 * 4.2 Case Details Contract (GET /api/v1/cases/{case_id} & 02_DATABASE_SCHEMA.md)
 * Canonical fields strictly preserved
 */
export interface CaseDetails {
  case_id: UUID;
  case_code: string;
  title: string;
  description?: string;
  status: MasterSystemState;
  jurisdiction: string;
  created_by: UUID;
  created_at: string;
  member_role: SystemRole;
  document_count: number;
  entity_count: number;
}

/**
 * Tab configuration definition
 */
export interface TabDefinition {
  id: CaseShellTabId;
  label: string;
  requiredRole?: SystemRole;
  description: string;
}
