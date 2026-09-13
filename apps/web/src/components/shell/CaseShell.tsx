import React, { useState, useMemo, useEffect } from 'react';
import { CaseDetails, CaseShellTabId, SystemRole } from '../../types/shell';
import { CaseShellTabs } from './CaseShellTabs';
import { PermissionGate } from './PermissionGate';
import { CaseNotFound } from './CaseNotFound';
import { GraphCanvas } from '../graph/GraphCanvas';
import { GraphToolbar } from '../graph/GraphToolbar';
import { filterGraphData } from '../graph/graphFilter';
import { CaseSearchInput } from '../search/CaseSearchInput';
import { mockGraphPayload } from '../../mocks/graphMock';
import {
  GraphNodeData,
  GraphEdgeData,
  GraphFilterState,
  DEFAULT_FILTER_STATE
} from '../../types/graph';
import { EntitySearchResult } from '../../types/search';
import { TimelineView } from '../timeline/TimelineView';
import { getTimelineForCase } from '../../mocks/timelineMock';
import {
  createDefaultFilterState,
  applyTimelineToGraph,
  filterTimelineEvents
} from '../timeline/timelineUtils';
import { TimelineFilterState, TimelineEvent } from '../../types/timeline';

export interface CaseShellProps {
  caseData: CaseDetails | null;
  currentUserRole: SystemRole;
  onReturnToCases?: () => void;
  notFoundRequestId?: string;
  initialTab?: CaseShellTabId;
  selectedEntityId?: string | null;
}

export const CaseShell: React.FC<CaseShellProps> = ({
  caseData,
  currentUserRole,
  onReturnToCases,
  notFoundRequestId,
  initialTab = 'overview',
  selectedEntityId
}) => {
  const [activeTab, setActiveTab] = useState<CaseShellTabId>(initialTab);
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdgeData | null>(null);
  const [filterState, setFilterState] = useState<GraphFilterState>(DEFAULT_FILTER_STATE);

  // Timeline payload & filter state for active case (Section 18, 23, 35)
  const activeCaseId = caseData?.case_id || '';
  const timelinePayload = useMemo(() => {
    return getTimelineForCase(activeCaseId);
  }, [activeCaseId]);

  const [timelineFilterState, setTimelineFilterState] = useState<TimelineFilterState>(() =>
    createDefaultFilterState(timelinePayload.time_bounds)
  );
  const [selectedTimelineEventId, setSelectedTimelineEventId] = useState<string | null>(null);

  // Reset timeline filter state and selection when active case changes (Section 23)
  useEffect(() => {
    setTimelineFilterState(createDefaultFilterState(timelinePayload.time_bounds));
    setSelectedTimelineEventId(null);
  }, [activeCaseId, timelinePayload.time_bounds]);

  // In-memory filter derivation composed with timeline visibility constraints (Section 19, 20)
  const filteredGraphData = useMemo(() => {
    const byToolbar = filterGraphData(mockGraphPayload, filterState);
    const visibleEvents = filterTimelineEvents(timelinePayload.events, timelineFilterState);
    return applyTimelineToGraph(byToolbar, timelinePayload.events, visibleEvents);
  }, [filterState, timelinePayload.events, timelineFilterState]);

  // Selection preservation: clear selected element if filtered out (Section 26, 27, 75)
  useEffect(() => {
    if (selectedNode) {
      const isStillVisible = filteredGraphData.nodes.some(
        (n) => n.data.id === selectedNode.id
      );
      if (!isStillVisible) {
        setSelectedNode(null);
      }
    }
    if (selectedEdge) {
      const isStillVisible = filteredGraphData.edges.some(
        (e) => e.data.id === selectedEdge.id
      );
      if (!isStillVisible) {
        setSelectedEdge(null);
      }
    }
  }, [filteredGraphData, selectedNode, selectedEdge]);

  const handleResetFilters = () => {
    setFilterState(DEFAULT_FILTER_STATE);
  };

  const handleClearSelection = () => {
    setSelectedNode(null);
    setSelectedEdge(null);
  };

  const handleResetTimelineFilters = () => {
    setTimelineFilterState(createDefaultFilterState(timelinePayload.time_bounds));
  };

  const handleTimelineEventSelect = (event: TimelineEvent) => {
    setSelectedTimelineEventId(event.event_id);
    const targetEntityId = event.source_entity_id || event.target_entity_id;
    if (targetEntityId) {
      const node = mockGraphPayload.nodes.find((n) => n.data.id === targetEntityId);
      if (node) {
        setSelectedNode(node.data);
        setSelectedEdge(null);
      }
    }
  };

  const handleCaseEntitySelect = (entity: EntitySearchResult) => {
    const node = mockGraphPayload.nodes.find((n) => n.data.id === entity.entity_id);
    if (node) {
      setSelectedNode(node.data);
      setSelectedEdge(null);
      setActiveTab('graph');
    }
  };

  // Sync external entity selection (e.g. from GlobalSearchModal)
  useEffect(() => {
    if (selectedEntityId) {
      const node = mockGraphPayload.nodes.find((n) => n.data.id === selectedEntityId);
      if (node) {
        setSelectedNode(node.data);
        setSelectedEdge(null);
        setActiveTab('graph');
      }
    }
  }, [selectedEntityId]);

  if (!caseData) {
    return (
      <CaseNotFound
        onReturnToCases={onReturnToCases}
        requestId={notFoundRequestId}
      />
    );
  }

  return (
    <div className="case-shell-container">
      {/* 23. Case Header */}
      <header className="case-header" aria-label="Case Metadata Header">
        <div className="case-header-primary">
          <div className="case-code-badge" aria-label="Case Reference Code">
            {caseData.case_code}
          </div>
          <div className="case-title-block">
            <h1 className="case-title">{caseData.title}</h1>
            {caseData.description && (
              <p className="case-description">{caseData.description}</p>
            )}
          </div>
        </div>

        <div className="case-header-meta">
          <div className="meta-item">
            <span className="meta-label">Jurisdiction</span>
            <span className="meta-value">{caseData.jurisdiction}</span>
          </div>

          <div className="meta-item">
            <span className="meta-label">Lifecycle State</span>
            <span className="status-badge status-canonical" aria-label={`State: ${caseData.status}`}>
              {caseData.status}
            </span>
          </div>

          <div className="meta-item">
            <span className="meta-label">Case Member Role</span>
            <span className="role-badge role-case" aria-label={`Role in Case: ${caseData.member_role}`}>
              {caseData.member_role}
            </span>
          </div>

          <div className="meta-item">
            <span className="meta-label">Documents</span>
            <span className="meta-count" aria-label={`${caseData.document_count} ingested documents`}>
              {caseData.document_count}
            </span>
          </div>

          <div className="meta-item">
            <span className="meta-label">Entities</span>
            <span className="meta-count" aria-label={`${caseData.entity_count} resolved entities`}>
              {caseData.entity_count}
            </span>
          </div>
        </div>

        {/* Case-Scoped Entity Search Input (Section 42) */}
        <div className="case-header-search">
          <CaseSearchInput
            activeCaseId={caseData.case_id}
            onSelectEntity={handleCaseEntitySelect}
          />
        </div>
      </header>

      {/* 26. Case Tabs Navigation */}
      <CaseShellTabs activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* 28. Tab Content Panels & Boundaries */}
      <main className="case-tab-viewport">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <section
            id="tabpanel-overview"
            role="tabpanel"
            aria-labelledby="tab-overview"
            className="tab-panel"
          >
            <div className="placeholder-panel">
              <div className="placeholder-header">
                <span className="placeholder-badge">STEP 1 COMPLETE</span>
                <h3 className="placeholder-title">Overview Workspace</h3>
              </div>
              <p className="placeholder-text">
                Case-centric intelligence dashboard highlighting document ingestion pipelines, unresolved entity candidate reviews, active pattern alerts, and graph metrics.
              </p>
              <div className="overview-summary-grid">
                <div className="summary-card">
                  <span className="card-label">INGESTED DOCUMENTS</span>
                  <span className="card-number">{caseData.document_count}</span>
                  <span className="card-subtext">Received & parsed</span>
                </div>
                <div className="summary-card">
                  <span className="card-label">RESOLVED ENTITIES</span>
                  <span className="card-number">{caseData.entity_count}</span>
                  <span className="card-subtext">Canonical nodes</span>
                </div>
                <div className="summary-card">
                  <span className="card-label">CASE STATUS</span>
                  <span className="card-status">{caseData.status}</span>
                  <span className="card-subtext">Relational state</span>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Graph Tab (Step 2 Cytoscape.js Viewport + Step 3 GraphToolbar) */}
        {activeTab === 'graph' && (
          <section
            id="tabpanel-graph"
            role="tabpanel"
            aria-labelledby="tab-graph"
            className="tab-panel tab-panel-graph"
          >
            <GraphToolbar
              filterState={filterState}
              onFilterChange={setFilterState}
              onResetFilters={handleResetFilters}
              onClearSelection={handleClearSelection}
              hasSelection={Boolean(selectedNode || selectedEdge)}
              totalNodesCount={mockGraphPayload.nodes.length}
              visibleNodesCount={filteredGraphData.nodes.length}
              totalEdgesCount={mockGraphPayload.edges.length}
              visibleEdgesCount={filteredGraphData.edges.length}
            />

            <GraphCanvas
              graphData={filteredGraphData}
              layoutName={filterState.layout}
              onNodeSelect={(node) => {
                setSelectedNode(node);
                setSelectedEdge(null);
              }}
              onEdgeSelect={(edge) => {
                setSelectedEdge(edge);
                setSelectedNode(null);
              }}
              selectedElementId={selectedNode?.id || selectedEdge?.id}
            />

            {(selectedNode || selectedEdge) && (
              <div className="graph-selected-bar" role="status" aria-label="Selected Graph Element">
                <div className="selected-item-info">
                  {selectedNode && (
                    <>
                      <span className="selected-badge">NODE: {selectedNode.entity_type}</span>
                      <strong>{selectedNode.label}</strong>
                      <span style={{ color: 'var(--text-muted)' }}>Status: {selectedNode.status}</span>
                      {selectedNode.is_pivot && (
                        <span style={{ color: '#fbbf24', fontWeight: 600 }}>(Reference Pivot)</span>
                      )}
                    </>
                  )}
                  {selectedEdge && (
                    <>
                      <span className="selected-badge">EDGE: {selectedEdge.relationship_type}</span>
                      <span>
                        Evidence: <strong>{selectedEdge.status}</strong>{' '}
                        {selectedEdge.is_inferred ? '(Dashed Line)' : '(Solid Line)'}
                      </span>
                      {selectedEdge.confidence !== undefined && (
                        <span style={{ color: 'var(--text-muted)' }}>
                          Confidence: {(selectedEdge.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </>
                  )}
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '2px 8px', fontSize: '11px' }}
                  onClick={handleClearSelection}
                  aria-label="Clear active graph element selection"
                >
                  Clear Selection
                </button>
              </div>
            )}
          </section>
        )}

        {/* Timeline Tab (Step 5 Interactive Timeline & Temporal Scrubber) */}
        {activeTab === 'timeline' && (
          <section
            id="tabpanel-timeline"
            role="tabpanel"
            aria-labelledby="tab-timeline"
            className="tab-panel tab-panel-timeline"
          >
            <TimelineView
              events={timelinePayload.events}
              timeBounds={timelinePayload.time_bounds}
              filterState={timelineFilterState}
              onFilterChange={setTimelineFilterState}
              onResetFilters={handleResetTimelineFilters}
              onSelectEvent={handleTimelineEventSelect}
              selectedEventId={selectedTimelineEventId}
            />
          </section>
        )}

        {/* Entities Tab */}
        {activeTab === 'entities' && (
          <section
            id="tabpanel-entities"
            role="tabpanel"
            aria-labelledby="tab-entities"
            className="tab-panel"
          >
            <div className="placeholder-panel">
              <div className="placeholder-header">
                <span className="placeholder-badge">STEP 4 PLACEHOLDER</span>
                <h3 className="placeholder-title">Entity Catalog & Resolution Staging</h3>
              </div>
              <p className="placeholder-text">
                Canonical registry of resolved persons, phone identifiers, bank accounts, and vehicles with cross-case deduplication candidate matches.
              </p>
            </div>
          </section>
        )}

        {/* Evidence Tab */}
        {activeTab === 'evidence' && (
          <section
            id="tabpanel-evidence"
            role="tabpanel"
            aria-labelledby="tab-evidence"
            className="tab-panel"
          >
            <div className="placeholder-panel">
              <div className="placeholder-header">
                <span className="placeholder-badge">STEP 4 PLACEHOLDER</span>
                <h3 className="placeholder-title">Evidence & Provenance Panel</h3>
              </div>
              <p className="placeholder-text">
                Granular source traceability displaying original FIR/CDR text spans, bounding boxes, OCR confidence scores, and multi-source corroboration chains.
              </p>
            </div>
          </section>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <section
            id="tabpanel-alerts"
            role="tabpanel"
            aria-labelledby="tab-alerts"
            className="tab-panel"
          >
            <div className="placeholder-panel">
              <div className="placeholder-header">
                <span className="placeholder-badge">STEP 5 PLACEHOLDER</span>
                <h3 className="placeholder-title">Pattern Alerts & Motif Detections</h3>
              </div>
              <p className="placeholder-text">
                Automated heuristic rule matches (smurfing, circular transactions, mule account bursts) flagging priority investigative leads.
              </p>
            </div>
          </section>
        )}

        {/* Audit Tab — Restricted to SUPERVISOR */}
        {activeTab === 'audit' && (
          <section
            id="tabpanel-audit"
            role="tabpanel"
            aria-labelledby="tab-audit"
            className="tab-panel"
          >
            <PermissionGate
              currentRole={currentUserRole}
              allowedRoles={['SUPERVISOR']}
              fallback={
                <div className="restricted-banner" role="status" aria-label="Restricted View">
                  <div className="restricted-header">
                    <span className="restricted-tag">[RESTRICTED]</span>
                    <h4 className="restricted-title">Supervisor Authorization Required</h4>
                  </div>
                  <p className="restricted-message">
                    Access to the Case Audit Ledger requires <strong>SUPERVISOR</strong> role permissions. Your current active role is{' '}
                    <strong>{currentUserRole}</strong>.
                  </p>
                  <p className="restricted-note">
                    Audit records contain immutable database logs, export signatures, and human-in-the-loop prediction override records.
                  </p>
                </div>
              }
            >
              <div className="placeholder-panel">
                <div className="placeholder-header">
                  <span className="placeholder-badge-supervisor">SUPERVISOR VIEW</span>
                  <h3 className="placeholder-title">Case Audit & Export Ledger</h3>
                </div>
                <p className="placeholder-text">
                  Immutable append-only access records, review overrides, cryptographic export hashes, and model decision tracking (07_AUTH_SECURITY.md Section 7.2).
                </p>
                <div className="audit-ledger-preview">
                  <div className="audit-entry">
                    <span className="audit-time">2026-08-15 09:30:00 UTC</span>
                    <span className="audit-actor">system_intake</span>
                    <span className="audit-action">CASE_CREATED</span>
                    <span className="audit-detail">Case DL-2026-CR-0192 registered by Special Cell</span>
                  </div>
                  <div className="audit-entry">
                    <span className="audit-time">2026-08-16 11:20:14 UTC</span>
                    <span className="audit-actor">agent_1_nlp</span>
                    <span className="audit-action">DOCUMENTS_INGESTED</span>
                    <span className="audit-detail">14 source documents parsed and canonical entities extracted</span>
                  </div>
                </div>
              </div>
            </PermissionGate>
          </section>
        )}
      </main>
    </div>
  );
};
