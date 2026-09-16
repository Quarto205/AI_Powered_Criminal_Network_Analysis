import React, { useState, useMemo, useEffect } from 'react';
import { useCase } from '../context/CaseContext';
import { EntityDrawer } from '../components/entities/EntityDrawer';
import { GraphExplorerView } from '../components/workspace/GraphExplorerView';
import { apiClient } from '../services/apiClient';
import { NetworkEdge, EntityDossier } from '../types';
import {
  Search,
  Sparkles,
  RotateCcw,
  SlidersHorizontal,
} from 'lucide-react';

export const GraphView: React.FC = () => {
  const { entities, selectedEntity, setSelectedEntity, isDrawerOpen, setIsDrawerOpen } = useCase();

  const [searchQuery, setSearchQuery] = useState('');
  const [showAiLinks, setShowAiLinks] = useState(true);
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<string>('ALL');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [hopDepth, setHopDepth] = useState<number>(2);
  
  const [graphNodes, setGraphNodes] = useState<EntityDossier[]>([]);
  const [graphEdges, setGraphEdges] = useState<NetworkEdge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { activeCase } = useCase();

  useEffect(() => {
    const fetchGraph = async () => {
      if (!activeCase?.id) return;
      setIsLoading(true);
      try {
        const res = await apiClient.get<any>(`/api/v1/cases/${activeCase.id}/graph?depth=${hopDepth}&limit=500`);
        if (res.success && res.data) {
          // Assume response data contains nodes and edges matching frontend structure
          // Or map them if they are in raw Neo4j/Cytoscape format
          const rawNodes = res.data.nodes || [];
          const rawEdges = res.data.edges || [];
          
          const mappedNodes = rawNodes.map((n: any) => ({
            id: n.data?.id || n.id,
            caseId: activeCase.id,
            name: n.data?.name || n.name || 'Unknown',
            type: n.data?.label || n.label || 'EVENT',
            primaryRole: 'Subject',
            threatLevel: 'MONITORED',
            degreeCentrality: 0.5,
            betweenness: 0.5,
            clusteringCoeff: 0.5,
            isObserved: true,
            biometricVerified: false,
            aliases: [],
            identifiers: {},
            evidenceCount: 0,
            connectionsCount: 0
          }));
          
          const mappedEdges = rawEdges.map((e: any) => ({
            id: e.data?.id || e.id || `edge-${e.source}-${e.target}`,
            source: e.data?.source || e.source,
            target: e.data?.target || e.target,
            label: e.data?.label || e.label || 'CONNECTED_TO',
            epistemicType: 'VERIFIED_OBSERVED',
            confidence: 0.9,
          }));
          
          setGraphNodes(mappedNodes);
          setGraphEdges(mappedEdges);
        }
      } catch (err) {
        console.error("Graph fetch failed:", err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchGraph();
  }, [activeCase?.id, hopDepth]);

  // Filter elements
  const filteredEntities = useMemo(() => {
    // If backend provided graphNodes, use them, otherwise fallback to context entities
    const baseEntities = graphNodes.length > 0 ? graphNodes : entities;
    return baseEntities.filter((ent) => {
      if (selectedTypeFilter !== 'ALL' && ent.type !== selectedTypeFilter) return false;
      if (searchQuery && !ent.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [entities, graphNodes, selectedTypeFilter, searchQuery]);

  const filteredEdges = useMemo(() => {
    const validNodeIds = new Set(filteredEntities.map((n) => n.id));
    return graphEdges.filter((edge) => {
      if (!showAiLinks && edge.epistemicType === 'AI_INFERRED') return false;
      return validNodeIds.has(edge.source) && validNodeIds.has(edge.target);
    });
  }, [filteredEntities, showAiLinks, graphEdges]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: 'calc(100vh - 110px)' }}>
      {/* Top Control Bar */}
      <div
        style={{
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '0.65rem 1rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          boxShadow: 'var(--shadow-xs)',
        }}
      >
        {/* Left: Search & Filter Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: '300px' }}>
          <div
            style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              flex: 1,
              maxWidth: '320px',
            }}
          >
            <Search size={16} color="var(--cnas-text-muted)" style={{ position: 'absolute', left: '10px' }} />
            <input
              type="text"
              placeholder="Find entity or account in graph..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                height: '34px',
                paddingLeft: '32px',
                paddingRight: '12px',
                fontSize: '12px',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'var(--cnas-surface-subtle)',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', fontWeight: 600 }}>Type:</span>
            <select
              value={selectedTypeFilter}
              onChange={(e) => setSelectedTypeFilter(e.target.value)}
              style={{
                height: '34px',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--cnas-navy)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--cnas-surface-subtle)',
                padding: '0 8px',
              }}
            >
              <option value="ALL">All Classes (14)</option>
              <option value="PERSON">Physical Person</option>
              <option value="SHELL_COMPANY">Shell Company</option>
              <option value="BANK_ACCOUNT">Bank Account</option>
              <option value="LOGISTICS_HUB">Logistics Hub</option>
            </select>
          </div>
        </div>

        {/* Right: AI Inference Toggle, Reset View, More Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          {/* AI Predicted Edges Toggle */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              backgroundColor: 'var(--cnas-ai-subtle)',
              border: '1px dashed var(--cnas-ai-border)',
              padding: '0.35rem 0.65rem',
              borderRadius: 'var(--radius-full)',
              cursor: 'pointer',
            }}
            onClick={() => setShowAiLinks((prev) => !prev)}
          >
            <Sparkles size={14} color="var(--cnas-ai-primary)" />
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--cnas-ai-text)' }}>
              AI Links
            </span>
            <input
              type="checkbox"
              checked={showAiLinks}
              onChange={(e) => setShowAiLinks(e.target.checked)}
              style={{ accentColor: 'var(--cnas-ai-primary)', cursor: 'pointer' }}
            />
            <span
              style={{
                fontFamily: 'var(--font-code)',
                fontSize: '10px',
                fontWeight: 700,
                backgroundColor: '#ffffff',
                padding: '1px 4px',
                borderRadius: 'var(--radius-xs)',
                color: 'var(--cnas-ai-text)',
              }}
            >
              ≥ 90%
            </span>
          </div>

          <div style={{ height: '20px', width: '1px', backgroundColor: 'var(--cnas-border)' }} />

          {/* Reset Camera */}
          <button
            onClick={() => {}}
            style={{
              width: '34px',
              height: '34px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--cnas-border)',
              backgroundColor: 'var(--cnas-surface)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--cnas-text-secondary)',
            }}
            title="Reset Camera View"
          >
            <RotateCcw size={15} />
          </button>

          {/* Advanced Filter Drawer Trigger */}
          <button
            onClick={() => setShowAdvancedFilters((prev) => !prev)}
            style={{
              height: '34px',
              padding: '0 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--cnas-border)',
              backgroundColor: showAdvancedFilters ? 'var(--cnas-surface-container)' : 'var(--cnas-surface)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--cnas-navy)',
            }}
          >
            <SlidersHorizontal size={14} />
            <span>More Filters</span>
          </button>
        </div>
      </div>

      {/* Collapsible Advanced Filters Bar */}
      {showAdvancedFilters && (
        <div
          style={{
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '0.75rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)' }}>
                Hop Depth:
              </span>
              <input
                type="range"
                min={1}
                max={4}
                value={hopDepth}
                onChange={(e) => setHopDepth(Number(e.target.value))}
                style={{ accentColor: 'var(--cnas-blue)', cursor: 'pointer', width: '100px' }}
              />
              <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                {hopDepth} Hops
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)' }}>
                Temporal Span:
              </span>
              <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', color: 'var(--cnas-navy)', backgroundColor: 'var(--cnas-surface-subtle)', padding: '2px 8px', borderRadius: 'var(--radius-xs)' }}>
                18 May 2026 → Present
              </span>
            </div>
          </div>

          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedTypeFilter('ALL');
              setShowAiLinks(true);
              setHopDepth(2);
            }}
            style={{ fontSize: '11px', color: 'var(--cnas-blue)', fontWeight: 600 }}
          >
            Reset Extra Filters
          </button>
        </div>
      )}

      {/* Main Canvas Area */}
      <div
        style={{
          position: 'relative',
          flex: 1,
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-xs)',
        }}
      >
        <GraphExplorerView 
          entities={filteredEntities} 
          edges={filteredEdges} 
          onNodeSelect={(node) => {
            setSelectedEntity(node);
            setIsDrawerOpen(true);
          }}
          selectedNodeId={selectedEntity?.id || null}
        />

        {/* Docked / Slide-over Entity Drawer */}
        <EntityDrawer />
      </div>
    </div>
  );
};
