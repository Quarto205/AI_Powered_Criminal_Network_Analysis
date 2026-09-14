/**
 * AuditPanel Component
 * Strictly adheres to 02_DATABASE_SCHEMA.md, 04_API_SPEC.md (Section 4.5),
 * 07_AUTH_SECURITY.md (Section 7.1, 7.2), and 08_UI_DATA_CONTRACT.md.
 *
 * Dev B — Step 5:
 * - Immutable, append-only, case-scoped operational audit trail.
 * - RBAC enforced via PermissionGate (SUPERVISOR access only; INVESTIGATOR denied).
 * - Read-only invariant: zero edit, delete, overwrite, or mutation controls.
 * - Sensitive PII masking: raw phone numbers, bank accounts, and bearer secrets masked.
 * - Filtering by actor, action code (ENTITY_MERGE, PREDICTION_OVERRIDE, EXPORT_REPORT, etc.), and date range.
 * - Case Export trigger: POST /api/v1/cases/{case_id}/exports (PDF | CSV, include_audit_trail).
 * - Displays export_id, download_url, cryptographic hash, and non-accusatory investigative disclaimer.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldCheck,
  Lock,
  Download,
  Filter,
  Search,
  Calendar,
  FileText,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Clock,
  User,
  Shield,
  ExternalLink,
} from 'lucide-react';
import { AuditLogItem, ExportRequest, ExportResponse } from '../../contracts/audit';
import { UserRole } from '../../contracts/common';
import { Button } from '../common/Button';
import { PermissionGate } from '../common/PermissionGate';
import { apiClient } from '../../api';
import { useCase } from '../../context/CaseContext';
import { DEMO_AUDIT_LOGS } from '../../fixtures/demoAudit';
import { DEMO_CASE_ID } from '../../fixtures/demoCase';

export interface AuditPanelProps {
  caseId?: string;
  currentRole?: UserRole;
  auditLogs?: AuditLogItem[];
  onExportTriggered?: (response: ExportResponse) => void;
}

export const CANONICAL_EXPORT_DISCLAIMER =
  'Predictions and priority rankings represent investigative leads and do not constitute moral or legal proof of guilt.';

/**
 * Sanitizes and masks sensitive identifiers from audit descriptions.
 * Invariant: Raw phone numbers, bank accounts, and authorization tokens must never be exposed.
 */
export function sanitizeAuditDisplay(text: string | null | undefined): string {
  if (!text) return '-';

  return text
    // Redact bearer tokens or secrets
    .replace(/(?:Bearer\s+|token=)[a-zA-Z0-9_\-\.]+/gi, 'Bearer [REDACTED_SECRET]')
    // Redact 10-digit Indian mobile numbers or +91 sequences
    .replace(/(?:\+91[\s\-]?)?[6-9]\d{9}/g, (match) => {
      const clean = match.replace(/[\s\-]/g, '');
      const prefix = clean.startsWith('+91') ? '+91 ' : '';
      const numPart = clean.startsWith('+91') ? clean.slice(3) : clean;
      return `${prefix}${numPart.slice(0, 5)} •••••`;
    })
    // Redact full raw bank account numbers (9-18 consecutive digits)
    .replace(/\b\d{9,18}\b/g, (match) => `••••-••••-${match.slice(-4)}`);
}

export const AuditPanel: React.FC<AuditPanelProps> = ({
  caseId: propCaseId,
  currentRole: propRole,
  auditLogs: propAuditLogs,
  onExportTriggered,
}) => {
  let contextCaseId: string | null = null;
  let contextRole: UserRole = 'INVESTIGATOR';

  try {
    const caseCtx = useCase();
    contextCaseId = caseCtx.activeCaseId;
    contextRole = caseCtx.currentRole;
  } catch {
    // Isolated testing support
  }

  const effectiveCaseId = propCaseId ?? contextCaseId ?? DEMO_CASE_ID;
  const effectiveRole = propRole ?? contextRole;
  const isSupervisor = effectiveRole === 'SUPERVISOR';

  // Audit Logs State
  const [logs, setLogs] = useState<AuditLogItem[]>(() => propAuditLogs ?? []);
  const [loading, setLoading] = useState<boolean>(!propAuditLogs && isSupervisor);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Filters State
  const [actorQuery, setActorQuery] = useState<string>('');
  const [actionFilter, setActionFilter] = useState<string>('ALL');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Export State
  const [exportFormat, setExportFormat] = useState<'PDF' | 'CSV'>('PDF');
  const [includeAuditTrail, setIncludeAuditTrail] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportResult, setExportResult] = useState<ExportResponse | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // Fetch Audit Trail - ONLY if authorized (RBAC defense-in-depth)
  useEffect(() => {
    if (propAuditLogs) {
      setLogs(propAuditLogs);
      setLoading(false);
      return;
    }

    if (!isSupervisor) {
      // Do NOT fetch privileged audit data for unauthorized investigators
      setLogs([]);
      setLoading(false);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setFetchError(null);

    apiClient
      .getCaseAudit(effectiveCaseId)
      .then((resp) => {
        if (isMounted) {
          setLogs(resp.data.audit_logs);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          // Fall back to deterministic fixtures if mock/network returns error
          setLogs(DEMO_AUDIT_LOGS);
          setFetchError(err instanceof Error ? err.message : null);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [propAuditLogs, effectiveCaseId, isSupervisor]);

  // Unique actions present in the audit log for the action dropdown filter
  const availableActions = useMemo(() => {
    const defaultActions = [
      'CASE_CREATE',
      'DOCUMENT_UPLOAD',
      'ENTITY_EXTRACTION',
      'ANALYSIS_TRIGGER',
      'REVIEW_CONFIRM',
      'ENTITY_MERGE',
      'PREDICTION_OVERRIDE',
      'EXPORT_REPORT',
    ];
    const logActions = logs.map((l) => l.action);
    return Array.from(new Set([...defaultActions, ...logActions]));
  }, [logs]);

  // Filtered Audit Entries
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      // Actor filter
      if (actorQuery.trim() && !log.actor.toLowerCase().includes(actorQuery.toLowerCase().trim())) {
        return false;
      }

      // Action code filter
      if (actionFilter !== 'ALL' && log.action !== actionFilter) {
        return false;
      }

      // Date range filter
      if (startDate) {
        const startMillis = new Date(startDate).getTime();
        const logMillis = new Date(log.timestamp).getTime();
        if (logMillis < startMillis) return false;
      }

      if (endDate) {
        // End date inclusive of end of day
        const endMillis = new Date(endDate).getTime() + 86400000;
        const logMillis = new Date(log.timestamp).getTime();
        if (logMillis > endMillis) return false;
      }

      return true;
    });
  }, [logs, actorQuery, actionFilter, startDate, endDate]);

  const handleResetFilters = () => {
    setActorQuery('');
    setActionFilter('ALL');
    setStartDate('');
    setEndDate('');
  };

  // Trigger Case Report Export
  const handleExport = async () => {
    setIsExporting(true);
    setExportError(null);
    setExportResult(null);

    const payload: ExportRequest = {
      export_format: exportFormat,
      include_audit_trail: includeAuditTrail,
    };

    try {
      const resp = await apiClient.exportReport(effectiveCaseId, payload);
      if (resp.success && resp.data) {
        setExportResult(resp.data);
        if (onExportTriggered) {
          onExportTriggered(resp.data);
        }
      } else {
        throw new Error('Export service did not return a success envelope');
      }
    } catch (err: unknown) {
      setExportError(err instanceof Error ? err.message : 'Export failed due to service error');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <PermissionGate requiredRole="SUPERVISOR" currentRole={effectiveRole}>
      <div
        data-testid="audit-panel-root"
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          overflowY: 'auto',
          padding: '24px',
          background: '#090d16',
          gap: '24px',
        }}
      >
        {/* Panel Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: '16px',
            borderBottom: '1px solid #1e293b',
            paddingBottom: '18px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2
                data-testid="audit-panel-title"
                style={{ fontSize: '18px', fontWeight: 600, color: '#f8fafc', margin: 0 }}
              >
                Case Operations & Integrity Audit Ledger
              </h2>
              <span
                data-testid="role-badge"
                style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  fontWeight: 700,
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  color: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  textTransform: 'uppercase',
                }}
              >
                {effectiveRole} PRIVILEGED
              </span>
            </div>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0 0' }}>
              Append-only historical ledger of all case lifecycle actions, entity mergers, prediction overrides, and report exports.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Lock size={14} color="#10b981" />
            <span
              data-testid="immutable-badge"
              style={{
                fontSize: '11px',
                color: '#10b981',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
              }}
            >
              IMMUTABLE_LOG_ENFORCED
            </span>
          </div>
        </div>

        {/* Fetch Error Warning Banner */}
        {fetchError && (
          <div
            data-testid="audit-fetch-error-banner"
            style={{
              padding: '10px 14px',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: '#fbbf24',
              fontSize: '12px',
            }}
          >
            <AlertTriangle size={14} color="#fbbf24" />
            <span>Audit service fallback active: {fetchError}</span>
          </div>
        )}

        {/* Case Scope Context */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '12px',
            color: '#64748b',
          }}
        >
          <span>Target Case ID:</span>
          <span
            data-testid="audit-case-id"
            style={{ fontFamily: 'var(--font-mono)', color: '#94a3b8', fontWeight: 600 }}
          >
            {effectiveCaseId}
          </span>
        </div>

        {/* Case Export Trigger Section */}
        <div
          data-testid="case-export-section"
          style={{
            backgroundColor: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: '8px',
            padding: '18px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Download size={16} color="#38bdf8" />
              <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', margin: 0 }}>
                Case Dossier & Evidence Export
              </h3>
            </div>
            <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
              POST /api/v1/cases/{effectiveCaseId}/exports
            </span>
          </div>

          {/* Export Disclaimer */}
          <div
            data-testid="export-disclaimer"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
              padding: '8px 12px',
              backgroundColor: '#090d16',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              fontSize: '11px',
              color: '#94a3b8',
              lineHeight: 1.4,
            }}
          >
            <Shield size={14} color="#38bdf8" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{CANONICAL_EXPORT_DISCLAIMER}</span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '20px',
              flexWrap: 'wrap',
            }}
          >
            {/* Format Selection */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 500 }}>Format:</span>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  type="button"
                  data-testid="export-format-pdf"
                  onClick={() => setExportFormat('PDF')}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '5px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 600,
                    border: exportFormat === 'PDF' ? '1px solid #38bdf8' : '1px solid #334155',
                    backgroundColor: exportFormat === 'PDF' ? 'rgba(56, 189, 248, 0.15)' : '#1e293b',
                    color: exportFormat === 'PDF' ? '#38bdf8' : '#94a3b8',
                    cursor: 'pointer',
                  }}
                >
                  <FileText size={12} />
                  PDF Dossier
                </button>

                <button
                  type="button"
                  data-testid="export-format-csv"
                  onClick={() => setExportFormat('CSV')}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '5px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 600,
                    border: exportFormat === 'CSV' ? '1px solid #38bdf8' : '1px solid #334155',
                    backgroundColor: exportFormat === 'CSV' ? 'rgba(56, 189, 248, 0.15)' : '#1e293b',
                    color: exportFormat === 'CSV' ? '#38bdf8' : '#94a3b8',
                    cursor: 'pointer',
                  }}
                >
                  <FileSpreadsheet size={12} />
                  CSV Data
                </button>
              </div>
            </div>

            {/* Include Audit Trail Checkbox */}
            <label
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                color: '#e2e8f0',
                cursor: 'pointer',
                userSelect: 'none',
              }}
            >
              <input
                type="checkbox"
                data-testid="export-include-audit-checkbox"
                checked={includeAuditTrail}
                onChange={(e) => setIncludeAuditTrail(e.target.checked)}
                style={{
                  cursor: 'pointer',
                  accentColor: '#38bdf8',
                  width: '14px',
                  height: '14px',
                }}
              />
              <span>Include immutable audit trail in export</span>
            </label>

            {/* Trigger Button */}
            <Button
              variant="primary"
              size="sm"
              data-testid="export-trigger-btn"
              onClick={handleExport}
              disabled={isExporting}
            >
              {isExporting ? 'Generating Case Export...' : `Generate ${exportFormat} Export`}
            </Button>
          </div>

          {/* Export Success Banner */}
          {exportResult && (
            <div
              data-testid="export-success-banner"
              style={{
                padding: '12px 16px',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: '6px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={15} color="#10b981" />
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#10b981' }}>
                  Export Generated Successfully
                </span>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  color: '#94a3b8',
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <span style={{ color: '#64748b' }}>Export ID: </span>
                  <span data-testid="export-result-id" style={{ color: '#e2e8f0' }}>
                    {exportResult.export_id}
                  </span>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>SHA-256 Hash: </span>
                  <span data-testid="export-result-hash" style={{ color: '#38bdf8' }}>
                    {exportResult.hash}
                  </span>
                </div>
              </div>

              <div style={{ marginTop: '4px' }}>
                <a
                  href={exportResult.download_url}
                  data-testid="export-download-link"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: '#38bdf8',
                    fontSize: '12px',
                    fontWeight: 600,
                    textDecoration: 'none',
                  }}
                >
                  <ExternalLink size={13} />
                  Download Case Export
                </a>
              </div>
            </div>
          )}

          {/* Export Error Banner */}
          {exportError && (
            <div
              data-testid="export-error-banner"
              style={{
                padding: '10px 14px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: '#f87171',
                fontSize: '12px',
              }}
            >
              <AlertTriangle size={15} color="#f87171" />
              <span>{exportError}</span>
            </div>
          )}
        </div>

        {/* Filters Bar */}
        <div
          data-testid="audit-filters-bar"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            flexWrap: 'wrap',
            backgroundColor: '#0f172a',
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid #1e293b',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '12px' }}>
            <Filter size={14} />
            <span style={{ fontWeight: 600 }}>Filter Audit Trail:</span>
          </div>

          {/* Actor Search Input */}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={13} color="#64748b" style={{ position: 'absolute', left: '10px' }} />
            <input
              type="text"
              data-testid="audit-actor-search"
              placeholder="Search by actor..."
              value={actorQuery}
              onChange={(e) => setActorQuery(e.target.value)}
              style={{
                padding: '6px 10px 6px 30px',
                backgroundColor: '#090d16',
                border: '1px solid #334155',
                borderRadius: '4px',
                color: '#f8fafc',
                fontSize: '11px',
                outline: 'none',
                width: '180px',
              }}
            />
          </div>

          {/* Action Code Dropdown */}
          <select
            data-testid="audit-action-filter"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            style={{
              padding: '6px 10px',
              backgroundColor: '#090d16',
              border: '1px solid #334155',
              borderRadius: '4px',
              color: '#f8fafc',
              fontSize: '11px',
              outline: 'none',
            }}
          >
            <option value="ALL">All Actions</option>
            {availableActions.map((act) => (
              <option key={act} value={act}>
                {act}
              </option>
            ))}
          </select>

          {/* Date Range Inputs */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Calendar size={13} color="#64748b" />
            <input
              type="date"
              data-testid="audit-date-start"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{
                padding: '5px 8px',
                backgroundColor: '#090d16',
                border: '1px solid #334155',
                borderRadius: '4px',
                color: '#f8fafc',
                fontSize: '11px',
                outline: 'none',
              }}
            />
            <span style={{ color: '#64748b', fontSize: '11px' }}>to</span>
            <input
              type="date"
              data-testid="audit-date-end"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{
                padding: '5px 8px',
                backgroundColor: '#090d16',
                border: '1px solid #334155',
                borderRadius: '4px',
                color: '#f8fafc',
                fontSize: '11px',
                outline: 'none',
              }}
            />
          </div>

          {/* Reset Filters */}
          {(actorQuery || actionFilter !== 'ALL' || startDate || endDate) && (
            <button
              type="button"
              data-testid="audit-reset-filters-btn"
              onClick={handleResetFilters}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '5px 8px',
                backgroundColor: 'transparent',
                border: 'none',
                color: '#38bdf8',
                fontSize: '11px',
                cursor: 'pointer',
              }}
            >
              <RotateCcw size={11} />
              Reset Filters
            </button>
          )}

          <div style={{ marginLeft: 'auto', fontSize: '11px', color: '#64748b' }}>
            Showing{' '}
            <span data-testid="audit-count" style={{ color: '#e2e8f0', fontWeight: 600 }}>
              {filteredLogs.length}
            </span>{' '}
            of {logs.length} events
          </div>
        </div>

        {/* Audit Log Table (Read-Only / Append-Only Invariant) */}
        <div
          data-testid="audit-table-container"
          style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: '8px',
            overflow: 'hidden',
          }}
        >
          {loading ? (
            <div style={{ padding: '36px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
              Loading immutable audit records...
            </div>
          ) : filteredLogs.length === 0 ? (
            <div
              data-testid="audit-empty-state"
              style={{
                padding: '40px 24px',
                textAlign: 'center',
                color: '#64748b',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <FileText size={28} color="#334155" />
              <div style={{ fontSize: '13px', color: '#94a3b8', fontWeight: 500 }}>
                No audit records match the selected filter criteria.
              </div>
            </div>
          ) : (
            <table
              data-testid="audit-table"
              style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}
            >
              <thead>
                <tr style={{ background: '#131d36', borderBottom: '1px solid #1e293b', color: '#94a3b8' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600, width: '180px' }}>Timestamp (IST)</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, width: '220px' }}>Actor</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, width: '180px' }}>Action</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Target Item / Context</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, width: '110px' }}>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => {
                  const sanitizedTarget = sanitizeAuditDisplay(log.target_item);

                  return (
                    <tr
                      key={log.audit_id}
                      data-testid={`audit-row-${log.audit_id}`}
                      style={{ borderBottom: '1px solid #1e293b' }}
                    >
                      {/* Timestamp */}
                      <td
                        data-testid="audit-cell-timestamp"
                        style={{
                          padding: '12px 16px',
                          color: '#94a3b8',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '11px',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={11} color="#64748b" />
                          <span>
                            {new Date(log.timestamp).toLocaleString('en-IN', {
                              timeZone: 'Asia/Kolkata',
                              dateStyle: 'short',
                              timeStyle: 'medium',
                            })}{' '}
                            IST
                          </span>
                        </div>
                      </td>

                      {/* Actor */}
                      <td
                        data-testid="audit-cell-actor"
                        style={{ padding: '12px 16px', color: '#f8fafc', fontWeight: 500 }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <User size={13} color="#64748b" />
                          <span>{log.actor}</span>
                        </div>
                      </td>

                      {/* Action Code */}
                      <td data-testid="audit-cell-action" style={{ padding: '12px 16px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            backgroundColor:
                              log.action === 'ENTITY_MERGE'
                                ? 'rgba(168, 85, 247, 0.15)'
                                : log.action === 'PREDICTION_OVERRIDE'
                                ? 'rgba(245, 158, 11, 0.15)'
                                : log.action === 'EXPORT_REPORT'
                                ? 'rgba(56, 189, 248, 0.15)'
                                : 'rgba(100, 116, 139, 0.2)',
                            color:
                              log.action === 'ENTITY_MERGE'
                                ? '#c084fc'
                                : log.action === 'PREDICTION_OVERRIDE'
                                ? '#fbbf24'
                                : log.action === 'EXPORT_REPORT'
                                ? '#38bdf8'
                                : '#cbd5e1',
                            border:
                              log.action === 'ENTITY_MERGE'
                                ? '1px solid rgba(168, 85, 247, 0.3)'
                                : log.action === 'PREDICTION_OVERRIDE'
                                ? '1px solid rgba(245, 158, 11, 0.3)'
                                : log.action === 'EXPORT_REPORT'
                                ? '1px solid rgba(56, 189, 248, 0.3)'
                                : '1px solid rgba(100, 116, 139, 0.3)',
                          }}
                        >
                          {log.action}
                        </span>
                      </td>

                      {/* Target Item / Context (Sanitized & Masked) */}
                      <td
                        data-testid="audit-cell-target"
                        style={{ padding: '12px 16px', color: '#cbd5e1', lineHeight: 1.45 }}
                      >
                        <span>{sanitizedTarget}</span>
                      </td>

                      {/* Outcome */}
                      <td data-testid="audit-cell-outcome" style={{ padding: '12px 16px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            color: log.outcome === 'SUCCESS' ? '#10b981' : '#f87171',
                            fontWeight: 600,
                            fontSize: '11px',
                          }}
                        >
                          <ShieldCheck size={13} />
                          {log.outcome}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </PermissionGate>
  );
};
