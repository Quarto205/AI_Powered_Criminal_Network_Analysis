/**
 * SIH26189 — Deterministic Case Mocks
 * Source: docs/contracts/04_API_SPEC.md & 06_WORKFLOWS.md
 * 
 * Invariants:
 * 1. Strictly deterministic fixtures: no Math.random(), no dynamic dates.
 * 2. All application IDs are valid UUID-v4 format.
 * 3. Human-readable identifiers (DL-2026-CR-0192) are case_code references, never primary keys.
 * 4. Synthetic data only: no real PII, police records, or secret credentials.
 * 5. Stealth authorization fixture: 404 response obscures resource existence.
 */

import { CaseDetails, ApiResponse } from '../types/shell';

/**
 * Deterministic active case fixture
 */
export const mockActiveCase: CaseDetails = {
  case_id: 'a8f3b2e1-4c5d-4f6a-9b8c-7d6e5f4a3b2c',
  case_code: 'DL-2026-CR-0192',
  title: 'Syndicate Hawala & Mule Network Investigation',
  description: 'Multi-jurisdictional financial routing and suspected contraband distribution network across Northern NCR corridor.',
  status: 'GRAPH_READY',
  jurisdiction: 'Delhi NCR — Special Cell',
  created_by: 'f1e2d3c4-b5a6-4789-8012-3456789abcde',
  created_at: '2026-08-15T09:30:00Z',
  member_role: 'INVESTIGATOR',
  document_count: 14,
  entity_count: 48
};

/**
 * Deterministic successful API response envelope
 */
export const mockActiveCaseResponse: ApiResponse<CaseDetails> = {
  success: true,
  data: mockActiveCase,
  request_id: 'e7b1a2c3-d4e5-4f60-8192-a3b4c5d6e7f8'
};

/**
 * Deterministic 404 stealth authorization error envelope (06_WORKFLOWS.md Section 6.2)
 * Intentionally generic to prevent case enumeration without leaking whether the case exists.
 */
export const mockCaseNotFoundResponse: ApiResponse<CaseDetails> = {
  success: false,
  data: null,
  error: {
    code: 'ERR_CASE_NOT_FOUND',
    message: 'The requested case resource was not found or access is not authorized.',
    details: null
  },
  request_id: '9f8e7d6c-5b4a-4321-8fed-cba987654321'
};

/**
 * Deterministic secondary case fixtures for navigation demonstration
 */
export const mockCasesList: CaseDetails[] = [
  mockActiveCase,
  {
    case_id: 'b9e4c3d2-5a6b-4c7d-8e9f-0a1b2c3d4e5f',
    case_code: 'MH-2026-EC-0084',
    title: 'Offshore Remittance & Shell Logistics Inquiry',
    description: 'Cross-border layered trade-based remittance network involving proxy shipping entities.',
    status: 'ANALYSIS',
    jurisdiction: 'Mumbai — Cyber & Economic Offenses',
    created_by: 'f1e2d3c4-b5a6-4789-8012-3456789abcde',
    created_at: '2026-08-28T14:15:00Z',
    member_role: 'ANALYST',
    document_count: 9,
    entity_count: 31
  }
];
