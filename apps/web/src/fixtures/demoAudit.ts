/**
 * Deterministic Synthetic Audit Ledger Fixture
 * Strictly adheres to 07_AUTH_SECURITY.md and 02_DATABASE_SCHEMA.md (audit_logs table).
 */

import { AuditLogItem } from '../contracts/audit';

export const DEMO_AUDIT_LOGS: AuditLogItem[] = [
  {
    audit_id: 'aud-001',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'CASE_CREATE',
    target_item: 'CR-2026-DEL-0891',
    timestamp: '2026-08-14T09:30:00Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-002',
    actor: 'sub_verma@delhipolice.gov.in (Investigator)',
    action: 'DOCUMENT_UPLOAD',
    target_item: 'FIR_104_2026_SpecialCell.pdf',
    timestamp: '2026-08-14T09:45:12Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-003',
    actor: 'Agent 1 NLP Worker',
    action: 'ENTITY_EXTRACTION',
    target_item: '14 entities, 12 relations extracted',
    timestamp: '2026-08-14T09:48:30Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-004',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'ANALYSIS_TRIGGER',
    target_item: 'Pipelines: [SNA, PATTERN_MOTIFS, GAT_LINK_PREDICTION]',
    timestamp: '2026-08-14T11:30:00Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-005',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'REVIEW_CONFIRM',
    target_item: 'Confirmed entity alias: Raju Seth -> Rajesh Sharma',
    timestamp: '2026-08-14T14:22:05Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-006',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'ENTITY_MERGE',
    target_item: 'Merged alias node-person-1 (Tariq Khan) with candidate ent-tariq-alias',
    timestamp: '2026-08-14T15:10:00Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-007',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'PREDICTION_OVERRIDE',
    target_item: 'Override link prediction pred-001 (KNOWS between Tariq Khan & Rajesh Gupta) -> REJECTED: Verified legitimate vendor relationship',
    timestamp: '2026-08-14T16:05:30Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-008',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'EXPORT_REPORT',
    target_item: 'Exported case summary dossier (Format: PDF, Hash: sha256:88fa2901bce47101ef)',
    timestamp: '2026-08-14T17:00:00Z',
    outcome: 'SUCCESS',
  },
];
