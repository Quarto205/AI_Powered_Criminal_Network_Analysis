/**
 * SIH26189 — Deterministic Case Management Mock Fixtures
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
