/**
 * Canonical Audit & Review Schemas for SIH26189.
 * Strictly adheres to 02_DATABASE_SCHEMA.md, 04_API_SPEC.md, 07_AUTH_SECURITY.md,
 * and main/backend/schemas/evidence_analysis.py.
 */

import { UUID } from './common';

export const ReviewTargetTypes = {
  ENTITY: 'ENTITY',
  RELATIONSHIP: 'RELATIONSHIP',
} as const;

export type ReviewTargetType = (typeof ReviewTargetTypes)[keyof typeof ReviewTargetTypes];

export const ReviewActions = {
  CONFIRM: 'CONFIRM',
  REJECT: 'REJECT',
  MERGE: 'MERGE',
} as const;

export type ReviewAction = (typeof ReviewActions)[keyof typeof ReviewActions];

export interface ReviewRequest {
  target_type: ReviewTargetType | string;
  target_id: UUID;
  action: ReviewAction | string;
  secondary_target_id?: UUID | null;
  reason: string;
}

export interface ReviewResponse {
  review_id: UUID;
  target_type: string;
  target_id: UUID;
  action: string;
  resulting_status: string;
  secondary_target_id?: UUID | null;
  applied_at: string;
  reason: string;
}

export interface AuditLogItem {
  audit_id: UUID;
  actor: string;
  action: string;
  target_item?: string | null;
  timestamp: string;
  outcome: string;
}

export interface CaseAuditResponse {
  audit_logs: AuditLogItem[];
  total: number;
}

export interface ExportRequest {
  export_format: 'PDF' | 'CSV';
  include_audit_trail: boolean;
}

export interface ExportResponse {
  export_id: UUID;
  download_url: string;
  hash: string;
}

export interface TimelineEventItem {
  event_id: UUID;
  case_id: UUID;
  event_type: 'COMMUNICATION' | 'TRANSACTION' | 'MOVEMENT' | 'DOCUMENT_OBSERVATION';
  timestamp: string;
  description: string;
  entities_involved: Array<{
    entity_id: UUID;
    canonical_name: string;
    role: string;
  }>;
  source_ref?: string;
  details?: Record<string, unknown>;
}
