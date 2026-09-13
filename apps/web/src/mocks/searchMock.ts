/**
 * SIH26189 — Deterministic Search Mock Fixtures & Search Engine
 * Source: docs/contracts/04_API_SPEC.md (Section 4.2), 08_UI_DATA_CONTRACT.md
 * 
 * Invariants:
 * 1. Deterministic synthetic data: no Math.random(), no Date.now().
 * 2. Valid UUID-v4 format for all IDs.
 * 3. Shared IDs with caseMock and graphMock for seamless in-case graph pivot.
 * 4. Masked identifiers strictly enforced (+91-XXXXX-5678, SBIN000XXXX4921).
 * 5. Scope discipline: CaseSearchInput only receives active case entities;
 *    GlobalSearchModal receives authorized cross-case entities and cases.
 */

import {
  CaseSearchResult,
  EntitySearchResult,
  GlobalSearchPayload,
  GlobalSearchApiResponse,
  CaseEntitiesApiResponse
} from '../types/search';
import { mockActiveCase, mockCasesList } from './caseMock';
import {
  PIVOT_NODE_ID,
  PHONE_NODE_ID,
  BANK_NODE_ID,
  PERSON_B_NODE_ID
} from './graphMock';

export const CASE_1_ID = mockActiveCase.case_id; // 'a8f3b2e1-4c5d-4f6a-9b8c-7d6e5f4a3b2c'
export const CASE_2_ID = mockCasesList[1].case_id; // 'b9e4c3d2-5a6b-4c7d-8e9f-0a1b2c3d4e5f'

/**
 * Authorized Cases Fixtures (Section 11, 17)
 */
export const mockAuthorizedCases: CaseSearchResult[] = [
  {
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    title: 'Syndicate Hawala & Mule Network Investigation',
    jurisdiction: 'Delhi NCR — Special Cell'
  },
  {
    case_id: CASE_2_ID,
    case_code: 'MH-2026-EC-0084',
    title: 'Offshore Remittance & Shell Logistics Inquiry',
    jurisdiction: 'Mumbai — Cyber & Economic Offenses'
  }
];

/**
 * Authorized Entities Fixtures (Section 12, 18)
 * Strictly synthetic, masked identifiers only.
 */
export const mockAuthorizedEntities: EntitySearchResult[] = [
  // --- Case 1 Entities (Matching graphMock.ts) ---
  {
    entity_id: PIVOT_NODE_ID,
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Person',
    canonical_name: 'Person A',
    masked_identifier: 'Person A (Primary Target)',
    status: 'VERIFIED',
    alias_count: 2
  },
  {
    entity_id: PHONE_NODE_ID,
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Phone',
    canonical_name: 'Phone ••••5678',
    masked_identifier: '+91-XXXXX-5678',
    status: 'ACTIVE'
  },
  {
    entity_id: BANK_NODE_ID,
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'BankAccount',
    canonical_name: 'Account ••••4921',
    masked_identifier: 'SBIN000XXXX4921',
    status: 'FLAGGED'
  },
  {
    entity_id: PERSON_B_NODE_ID,
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Person',
    canonical_name: 'Person B',
    masked_identifier: 'Person B (Associate)',
    status: 'UNDER_INQUIRY',
    alias_count: 0
  },
  {
    entity_id: 'c7d8e9f0-1a2b-3c4d-5e6f-7a8b9c0d1e2f',
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Vehicle',
    canonical_name: 'Vehicle ••••1042',
    masked_identifier: 'DL01****1042',
    status: 'OBSERVED'
  },
  {
    entity_id: 'd8e9f0a1-2b3c-4d5e-6f7a-8b9c0d1e2f3a',
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Location',
    canonical_name: 'Safehouse Location Sector 62',
    masked_identifier: 'Noida Sector **',
    status: 'SUSPECTED'
  },
  {
    entity_id: 'e9f0a1b2-3c4d-5e6f-7a8b-9c0d1e2f3a4b',
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Organization',
    canonical_name: 'Apex Logistics Front Co',
    masked_identifier: 'CIN: U63090DL****',
    status: 'FLAGGED'
  },
  {
    entity_id: 'f0a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c',
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Phone',
    canonical_name: 'Phone ••••9821',
    masked_identifier: '+91-XXXXX-9821',
    status: 'ACTIVE'
  },
  {
    entity_id: 'a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d',
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'BankAccount',
    canonical_name: 'Account ••••8810',
    masked_identifier: 'HDFC000XXXX8810',
    status: 'ACTIVE'
  },
  {
    entity_id: 'b2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e',
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Evidence',
    canonical_name: 'CDR Record Batch 04',
    masked_identifier: 'DOC-CDR-2026-****',
    status: 'CORROBORATED'
  },
  {
    entity_id: 'c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f',
    case_id: CASE_1_ID,
    case_code: 'DL-2026-CR-0192',
    entity_type: 'Offense',
    canonical_name: 'Hawala Transfer IPC 120B/420',
    masked_identifier: 'FIR-2026-****',
    status: 'CONFIRMED'
  },

  // --- Case 2 Entities (Cross-case testing for MH-2026-EC-0084) ---
  {
    entity_id: '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d',
    case_id: CASE_2_ID,
    case_code: 'MH-2026-EC-0084',
    entity_type: 'Person',
    canonical_name: 'Person C',
    masked_identifier: 'Person C (Director)',
    status: 'ACTIVE',
    alias_count: 1
  },
  {
    entity_id: '2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e',
    case_id: CASE_2_ID,
    case_code: 'MH-2026-EC-0084',
    entity_type: 'Vehicle',
    canonical_name: 'Vehicle ••••3910',
    masked_identifier: 'MH02****3910',
    status: 'CONFIRMED'
  },
  {
    entity_id: '3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f',
    case_id: CASE_2_ID,
    case_code: 'MH-2026-EC-0084',
    entity_type: 'BankAccount',
    canonical_name: 'Account ••••7722',
    masked_identifier: 'ICIC000XXXX7722',
    status: 'FLAGGED'
  },
  {
    entity_id: '4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a',
    case_id: CASE_2_ID,
    case_code: 'MH-2026-EC-0084',
    entity_type: 'Phone',
    canonical_name: 'Phone ••••4433',
    masked_identifier: '+91-XXXXX-4433',
    status: 'ACTIVE'
  }
];

/**
 * Pure deterministic mock search engine for GlobalSearchModal (Section 27)
 */
export function searchAuthorizedRecords(query: string): GlobalSearchPayload {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return { cases: [], entities: [] };
  }

  const matchingCases = mockAuthorizedCases.filter((c) => {
    return (
      c.case_code.toLowerCase().includes(normalized) ||
      c.title.toLowerCase().includes(normalized) ||
      c.jurisdiction.toLowerCase().includes(normalized)
    );
  });

  const matchingEntities = mockAuthorizedEntities.filter((e) => {
    return (
      e.canonical_name.toLowerCase().includes(normalized) ||
      e.masked_identifier.toLowerCase().includes(normalized) ||
      e.entity_type.toLowerCase().includes(normalized) ||
      (e.case_code && e.case_code.toLowerCase().includes(normalized))
    );
  });

  return {
    cases: matchingCases,
    entities: matchingEntities
  };
}

/**
 * Pure deterministic case-scoped entity search for CaseSearchInput (Section 43, 44, 45)
 * Contract: Only returns entities belonging to activeCaseId, limited to 10.
 */
export function searchCaseEntities(
  caseId: string,
  query: string,
  limit: number = 10
): EntitySearchResult[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return [];
  }

  const caseScopedEntities = mockAuthorizedEntities.filter(
    (e) => e.case_id === caseId
  );

  const matched = caseScopedEntities.filter((e) => {
    return (
      e.canonical_name.toLowerCase().includes(normalized) ||
      e.masked_identifier.toLowerCase().includes(normalized) ||
      e.entity_type.toLowerCase().includes(normalized)
    );
  });

  return matched.slice(0, limit);
}

/**
 * Mock API Response Envelopes
 */
export const mockGlobalSearchApiResponse: GlobalSearchApiResponse = {
  success: true,
  data: {
    cases: mockAuthorizedCases,
    entities: mockAuthorizedEntities
  },
  request_id: 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d'
};

export const mockCaseEntitiesApiResponse: CaseEntitiesApiResponse = {
  success: true,
  data: mockAuthorizedEntities.filter((e) => e.case_id === CASE_1_ID),
  request_id: 'b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e'
};
