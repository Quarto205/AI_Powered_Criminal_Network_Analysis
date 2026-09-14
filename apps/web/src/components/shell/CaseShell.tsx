/**
 * CaseShell Component
 * Strictly adheres to 08_UI_DATA_CONTRACT.md (Section 8.1).
 * Houses the case header, jurisdiction badges, tab navigation, and active drawers.
 * Evidence UI scope: Overview, Graph, Timeline tabs, EntityDrawer, EvidencePanel, EntityReviewQueue.
 */

import React, { useState, useEffect } from 'react';
import { Network, LayoutDashboard, Clock, MapPin, Hash, Shield } from 'lucide-react';
import { useCase } from '../../context/CaseContext';
import { useSelection } from '../../context/SelectionContext';
import { Badge } from '../common/Badge';
import { LoadingState, AlertBox } from '../common/States';
import { OverviewTab } from '../tabs/OverviewTab';
import { GraphCanvas } from '../tabs/GraphCanvas';
import { GraphToolbar } from '../tabs/GraphToolbar';
import { TimelineTab } from '../tabs/TimelineTab';
import { AuditTab } from '../tabs/AuditTab';
import { EntityDrawer } from '../drawers/EntityDrawer';
import { EvidencePanel } from '../drawers/EvidencePanel';
import { EntityReviewQueue } from '../triage/EntityReviewQueue';
import { apiClient } from '../../api';
import { CytoscapeNode, CytoscapeEdge } from '../../contracts/graph';
import { EntityTypes } from '../../contracts/common';

export const CaseShell: React.FC = () => {
  const { activeCase, loading, error } = useCase();
  const { selectedNode, selectedEdge, activeDrawer, closeDrawer } = useSelection();
  const [activeTab, setActiveTab] = useState<string>('overview');

  // Graph Canvas State
  const [graphNodes, setGraphNodes] = useState<CytoscapeNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<CytoscapeEdge[]>([]);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<Set<string>>(
    new Set(Object.values(EntityTypes))
  );
  const [showPredictedEdges, setShowPredictedEdges] = useState<boolean>(true);
  const [activeLayout, setActiveLayout] = useState<string>('preset');
  const [visibleStats, setVisibleStats] = useState({ visibleNodes: 0, visibleEdges: 0 });

  // Load Graph Data
  const loadGraphData = () => {
    if (!activeCase) return;
    apiClient.getCaseGraph(activeCase.case_id).then((resp) => {
      setGraphNodes(resp.data.nodes);
      setGraphEdges(resp.data.edges);
    });
  };

  useEffect(() => {
    if (activeCase) {
      loadGraphData();
    }
  }, [activeCase]);

  const toggleEntityType = (type: string) => {
    const next = new Set(selectedEntityTypes);
    if (next.has(type)) {
      if (next.size > 1) next.delete(type);
    } else {
      next.add(type);
    }
    setSelectedEntityTypes(next);
  };

  if (loading) {
    return <LoadingState message="Loading case boundaries and analytical models..." />;
  }

  if (error || !activeCase) {
    return (
      <div style={{ padding: '40px' }}>
        <AlertBox
          type="error"
          title="Case Boundary Access Denied"
          message={error ?? 'The requested case does not exist or your credentials lack authorized membership.'}
        />
      </div>
    );
  }

  const TABS = [
    { id: 'overview', label: 'Case Overview', icon: <LayoutDashboard size={15} /> },
    { id: 'graph', label: 'Graph Canvas', icon: <Network size={15} /> },
    { id: 'timeline', label: 'Timeline', icon: <Clock size={15} /> },
    { id: 'audit', label: 'Audit Ledger', icon: <Shield size={15} /> },
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        overflow: 'hidden',
        background: '#090d16',
      }}
    >
      {/* Sub-Header: Active Case Metadata */}
      <div
        style={{
          padding: '12px 24px',
          background: '#0f172a',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px', fontWeight: 600, color: '#f8fafc' }}>
                {activeCase.title}
              </span>
              <Badge variant="default">{activeCase.status}</Badge>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginTop: '4px',
                fontSize: '12px',
                color: '#64748b',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Hash size={13} /> {activeCase.case_code}
              </span>
              <span>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <MapPin size={13} /> {activeCase.jurisdiction}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div
          style={{
            display: 'flex',
            background: '#090d16',
            padding: '3px',
            borderRadius: '6px',
            border: '1px solid #1e293b',
            gap: '2px',
          }}
        >
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  fontSize: '12px',
                  fontWeight: 500,
                  borderRadius: '4px',
                  border: 'none',
                  cursor: 'pointer',
                  background: isActive ? '#1e293b' : 'transparent',
                  color: isActive ? '#38bdf8' : '#94a3b8',
                  transition: 'all 0.15s ease',
                }}
              >
                {tab.icon}
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Workspace Body */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', display: 'flex' }}>
        <div style={{ flex: 1, height: '100%', overflowY: 'auto' }}>
          {activeTab === 'overview' && (
            <OverviewTab caseDetail={activeCase} onNavigateToTab={setActiveTab} />
          )}

          {activeTab === 'graph' && (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <GraphToolbar
                selectedEntityTypes={selectedEntityTypes}
                onToggleEntityType={toggleEntityType}
                showPredictedEdges={showPredictedEdges}
                onTogglePredictedEdges={() => setShowPredictedEdges(!showPredictedEdges)}
                activeLayout={activeLayout}
                onChangeLayout={setActiveLayout}
                visibleStats={visibleStats}
                onRefresh={loadGraphData}
              />
              <div style={{ flex: 1, position: 'relative' }}>
                <GraphCanvas
                  nodes={graphNodes}
                  edges={graphEdges}
                  selectedEntityTypes={selectedEntityTypes}
                  showPredictedEdges={showPredictedEdges}
                  activeLayout={activeLayout}
                  onStatsChange={setVisibleStats}
                />
              </div>
            </div>
          )}

          {activeTab === 'timeline' && <TimelineTab />}
          {activeTab === 'audit' && <AuditTab />}
        </div>

        {/* Slide-out Drawers (Preserves Graph Canvas Context) */}
        {activeDrawer === 'ENTITY' && selectedNode && (
          <EntityDrawer nodeData={selectedNode} />
        )}
        {activeDrawer === 'EVIDENCE' && (
          <EvidencePanel edgeData={selectedEdge} nodeData={selectedNode} />
        )}
        {activeDrawer === 'REVIEW_QUEUE' && (
          <EntityReviewQueue onClose={closeDrawer} />
        )}
      </div>
    </div>
  );
};
