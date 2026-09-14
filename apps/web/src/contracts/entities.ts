/**
 * Canonical Entity Schemas for SIH26189.
 * Strictly adheres to 02_DATABASE_SCHEMA.md, 04_API_SPEC.md,
 * and main/backend/schemas/evidence_analysis.py.
 */

import { UUID, EntityType } from './common';
import { ProvenanceSpan } from './evidence';

export interface EntityAliasInfo {
  alias_id: UUID;
  alias_text: string;
  source_ref?: string | null;
}

export interface EntityIdentifierInfo {
  identifier_id: UUID;
  type: string;
  masked_value: string;
  value_policy?: string | null;
}

export interface RiskScoreInfo {
  score_id: UUID;
  score_type: string;
  value: number;
  features_summary?: Record<string, unknown> | null;
}

export interface EntityDetailResponse {
  entity_id: UUID;
  case_id: UUID;
  canonical_name: string;
  entity_type: EntityType | string;
  status: string;
  aliases: EntityAliasInfo[];
  identifiers: EntityIdentifierInfo[];
  risk_score?: RiskScoreInfo | null;
  provenance_spans: ProvenanceSpan[];
  created_at: string;
}

export interface EntityListQueryParams {
  type?: string;
  normalized_name?: string;
  limit?: number;
}
