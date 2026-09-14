/**
 * AlertsPanel Component
 * Strictly adheres to 01_SHARED_TYPES.md, 04_API_SPEC.md, 05_AI_CONTRACTS.md (Section 5.4.B), and 08_UI_DATA_CONTRACT.md.
 *
 * Dev B — Step 4:
 * - Deterministic motif pattern alerts (Cycles, Bursts, Fan-out/in, Bridge nodes).
 * - Safe temporal handling: explicitly flags "Insufficient Temporal Data" instead of creating false anomalies.
 * - Severity and status filtering.
 * - Non-disruptive "Focus on Canvas" leveraging SelectionContext without Cytoscape remount or zoom/pan reset.
 * - "Mark Reviewed" status transition (NEW -> REVIEWED).
 * - Strictly non-accusatory terminology (never labels patterns as guilt or crime probabilities).
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Bell,
  AlertTriangle,
  Info,
  CheckCircle2,
  Filter,
  Eye,
  X,
  Clock,
  GitBranch,
  Repeat,
  Zap,
  Activity,
  AlertCircle,
} from 'lucide-react';
import { AlertItem, AlertContributingEntity } from '../../types/contracts';
import { Button } from '../common/Button';
import { apiClient } from '../../api';
import { useCase } from '../../context/CaseContext';
import { useSelection } from '../../context/SelectionContext';
import { DEMO_ALERTS } from '../../fixtures/demoAlerts';
import { MOCK_GRAPH_NODES } from '../../mocks/graphMock';

export interface AlertsPanelProps {
  caseId?: string;
  alerts?: AlertItem[];
  onFocusEntities?: (entityIds: string[]) => void;
  onAlertReviewed?: (alertId: string) => void;
  onClose?: () => void;
}

export function getContributingEntitiesList(alert: AlertItem): AlertContributingEntity[] {
  if (Array.isArray(alert.contributing_entities)) {
    return alert.contributing_entities as AlertContributingEntity[];
  }
  return [];
}

// Motif type helper for human-readable labels and icons
export function getMotifCategory(alertType: string): {
  label: string;
  category: 'FINANCIAL_CYCLE' | 'COMMUNICATION_BURST' | 'FAN_OUT_IN' | 'BRIDGE_NODE' | 'OTHER';
  icon: React.ReactNode;
} {
  const upper = alertType.toUpperCase();
  if (upper.includes('CYCLE') || upper.includes('CIRCULAR')) {
    return {
      label: 'Financial Transaction Cycle (A → B → C → A)',
      category: 'FINANCIAL_CYCLE',
      icon: <Repeat size={15} color="#38bdf8" />,
    };
  }
  if (upper.includes('BURST') || upper.includes('SURGE')) {
    return {
      label: 'Communication Burst',
      category: 'COMMUNICATION_BURST',
      icon: <Zap size={15} color="#f59e0b" />,
    };
  }
  if (upper.includes('FAN_OUT') || upper.includes('FAN_IN') || upper.includes('DISBURSEMENT')) {
    return {
      label: 'Rapid Fan-Out / Fan-In',
      category: 'FAN_OUT_IN',
      icon: <GitBranch size={15} color="#ec4899" />,
    };
  }
  if (upper.includes('BRIDGE') || upper.includes('CUT_POINT') || upper.includes('BETWEENNESS')) {
    return {
      label: 'Bridge Node / Cut-Point',
      category: 'BRIDGE_NODE',
      icon: <Activity size={15} color="#a855f7" />,
    };
  }
  return {
    label: alertType.replace(/_/g, ' '),
    category: 'OTHER',
    icon: <AlertCircle size={15} color="#94a3b8" />,
  };
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  caseId,
  alerts: propAlerts,
  onFocusEntities,
  onAlertReviewed,
  onClose,
}) => {
  let safeCase: ReturnType<typeof useCase> | null = null;
  try {
    safeCase = useCase();
  } catch {
    // Context not mounted
  }

  let safeSelection: ReturnType<typeof useSelection> | null = null;
  try {
    safeSelection = useSelection();
  } catch {
    // Selection context not mounted
  }

  const activeCaseId = caseId ?? safeCase?.activeCaseId ?? DEMO_ALERTS.case_id;

  // Local state for alerts
  const [alertsList, setAlertsList] = useState<AlertItem[]>(() => propAlerts ?? DEMO_ALERTS.alerts);
  const [loading, setLoading] = useState<boolean>(!propAlerts);

  // Filters state
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Fetch alerts if not provided as props
  useEffect(() => {
    if (propAlerts) {
      setAlertsList(propAlerts);
      setLoading(false);
      return;
    }

    let isMounted = true;
    if (activeCaseId) {
      setLoading(true);
      apiClient
        .getCaseAlerts(activeCaseId)
        .then((res) => {
          if (isMounted) {
            setAlertsList(res.data.alerts as unknown as AlertItem[]);
            setLoading(false);
          }
        })
        .catch(() => {
          if (isMounted) {
            setAlertsList(DEMO_ALERTS.alerts);
            setLoading(false);
          }
        });
    }

    return () => {
      isMounted = false;
    };
  }, [propAlerts, activeCaseId]);

  // Filtered alerts
  const filteredAlerts = useMemo(() => {
    return alertsList.filter((alert) => {
      if (severityFilter !== 'ALL' && alert.severity !== severityFilter) {
        return false;
      }
      if (statusFilter !== 'ALL' && alert.status !== statusFilter) {
        return false;
      }
      return true;
    });
  }, [alertsList, severityFilter, statusFilter]);

  // Action: Focus on Canvas
  const handleFocusOnCanvas = (alert: AlertItem) => {
    const entityList = getContributingEntitiesList(alert);
    const entityIds = entityList.map((e) => e.entity_id);

    if (onFocusEntities) {
      onFocusEntities(entityIds);
    }

    // Reuse SelectionContext to select the first contributing entity without disrupting canvas
    if (entityIds.length > 0 && safeSelection) {
      const firstEntityId = entityIds[0];
      const matchNode = MOCK_GRAPH_NODES.find((n) => n.data.id === firstEntityId);
      if (matchNode) {
        safeSelection.selectNode(matchNode.data);
      }
    }
  };

  // Action: Mark Reviewed
  const handleMarkReviewed = (alertId: string) => {
    setAlertsList((prev) =>
      prev.map((a) => (a.alert_id === alertId ? { ...a, status: 'REVIEWED' } : a))
    );

    if (onAlertReviewed) {
      onAlertReviewed(alertId);
    }
  };

  return (
    <div
      data-testid="alerts-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        backgroundColor: '#090d16',
        color: '#f8fafc',
        overflow: 'hidden',
      }}
    >
      {/* -------------------------------------------------------------------- */}
      {/* HEADER                                                               */}
      {/* -------------------------------------------------------------------- */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 20px',
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#0f172a',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Bell size={20} color="#f59e0b" />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                data-testid="alerts-header-title"
                style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}
              >
                Pattern & Motif Alerts
              </span>
              <span
                data-testid="alerts-count-badge"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '1px 7px',
                  borderRadius: '10px',
                  fontSize: '11px',
                  fontWeight: 700,
                  backgroundColor: 'rgba(245, 158, 11, 0.15)',
                  color: '#fbbf24',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                }}
              >
                {filteredAlerts.length} Alerts
              </span>
            </div>
            <div style={{ fontSize: '11px', color: '#64748b' }}>
              Deterministic Rules Engine Scans for Structural & Temporal Motifs
            </div>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            data-testid="close-alerts-panel-btn"
            aria-label="Close alerts panel"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* FILTER CONTROLS                                                      */}
      {/* -------------------------------------------------------------------- */}
      <div
        data-testid="alerts-filter-bar"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          alignItems: 'center',
          padding: '12px 20px',
          borderBottom: '1px solid #1e293b',
          backgroundColor: 'rgba(15, 23, 42, 0.5)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Filter size={13} color="#64748b" />
          <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>FILTERS:</span>
        </div>

        {/* Severity Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label htmlFor="filter-severity" style={{ fontSize: '11px', color: '#94a3b8' }}>
            Severity:
          </label>
          <select
            id="filter-severity"
            data-testid="filter-severity"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              fontSize: '11px',
              padding: '4px 8px',
              backgroundColor: '#070b14',
              color: '#f8fafc',
              border: '1px solid #1e293b',
              borderRadius: '4px',
            }}
          >
            <option value="ALL">All Severities</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        {/* Status Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label htmlFor="filter-status" style={{ fontSize: '11px', color: '#94a3b8' }}>
            Status:
          </label>
          <select
            id="filter-status"
            data-testid="filter-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              fontSize: '11px',
              padding: '4px 8px',
              backgroundColor: '#070b14',
              color: '#f8fafc',
              border: '1px solid #1e293b',
              borderRadius: '4px',
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="NEW">NEW</option>
            <option value="REVIEWED">REVIEWED</option>
          </select>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* ALERTS LIST                                                          */}
      {/* -------------------------------------------------------------------- */}
      <div
        data-testid="alerts-list-container"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        {loading ? (
          <div style={{ padding: '20px', color: '#94a3b8', fontSize: '12px' }}>
            Loading deterministic pattern alerts...
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div
            data-testid="empty-alerts-message"
            style={{
              padding: '40px 20px',
              textAlign: 'center',
              color: '#64748b',
              fontSize: '13px',
            }}
          >
            No pattern alerts found matching the current filters.
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const motif = getMotifCategory(alert.alert_type);
            const isHigh = alert.severity === 'HIGH';
            const isMedium = alert.severity === 'MEDIUM';

            // Safe temporal handling
            const evidenceCtx = alert.evidence_context as Record<string, unknown> | undefined;
            const isTemporalIncomplete =
              evidenceCtx?.temporal_data_incomplete === true ||
              evidenceCtx?.has_temporal_data === false ||
              (!alert.created_at && !evidenceCtx?.window_hours && !evidenceCtx?.burst_duration_minutes);

            return (
              <div
                key={alert.alert_id}
                data-testid={`alert-card-${alert.alert_id}`}
                style={{
                  backgroundColor: '#0f172a',
                  border: isHigh ? '1px solid rgba(239, 68, 68, 0.4)' : isMedium ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid #1e293b',
                  borderRadius: '8px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  transition: 'border-color 0.15s ease',
                }}
              >
                {/* Alert Card Header */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    flexWrap: 'wrap',
                    gap: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isHigh ? (
                      <AlertTriangle size={18} color="#ef4444" />
                    ) : isMedium ? (
                      <Bell size={18} color="#f59e0b" />
                    ) : (
                      <Info size={18} color="#38bdf8" />
                    )}
                    <div>
                      <div
                        data-testid="alert-motif-type"
                        style={{
                          fontSize: '13px',
                          fontWeight: 600,
                          color: '#f8fafc',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        {motif.icon}
                        <span>{motif.label}</span>
                      </div>
                      <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                        Rule: {alert.rule_id} • ID: {alert.alert_id}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    {/* Severity Badge */}
                    <span
                      data-testid="alert-severity-badge"
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        backgroundColor: isHigh
                          ? 'rgba(239, 68, 68, 0.15)'
                          : isMedium
                          ? 'rgba(245, 158, 11, 0.15)'
                          : 'rgba(56, 189, 248, 0.15)',
                        color: isHigh ? '#f87171' : isMedium ? '#fbbf24' : '#38bdf8',
                        border: isHigh
                          ? '1px solid rgba(239, 68, 68, 0.3)'
                          : isMedium
                          ? '1px solid rgba(245, 158, 11, 0.3)'
                          : '1px solid rgba(56, 189, 248, 0.3)',
                      }}
                    >
                      {alert.severity}
                    </span>

                    {/* Status Badge */}
                    <span
                      data-testid="alert-status-badge"
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 600,
                        backgroundColor: alert.status === 'REVIEWED' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(100, 116, 139, 0.2)',
                        color: alert.status === 'REVIEWED' ? '#34d399' : '#cbd5e1',
                        border: alert.status === 'REVIEWED' ? '1px solid rgba(52, 211, 153, 0.3)' : '1px solid rgba(100, 116, 139, 0.3)',
                      }}
                    >
                      {alert.status}
                    </span>
                  </div>
                </div>

                {/* Description & Context */}
                {alert.description && (
                  <p
                    data-testid="alert-description"
                    style={{
                      margin: 0,
                      fontSize: '12px',
                      color: '#cbd5e1',
                      lineHeight: '1.45',
                    }}
                  >
                    {alert.description}
                  </p>
                )}

                {/* Temporal Data Section */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  {isTemporalIncomplete ? (
                    <span
                      data-testid="insufficient-temporal-badge"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 600,
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        color: '#f87171',
                        border: '1px solid rgba(239, 68, 68, 0.25)',
                      }}
                    >
                      <Clock size={11} />
                      Insufficient Temporal Data
                    </span>
                  ) : (
                    <span
                      data-testid="temporal-info"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px',
                        color: '#94a3b8',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      <Clock size={12} color="#64748b" />
                      {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Temporal window active'}
                    </span>
                  )}

                  {Boolean(evidenceCtx?.window_hours) && (
                    <span style={{ fontSize: '11px', color: '#64748b' }}>
                      Window: {String(evidenceCtx?.window_hours)} hrs
                    </span>
                  )}
                </div>

                {/* Contributing Entities */}
                {(() => {
                  const entities = getContributingEntitiesList(alert);
                  return (
                    <div data-testid="contributing-entities-section" style={{ marginTop: '2px' }}>
                      <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                        Contributing Entities ({entities.length}):
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {entities.map((entity, idx) => (
                          <span
                            key={idx}
                            data-testid={`entity-badge-${entity.entity_id}`}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              backgroundColor: '#070b14',
                              border: '1px solid #1e293b',
                              color: '#e2e8f0',
                            }}
                          >
                            <span style={{ fontWeight: 600 }}>{entity.canonical_name}</span>
                            {entity.role && (
                              <span style={{ fontSize: '9px', color: '#38bdf8', textTransform: 'uppercase' }}>
                                ({entity.role})
                              </span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })()}

                {/* Actions Bar */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '10px',
                    borderTop: '1px solid #1e293b',
                    marginTop: '4px',
                  }}
                >
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Eye size={13} />}
                    onClick={() => handleFocusOnCanvas(alert)}
                    data-testid="focus-canvas-btn"
                  >
                    Focus on Canvas
                  </Button>

                  {alert.status === 'NEW' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<CheckCircle2 size={13} color="#34d399" />}
                      onClick={() => handleMarkReviewed(alert.alert_id)}
                      data-testid="mark-reviewed-btn"
                    >
                      Mark Reviewed
                    </Button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* FOOTER DISCLAIMER                                                    */}
      {/* -------------------------------------------------------------------- */}
      <div
        style={{
          padding: '10px 20px',
          borderTop: '1px solid #1e293b',
          backgroundColor: '#070b14',
          fontSize: '11px',
          color: '#64748b',
          textAlign: 'center',
          flexShrink: 0,
        }}
      >
        Deterministic motif rules flag structural topologies for analyst corroboration. Patterns do not represent legal proof or guilt.
      </div>
    </div>
  );
};
