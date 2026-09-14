/**
 * Unit & Integration Tests for AuditPanel & PermissionGate Components
 * Strictly adheres to 02_DATABASE_SCHEMA.md, 04_API_SPEC.md (Section 4.5),
 * 07_AUTH_SECURITY.md (Section 7.1, 7.2), and 08_UI_DATA_CONTRACT.md.
 *
 * Dev B — Step 5:
 * Covers all 16 minimum test requirements:
 * 1. SUPERVISOR can access the audit panel
 * 2. INVESTIGATOR cannot access privileged audit data
 * 3. Unauthorized state is handled safely
 * 4. Audit entries render correctly
 * 5. Actor filtering works
 * 6. Action filtering works
 * 7. Date-range filtering works
 * 8. Sensitive identifiers remain masked/redacted
 * 9. Audit entries have no edit/delete controls (immutable invariant)
 * 10. Export format selection works for PDF/CSV
 * 11. Export request contains correct include_audit_trail
 * 12. Successful export displays export ID/hash/download state
 * 13. Failed export is handled without false success
 * 14. Case ID is correctly scoped
 * 15. Existing graph/context state is preserved
 * 16. Non-accusatory export/investigative disclaimer is preserved
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import {
  AuditPanel,
  CANONICAL_EXPORT_DISCLAIMER,
  sanitizeAuditDisplay,
} from '../components/panels/AuditPanel';
import { CaseProvider } from '../context/CaseContext';
import { SelectionProvider, useSelection } from '../context/SelectionContext';
import { AuditLogItem } from '../contracts/audit';
import { apiClient } from '../api';

const MOCK_AUDIT_LOGS: AuditLogItem[] = [
  {
    audit_id: 'aud-001',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'CASE_CREATE',
    target_item: 'Case CR-2026-DEL-0891 registered',
    timestamp: '2026-08-14T09:30:00Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-002',
    actor: 'sub_verma@delhipolice.gov.in (Investigator)',
    action: 'DOCUMENT_UPLOAD',
    target_item: 'FIR_104_2026_SpecialCell.pdf',
    timestamp: '2026-08-14T10:15:00Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-003',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'ENTITY_MERGE',
    target_item: 'Merged alias node-person-1 (Tariq Khan) with candidate ent-tariq-alias',
    timestamp: '2026-08-14T12:00:00Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-004',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'PREDICTION_OVERRIDE',
    target_item: 'Override link prediction pred-001 (KNOWS between Tariq Khan & Rajesh Gupta) -> REJECTED: Verified legitimate vendor relationship',
    timestamp: '2026-08-15T14:30:00Z',
    outcome: 'SUCCESS',
  },
  {
    audit_id: 'aud-005',
    actor: 'ins_sharma@delhipolice.gov.in (Supervisor)',
    action: 'EXPORT_REPORT',
    target_item: 'Exported case dossier (Format: PDF, Hash: sha256:88fa2901bce47101ef)',
    timestamp: '2026-08-16T16:00:00Z',
    outcome: 'SUCCESS',
  },
];

describe('AuditPanel Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. SUPERVISOR can access the audit panel
  it('1. permits SUPERVISOR to access the audit panel and renders title & badge', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    expect(screen.getByTestId('audit-panel-root')).toBeInTheDocument();
    expect(screen.getByTestId('audit-panel-title')).toHaveTextContent(
      'Case Operations & Integrity Audit Ledger'
    );
    expect(screen.getByTestId('role-badge')).toHaveTextContent('SUPERVISOR PRIVILEGED');
  });

  // 2. INVESTIGATOR cannot access privileged audit data
  it('2. blocks INVESTIGATOR from accessing privileged audit data via PermissionGate', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="INVESTIGATOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    expect(screen.queryByTestId('audit-panel-root')).not.toBeInTheDocument();
    expect(screen.getByTestId('permission-gate-restricted')).toBeInTheDocument();
    expect(screen.getByTestId('current-role-badge')).toHaveTextContent('INVESTIGATOR');
    expect(screen.getByTestId('required-role-badge')).toHaveTextContent('SUPERVISOR');
  });

  // 3. Unauthorized state is handled safely (no leak of audit logs)
  it('3. handles unauthorized state safely without leaking audit row data or calling API', () => {
    const getAuditSpy = vi.spyOn(apiClient, 'getCaseAudit');

    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="INVESTIGATOR"
      />
    );

    expect(screen.queryByTestId('audit-table')).not.toBeInTheDocument();
    expect(screen.queryByText('Tariq Khan')).not.toBeInTheDocument();
    expect(screen.queryByText('PREDICTION_OVERRIDE')).not.toBeInTheDocument();
    // Invariant: Unauthorized role must never trigger privileged audit fetch
    expect(getAuditSpy).not.toHaveBeenCalled();
  });

  // 4. Audit entries render correctly with timestamp, actor, action, target item, outcome
  it('4. renders audit rows with timestamp, actor, action, target item, and outcome', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const row1 = screen.getByTestId('audit-row-aud-001');
    expect(row1).toBeInTheDocument();
    expect(screen.getByTestId('audit-row-aud-003')).toBeInTheDocument();
    expect(within(row1).getByText('ins_sharma@delhipolice.gov.in (Supervisor)')).toBeInTheDocument();
    expect(within(row1).getByText('CASE_CREATE')).toBeInTheDocument();
    expect(within(row1).getByText('Case CR-2026-DEL-0891 registered')).toBeInTheDocument();
  });

  // 5. Actor filtering works
  it('5. filters audit entries correctly by actor substring search', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const searchInput = screen.getByTestId('audit-actor-search');
    fireEvent.change(searchInput, { target: { value: 'sub_verma' } });

    expect(screen.getByTestId('audit-row-aud-002')).toBeInTheDocument();
    expect(screen.queryByTestId('audit-row-aud-001')).not.toBeInTheDocument();
    expect(screen.queryByTestId('audit-row-aud-003')).not.toBeInTheDocument();
    expect(screen.getByTestId('audit-count')).toHaveTextContent('1');
  });

  // 6. Action filtering works (ENTITY_MERGE, PREDICTION_OVERRIDE, EXPORT_REPORT)
  it('6. filters audit entries correctly by action dropdown', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const actionSelect = screen.getByTestId('audit-action-filter');

    // Filter to ENTITY_MERGE
    fireEvent.change(actionSelect, { target: { value: 'ENTITY_MERGE' } });
    expect(screen.getByTestId('audit-row-aud-003')).toBeInTheDocument();
    expect(screen.queryByTestId('audit-row-aud-001')).not.toBeInTheDocument();

    // Filter to PREDICTION_OVERRIDE
    fireEvent.change(actionSelect, { target: { value: 'PREDICTION_OVERRIDE' } });
    expect(screen.getByTestId('audit-row-aud-004')).toBeInTheDocument();
    expect(screen.queryByTestId('audit-row-aud-003')).not.toBeInTheDocument();

    // Filter to EXPORT_REPORT
    fireEvent.change(actionSelect, { target: { value: 'EXPORT_REPORT' } });
    expect(screen.getByTestId('audit-row-aud-005')).toBeInTheDocument();
    expect(screen.queryByTestId('audit-row-aud-004')).not.toBeInTheDocument();
  });

  // 7. Date-range filtering works
  it('7. filters audit entries correctly by start and end date range', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const startDate = screen.getByTestId('audit-date-start');
    const endDate = screen.getByTestId('audit-date-end');

    // Only events on 2026-08-15
    fireEvent.change(startDate, { target: { value: '2026-08-15' } });
    fireEvent.change(endDate, { target: { value: '2026-08-15' } });

    expect(screen.getByTestId('audit-row-aud-004')).toBeInTheDocument();
    expect(screen.queryByTestId('audit-row-aud-001')).not.toBeInTheDocument();
    expect(screen.queryByTestId('audit-row-aud-005')).not.toBeInTheDocument();
  });

  // 8. Sensitive identifiers remain masked/redacted
  it('8. redacts and masks raw phone numbers, bank accounts, and authorization tokens', () => {
    const rawPiiLogs: AuditLogItem[] = [
      {
        audit_id: 'aud-pii-01',
        actor: 'system',
        action: 'CALL_RECORD',
        target_item: 'Call from +91 9873122345 to 9811099881 with token=secretToken12345678',
        timestamp: '2026-08-14T09:30:00Z',
        outcome: 'SUCCESS',
      },
      {
        audit_id: 'aud-pii-02',
        actor: 'system',
        action: 'FINANCIAL_TX',
        target_item: 'Account transfer from 12345678901234 to 98765432101234 for INR 500000',
        timestamp: '2026-08-14T09:35:00Z',
        outcome: 'SUCCESS',
      },
    ];

    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={rawPiiLogs}
      />
    );

    // Verify raw unmasked phone numbers are NOT in the DOM
    expect(screen.queryByText(/9873122345/)).not.toBeInTheDocument();
    expect(screen.queryByText(/secretToken12345678/)).not.toBeInTheDocument();
    expect(screen.queryByText(/12345678901234/)).not.toBeInTheDocument();

    // Verify sanitized outputs
    expect(sanitizeAuditDisplay(rawPiiLogs[0].target_item)).toContain('•••••');
    expect(sanitizeAuditDisplay(rawPiiLogs[0].target_item)).toContain('[REDACTED_SECRET]');
    expect(sanitizeAuditDisplay(rawPiiLogs[1].target_item)).toContain('••••-••••-1234');
  });

  // 9. Audit entries have no edit/delete controls (immutable invariant)
  it('9. strictly enforces read-only invariant: zero edit, delete, overwrite, or mutate buttons', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    expect(screen.getByTestId('immutable-badge')).toHaveTextContent('IMMUTABLE_LOG_ENFORCED');
    expect(screen.queryByText(/edit/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/delete/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/remove/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/mutate/i)).not.toBeInTheDocument();
  });

  // 10. Export format selection works for PDF/CSV
  it('10. permits toggling export format between PDF Dossier and CSV Data', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const pdfBtn = screen.getByTestId('export-format-pdf');
    const csvBtn = screen.getByTestId('export-format-csv');
    const triggerBtn = screen.getByTestId('export-trigger-btn');

    expect(triggerBtn).toHaveTextContent('Generate PDF Export');

    fireEvent.click(csvBtn);
    expect(triggerBtn).toHaveTextContent('Generate CSV Export');

    fireEvent.click(pdfBtn);
    expect(triggerBtn).toHaveTextContent('Generate PDF Export');
  });

  // 11. Export request contains correct include_audit_trail
  it('11. includes include_audit_trail flag in export API call', async () => {
    const exportSpy = vi.spyOn(apiClient, 'exportReport').mockResolvedValueOnce({
      success: true,
      data: {
        export_id: 'exp-test-999',
        download_url: '/api/v1/cases/test-case-001/exports/download?format=PDF',
        hash: 'sha256:test-hash-123456',
      },
      error: null,
      tracking_id: 'trk-test-999',
    });

    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const checkbox = screen.getByTestId('export-include-audit-checkbox');
    expect(checkbox).toBeChecked();

    // Toggle off
    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();

    // Click export
    const triggerBtn = screen.getByTestId('export-trigger-btn');
    fireEvent.click(triggerBtn);

    await waitFor(() => {
      expect(exportSpy).toHaveBeenCalledWith('test-case-001', {
        export_format: 'PDF',
        include_audit_trail: false,
      });
    });
  });

  // 12. Successful export displays export ID/hash/download state
  it('12. displays export ID, cryptographic hash, and download link on successful export', async () => {
    vi.spyOn(apiClient, 'exportReport').mockResolvedValueOnce({
      success: true,
      data: {
        export_id: 'exp-success-001',
        download_url: '/api/v1/cases/test-case-001/exports/download?format=PDF',
        hash: 'sha256:abc123def456',
      },
      error: null,
      tracking_id: 'trk-success-001',
    });

    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const triggerBtn = screen.getByTestId('export-trigger-btn');
    fireEvent.click(triggerBtn);

    await waitFor(() => {
      expect(screen.getByTestId('export-success-banner')).toBeInTheDocument();
      expect(screen.getByTestId('export-result-id')).toHaveTextContent('exp-success-001');
      expect(screen.getByTestId('export-result-hash')).toHaveTextContent('sha256:abc123def456');
      expect(screen.getByTestId('export-download-link')).toHaveAttribute(
        'href',
        '/api/v1/cases/test-case-001/exports/download?format=PDF'
      );
    });
  });

  // 13. Failed export is handled without false success
  it('13. handles export service errors gracefully without false success banner', async () => {
    vi.spyOn(apiClient, 'exportReport').mockRejectedValueOnce(
      new Error('SERVICE_UNAVAILABLE: Export worker timeout')
    );

    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const triggerBtn = screen.getByTestId('export-trigger-btn');
    fireEvent.click(triggerBtn);

    await waitFor(() => {
      expect(screen.getByTestId('export-error-banner')).toBeInTheDocument();
      expect(screen.getByTestId('export-error-banner')).toHaveTextContent(
        'SERVICE_UNAVAILABLE: Export worker timeout'
      );
      expect(screen.queryByTestId('export-success-banner')).not.toBeInTheDocument();
    });
  });

  // 14. Case ID is correctly scoped
  it('14. correctly scopes audit trail and export trigger to case ID', () => {
    render(
      <AuditPanel
        caseId="CR-2026-DEL-0891"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    expect(screen.getByTestId('audit-case-id')).toHaveTextContent('CR-2026-DEL-0891');
  });

  // 15. Existing graph/context state is preserved
  it('15. operates without disturbing SelectionContext selection state', () => {
    const TestWrapper: React.FC = () => {
      const { selectedNode, selectNode } = useSelection();

      return (
        <div>
          <div data-testid="selected-node-display">
            {selectedNode ? selectedNode.id : 'NONE'}
          </div>
          <button
            type="button"
            data-testid="select-node-btn"
            onClick={() =>
              selectNode({
                id: 'node-tariq-1',
                label: 'Tariq Khan',
                type: 'PERSON',
                entity_type: 'PERSON',
                case_id: 'test-case-001',
              })
            }
          >
            Select Node
          </button>
          <AuditPanel
            caseId="test-case-001"
            currentRole="SUPERVISOR"
            auditLogs={MOCK_AUDIT_LOGS}
          />
        </div>
      );
    };

    render(
      <CaseProvider>
        <SelectionProvider>
          <TestWrapper />
        </SelectionProvider>
      </CaseProvider>
    );

    expect(screen.getByTestId('selected-node-display')).toHaveTextContent('NONE');

    fireEvent.click(screen.getByTestId('select-node-btn'));
    expect(screen.getByTestId('selected-node-display')).toHaveTextContent('node-tariq-1');

    // Filter audit logs
    const actionSelect = screen.getByTestId('audit-action-filter');
    fireEvent.change(actionSelect, { target: { value: 'ENTITY_MERGE' } });

    // Graph node selection is preserved
    expect(screen.getByTestId('selected-node-display')).toHaveTextContent('node-tariq-1');
  });

  // 16. Non-accusatory export/investigative disclaimer is preserved
  it('16. displays canonical non-accusatory disclaimer for exports and investigative leads', () => {
    render(
      <AuditPanel
        caseId="test-case-001"
        currentRole="SUPERVISOR"
        auditLogs={MOCK_AUDIT_LOGS}
      />
    );

    const disclaimerEl = screen.getByTestId('export-disclaimer');
    expect(disclaimerEl).toBeInTheDocument();
    expect(disclaimerEl).toHaveTextContent(CANONICAL_EXPORT_DISCLAIMER);
    expect(disclaimerEl).toHaveTextContent(
      'Predictions and priority rankings represent investigative leads and do not constitute moral or legal proof of guilt.'
    );
  });
});
