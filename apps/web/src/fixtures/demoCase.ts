/**
 * Deterministic Synthetic Demo Case Fixture
 * Clearly marked as synthetic test data for SIH26189 demo scenario.
 */

import { CaseDetailResponse, CaseListItem } from '../contracts/cases';

export const DEMO_CASE_ID = '3fa85f64-5717-4562-b3fc-2c963f66afa6';
export const DEMO_CASE_2_ID = '7c9e6679-7425-40de-944b-e07fc1f90ae7';

export const DEMO_CASE_DETAIL: CaseDetailResponse = {
  case_id: DEMO_CASE_ID,
  case_code: 'CR-2026-DEL-0891',
  title: 'Operation Hawala Nexus — Cyber & Financial Syndicate',
  description: 'Investigation into coordinated inter-state mule account networks and illicit communications routing across Delhi NCR and Mumbai.',
  status: 'ACTIVE',
  jurisdiction: 'New Delhi - Special Cell / Crime Branch',
  created_by: '11111111-2222-3333-4444-555555555555',
  created_at: '2026-08-14T09:30:00Z',
  document_count: 8,
  entity_count: 14,
};

export const DEMO_CASES_LIST: CaseListItem[] = [
  {
    case_id: DEMO_CASE_ID,
    case_code: 'CR-2026-DEL-0891',
    title: 'Operation Hawala Nexus — Cyber & Financial Syndicate',
    status: 'ACTIVE',
    jurisdiction: 'New Delhi - Special Cell',
    member_role: 'SUPERVISOR',
    created_at: '2026-08-14T09:30:00Z',
  },
  {
    case_id: DEMO_CASE_2_ID,
    case_code: 'CR-2026-MUM-0312',
    title: 'Cross-Border Telecom Smuggling Syndicate',
    status: 'PENDING_REVIEW',
    jurisdiction: 'Mumbai - Cyber Police Station',
    member_role: 'INVESTIGATOR',
    created_at: '2026-08-20T14:15:00Z',
  },
];


export const DEMO_AUDIT_LOGS = [
  {
    audit_id: 'aud-001',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'CASE_CREATE',
    target_item: 'CR-2026-DEL-0891',
    timestamp: '2026-08-14T09:30:00Z',
    outcome: 'SUCCESS',
  },
];

