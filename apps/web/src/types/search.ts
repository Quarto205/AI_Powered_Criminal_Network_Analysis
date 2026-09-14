/**
 * SIH26189 — Search Domain Contracts
 * Source: docs/contracts/04_API_SPEC.md (Section 4.2), 08_UI_DATA_CONTRACT.md
 * 
 * Invariants:
 * 1. Reuses canonical ApiResponse envelope from types/shell.ts.
 * 2. Reuses canonical EntityType from types/graph.ts.
 * 3. Primary identifiers are valid UUID-v4 format.
 * 4. Masked identifiers are always presented in results (no raw PII / secret numbers).
 * 5. Authorization boundary is backend-driven; stealth empty responses preserve isolation.
 */

import { ApiResponse, UUID } from './shell';
import { EntityType } from './graph';

/**
 * Authorized case summary search result (Section 11)
 */
export interface CaseSearchResult {
  case_id: UUID;
  case_code: string;
  title: string;
  jurisdiction: string;
}

/**
 * Resolved entity search result with masked identifier (Section 12)
 */
export interface EntitySearchResult {
  entity_id: UUID;
  case_id: UUID;
  case_code?: string;
  entity_type: EntityType;
  canonical_name: string;
  masked_identifier: string;
  status: string;
  alias_count?: number;
}

/**
 * Global search result payload containing authorized cases and entities (Section 13)
 */
export interface GlobalSearchPayload {
  cases: CaseSearchResult[];
  entities: EntitySearchResult[];
}

/**
 * GET /api/v1/cases/{case_id}/entities response envelope
 */
export type CaseEntitiesApiResponse = ApiResponse<EntitySearchResult[]>;

/**
 * GET /api/v1/search response envelope
 */
export type GlobalSearchApiResponse = ApiResponse<GlobalSearchPayload>;
