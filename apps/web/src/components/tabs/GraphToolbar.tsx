import React from 'react';
import { Layers, Eye, EyeOff, Sparkles, RefreshCw } from 'lucide-react';
import { EntityTypes } from '../../contracts/common';

interface GraphToolbarProps {
  selectedEntityTypes: Set<string>;
  onToggleEntityType: (type: string) => void;
  showPredictedEdges: boolean;
  onTogglePredictedEdges: () => void;
  activeLayout: string;
  onChangeLayout: (layout: string) => void;
  visibleStats: { visibleNodes: number; visibleEdges: number };
  onRefresh?: () => void;
}

const ALL_ENTITY_TYPES = [
  { key: EntityTypes.PERSON, label: 'Person', color: '#818cf8' },
  { key: EntityTypes.PHONE, label: 'Phone', color: '#22d3ee' },
  { key: EntityTypes.BANK_ACCOUNT, label: 'Bank', color: '#34d399' },
  { key: EntityTypes.VEHICLE, label: 'Vehicle', color: '#fbbf24' },
  { key: EntityTypes.ORGANIZATION, label: 'Org', color: '#a78bfa' },
  { key: EntityTypes.LOCATION, label: 'Location', color: '#fb7185' },
  { key: EntityTypes.OFFENSE, label: 'Offense', color: '#f43f5e' },
];

const LAYOUTS = [
  { id: 'preset', name: 'Investigator Map' },
  { id: 'cose', name: 'Force-Directed' },
  { id: 'concentric', name: 'Concentric' },
  { id: 'breadthfirst', name: 'Hierarchical' },
  { id: 'grid', name: 'Grid' },
];

export const GraphToolbar: React.FC<GraphToolbarProps> = ({
  selectedEntityTypes,
  onToggleEntityType,
  showPredictedEdges,
  onTogglePredictedEdges,
  activeLayout,
  onChangeLayout,
  visibleStats,
  onRefresh,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        padding: '10px 16px',
        background: '#0d1322',
        borderBottom: '1px solid #1e293b',
        fontSize: '12px',
      }}
    >
      {/* Entity Filters */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ color: '#64748b', fontWeight: 600, textTransform: 'uppercase', fontSize: '10px', letterSpacing: '0.05em' }}>
          Filters:
        </span>
        {ALL_ENTITY_TYPES.map((t) => {
          const active = selectedEntityTypes.has(t.key);
          return (
            <button
              key={t.key}
              onClick={() => onToggleEntityType(t.key)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '3px 8px',
                borderRadius: '4px',
                border: active ? `1px solid ${t.color}` : '1px solid #334155',
                background: active ? 'rgba(30, 41, 59, 0.9)' : 'transparent',
                color: active ? '#f8fafc' : '#64748b',
                cursor: 'pointer',
                fontSize: '11px',
                transition: 'all 0.1s ease',
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: active ? t.color : '#475569',
                }}
              />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Toggles and Layout Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Toggle AI Inferred Edges */}
        <button
          onClick={onTogglePredictedEdges}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '4px',
            border: showPredictedEdges ? '1px dashed #f472b6' : '1px solid #334155',
            background: showPredictedEdges ? 'rgba(80, 7, 36, 0.4)' : 'transparent',
            color: showPredictedEdges ? '#f472b6' : '#64748b',
            cursor: 'pointer',
            fontSize: '11px',
            fontWeight: 500,
          }}
          title="Toggle visibility of machine-learning predicted association edges"
        >
          <Sparkles size={13} />
          <span>AI Predicted Links</span>
          {showPredictedEdges ? <Eye size={12} /> : <EyeOff size={12} />}
        </button>

        {/* Layout Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Layers size={13} color="#94a3b8" />
          <select
            value={activeLayout}
            onChange={(e) => onChangeLayout(e.target.value)}
            style={{
              padding: '4px 8px',
              borderRadius: '4px',
              background: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #334155',
              fontSize: '11px',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {LAYOUTS.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </div>

        {/* Refresh button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            title="Reload graph layout"
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '4px 8px',
              borderRadius: '4px',
              background: '#1e293b',
              color: '#94a3b8',
              border: '1px solid #334155',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={12} />
          </button>
        )}

        {/* Topology Stats */}
        <div style={{ color: '#94a3b8', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          Visible Nodes: <strong style={{ color: '#f8fafc' }}>{visibleStats.visibleNodes}</strong> | Visible Edges:{' '}
          <strong style={{ color: '#f8fafc' }}>{visibleStats.visibleEdges}</strong>
        </div>
      </div>
    </div>
  );
};
