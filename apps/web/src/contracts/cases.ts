/**
 * Canonical Case Management Schemas for SIH26189.
 * Strictly adheres to 04_API_SPEC.md (Section 4.2) and main/backend/schemas/cases.py.
 */

import { UUID, UserRole } from './common';

export interface CaseCreateRequest {
  case_code: string;
  title: string;
  description?: string;
  jurisdiction: string;
}

export interface CaseCreateResponse {
  case_id: UUID;
  case_code: string;
  title: string;
  status: string;
  jurisdiction: string;
  created_at: string;
  created_by: UUID;
}

export interface CaseUpdateRequest {
  title?: string;
  description?: string;
  jurisdiction?: string;
  status?: 'ACTIVE' | 'ARCHIVED' | 'CLOSED' | 'PENDING_REVIEW';
}

export interface CaseDetailResponse {
  case_id: UUID;
  case_code: string;
  title: string;
  description?: string | null;
  status: string;
  jurisdiction: string;
  created_by: UUID;
  created_at: string;
  document_count: number;
  entity_count: number;
}

export interface CaseListItem {
  case_id: UUID;
  case_code: string;
  title: string;
  status: string;
  jurisdiction: string;
  member_role: UserRole | string;
  created_at: string;
}

export interface CaseListResponse {
  cases: CaseListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CaseMemberItem {
  user_id: UUID;
  username: string;
  email: string;
  role_in_case: UserRole | string;
}

export interface CaseMemberAddRequest {
  user_id: UUID;
  role_in_case: UserRole;
}
