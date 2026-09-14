/**
 * SIH26189 â€” Deterministic Case Management Mock Fixtures
 * Strictly adheres to 02_DATABASE_SCHEMA.md, 04_API_SPEC.md, and contracts.ts.
 *
 * NOTE: For frontend development and testing only.
 * Contains synthetic Indian investigation scenario data (Special Cell Hawala & Illegal Telecom Nexus).
 */

import {
  CaseDetailResponse,
  CaseListItem,
  CaseListResponse,
  CaseMemberItem,
  UserRoles,
  UUID,
} from '../types/contracts';

export const MOCK_CASE_ID: UUID = 'e7b1a2c4-893f-4e12-b567-91a0c4581234';
export const MOCK_CASE_CODE = 'CR-2026-DEL-0891';

export const MOCK_CASE_DETAIL: CaseDetailResponse = {
  case_id: MOCK_CASE_ID,
  case_code: MOCK_CASE_CODE,
  title: 'Special Cell Hawala & Cross-Border Telecom Nexus',
  description:
    'Investigation into coordinated hawala transactions and unregistered SIM networks operating across Old Delhi, Jamia Nagar, and NCR corridors.',
  status: 'ACTIVE',
  jurisdiction: 'Special Cell, Delhi Police (Northern Range)',
  created_by: '11111111-2222-3333-4444-555555555555',
  created_at: '2026-02-15T09:30:00Z',
  document_count: 7,
  entity_count: 14,
};

export const MOCK_CASE_MEMBERS: CaseMemberItem[] = [
  {
    user_id: '11111111-2222-3333-4444-555555555555',
    username: 'insp_sharma',
    email: 'v.sharma@delhipolice.gov.in',
    role_in_case: UserRoles.INVESTIGATOR,
  },
  {
    user_id: '22222222-3333-4444-5555-666666666666',
    username: 'analyst_priya',
    email: 'p.verma@delhipolice.gov.in',
    role_in_case: UserRoles.ANALYST,
  },
  {
    user_id: '33333333-4444-5555-6666-777777777777',
    username: 'acp_singh',
    email: 'r.singh@delhipolice.gov.in',
    role_in_case: UserRoles.SUPERVISOR,
  },
];

export const MOCK_CASE_LIST: CaseListItem[] = [
  {
    case_id: MOCK_CASE_ID,
    case_code: MOCK_CASE_CODE,
    title: 'Special Cell Hawala & Cross-Border Telecom Nexus',
    status: 'ACTIVE',
    jurisdiction: 'Special Cell, Delhi Police',
    member_role: UserRoles.INVESTIGATOR,
    created_at: '2026-02-15T09:30:00Z',
  },
  {
    case_id: 'f8c2b3d5-904a-4f23-c678-02b1d5692345',
    case_code: 'CR-2026-DEL-0412',
    title: 'Counterfeit Currency Circulation - Chandni Chowk Syndicate',
    status: 'ACTIVE',
    jurisdiction: 'Crime Branch, Delhi Police',
    member_role: UserRoles.ANALYST,
    created_at: '2026-01-20T14:15:00Z',
  },
  {
    case_id: 'a1d3c4e6-015b-5a34-d789-13c2e6703456',
    case_code: 'CR-2025-HAR-1092',
    title: 'SIM Swap & Inter-State Banking Fraud Group',
    status: 'PENDING_REVIEW',
    jurisdiction: 'Cyber Crime PS, Gurugram',
    member_role: UserRoles.SUPERVISOR,
    created_at: '2025-11-05T11:00:00Z',
  },
];

export const MOCK_CASE_LIST_RESPONSE: CaseListResponse = {
  cases: MOCK_CASE_LIST,
  total: MOCK_CASE_LIST.length,
  limit: 10,
  offset: 0,
};

// --- Track A Compatibility Mocks ---
/**
 * SIH26189 â€” Deterministic Case Mocks
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
  jurisdiction: 'Delhi NCR \u2014 Special Cell',
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
    jurisdiction: 'Mumbai â€” Cyber & Economic Offenses',
    created_by: 'f1e2d3c4-b5a6-4789-8012-3456789abcde',
    created_at: '2026-08-28T14:15:00Z',
    member_role: 'ANALYST',
    document_count: 9,
    entity_count: 31
  }
];
