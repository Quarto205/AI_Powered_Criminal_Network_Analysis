/**
 * Canonical Evidence & Provenance Schemas for SIH26189.
 * Strictly adheres to 01_SHARED_TYPES.md, 04_API_SPEC.md,
 * and main/backend/schemas/evidence_analysis.py.
 */

import { UUID } from './common';

export interface ProvenanceSpan {
  chunk_id?: UUID | null;
  document_id?: UUID | null;
  file_name?: string | null;
  version_hash?: string | null;
  page_number?: number | null;
  character_start?: number | null;
  character_end?: number | null;
  source_ref: string;
  support_type: string;
  snippet?: string | null;
}

export interface EvidenceCitation {
  evidence_id: UUID;
  source_ref: string;
  support_type: string;
}

export interface RelationshipEndpointSummary {
  entity_id: UUID;
  canonical_name: string;
  entity_type: string;
}

export interface RelationshipDetailResponse {
  relationship_id: UUID;
  case_id: UUID;
  source_entity: RelationshipEndpointSummary;
  target_entity: RelationshipEndpointSummary;
  type: string;
  status: string;
  confidence_score: number;
  is_predicted: boolean;
  evidence_citations: EvidenceCitation[];
  created_at: string;
}

export interface DocumentUploadResponse {
  document_id: UUID;
  job_id: UUID;
  status: string;
}

export interface DocumentListItem {
  document_id: UUID;
  case_id: UUID;
  file_type: string;
  file_hash: string;
  status: string;
  created_at: string;
}
