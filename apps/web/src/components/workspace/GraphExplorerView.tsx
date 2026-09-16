import React, { useState, useRef, useMemo } from 'react';
import { EntityDossier, NetworkEdge } from '../../types';
import { Network3DConstellation, NODE_COLOR_MAP } from './Network3DConstellation';

interface GraphExplorerProps {
  entities: EntityDossier[];
  edges: NetworkEdge[];
  onNodeSelect: (node: EntityDossier) => void;
  selectedNodeId: string | null;
}

export const GraphExplorerView: React.FC<GraphExplorerProps> = ({ entities, edges, onNodeSelect, selectedNodeId }) => {
  const [mode, setMode] = useState<'2D' | '3D'>('2D');
  const [layout, setLayout] = useState<'ORGANIC' | 'HIERARCHICAL' | 'RADIAL'>('ORGANIC');
  
  // Custom layout computation
  const positionedNodes = useMemo(() => {
    const nodes = entities.map(e => ({ ...e, x: 0, y: 0, z: 0 }));
    const width = 800;
    const height = 600;
    
    if (layout === 'RADIAL') {
      const centerNode = nodes[0];
      if (centerNode) {
        centerNode.x = 0; centerNode.y = 0;
        const others = nodes.slice(1);
        others.forEach((n, i) => {
          const angle = (i / others.length) * Math.PI * 2;
          const radius = 200 + (i % 2) * 50;
          n.x = Math.cos(angle) * radius;
          n.y = Math.sin(angle) * radius;
          n.z = (Math.random() - 0.5) * 10;
        });
      }
    } else if (layout === 'HIERARCHICAL') {
      const typeGroups: Record<string, typeof nodes> = {};
      nodes.forEach(n => {
        if (!typeGroups[n.type]) typeGroups[n.type] = [];
        typeGroups[n.type].push(n);
      });
      let yOffset = -200;
      Object.values(typeGroups).forEach(group => {
        const xStep = width / (group.length + 1);
        group.forEach((n, i) => {
          n.x = -width/2 + xStep * (i + 1);
          n.y = yOffset;
          n.z = (Math.random() - 0.5) * 5;
        });
        yOffset += 150;
      });
    } else {
      nodes.forEach((n, i) => {
        n.x = (Math.random() - 0.5) * width * 0.8;
        n.y = (Math.random() - 0.5) * height * 0.8;
        n.z = (Math.random() - 0.5) * 20;
      });
      for (let step = 0; step < 50; step++) {
        edges.forEach(e => {
          const s = nodes.find(n => n.id === e.source);
          const t = nodes.find(n => n.id === e.target);
          if (s && t) {
            const dx = t.x - s.x; const dy = t.y - s.y;
            const dist = Math.sqrt(dx*dx + dy*dy) || 1;
            const force = (dist - 150) * 0.05;
            s.x += (dx/dist) * force; s.y += (dy/dist) * force;
            t.x -= (dx/dist) * force; t.y -= (dy/dist) * force;
          }
        });
      }
    }
    
    if (mode === '3D') {
      return nodes.map(n => ({ ...n, x: n.x / 20, y: n.y / 20, z: n.z }));
    }
    return nodes;
  }, [entities, edges, layout, mode]);

  const svgRef = useRef<SVGSVGElement>(null);
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', position: 'relative' }}>
      
      {/* Top Toolbar */}
      <div style={{ position: 'absolute', top: 16, left: 16, right: 16, zIndex: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', gap: '8px', backgroundColor: 'var(--cnas-surface)', padding: '6px', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)', border: '1px solid var(--cnas-border)' }}>
          <button 
            onClick={() => setMode('2D')}
            style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 600, borderRadius: '4px', border: 'none', backgroundColor: mode === '2D' ? 'var(--cnas-navy)' : 'transparent', color: mode === '2D' ? '#fff' : 'var(--cnas-text-secondary)', cursor: 'pointer' }}>
            2D Tactical
          </button>
          <button 
            onClick={() => setMode('3D')}
            style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 600, borderRadius: '4px', border: 'none', backgroundColor: mode === '3D' ? 'var(--cnas-navy)' : 'transparent', color: mode === '3D' ? '#fff' : 'var(--cnas-text-secondary)', cursor: 'pointer' }}>
            3D Cyber
          </button>
        </div>
        
        <div style={{ display: 'flex', gap: '8px', backgroundColor: 'var(--cnas-surface)', padding: '6px', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)', border: '1px solid var(--cnas-border)' }}>
          {(['ORGANIC', 'HIERARCHICAL', 'RADIAL'] as const).map(l => (
            <button 
              key={l}
              onClick={() => setLayout(l)}
              style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 600, borderRadius: '4px', border: 'none', backgroundColor: layout === l ? 'var(--cnas-surface-high)' : 'transparent', color: layout === l ? 'var(--cnas-navy)' : 'var(--cnas-text-secondary)', cursor: 'pointer' }}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Canvas Area */}
      <div style={{ flex: 1, backgroundColor: '#F8FAFC', backgroundImage: 'radial-gradient(rgba(148, 163, 184, 0.3) 1.2px, transparent 1.2px)', backgroundSize: '28px 28px', overflow: 'hidden', position: 'relative' }}>
        {mode === '3D' ? (
          <Network3DConstellation nodes={positionedNodes} edges={edges} onNodeClick={onNodeSelect} />
        ) : (
          <svg ref={svgRef} width="100%" height="100%" viewBox="-500 -400 1000 800" style={{ cursor: 'grab' }}>
            <g>
              {edges.map(edge => {
                const s = positionedNodes.find(n => n.id === edge.source);
                const t = positionedNodes.find(n => n.id === edge.target);
                if (!s || !t) return null;
                const isPredicted = edge.epistemicType === 'AI_INFERRED';
                
                return (
                  <g key={edge.id}>
                    <line 
                      x1={s.x} y1={s.y} x2={t.x} y2={t.y} 
                      stroke={isPredicted ? "#A855F7" : "#cbd5e1"} 
                      strokeWidth={isPredicted ? 2 : 1.5}
                      strokeDasharray={isPredicted ? "4 4" : "none"}
                    />
                    <g transform={`translate(${(s.x + t.x)/2}, ${(s.y + t.y)/2})`}>
                      <rect x="-40" y="-10" width="80" height="20" rx="4" fill={isPredicted ? "#F3E8FF" : "#E0F2FE"} stroke={isPredicted ? "#A855F7" : "#0EA5E9"} strokeWidth="1" />
                      <text x="0" y="4" fontSize="9" fontWeight="600" textAnchor="middle" fill={isPredicted ? "#7E22CE" : "#0369A1"}>
                        {edge.label.substring(0, 15)}...
                      </text>
                    </g>
                  </g>
                );
              })}
              
              {positionedNodes.map(node => {
                const colors = NODE_COLOR_MAP[node.type] || NODE_COLOR_MAP.PERSON;
                const isSelected = selectedNodeId === node.id;
                
                return (
                  <g key={node.id} transform={`translate(${node.x}, ${node.y})`} onClick={() => onNodeSelect(node as any)} style={{ cursor: 'pointer' }}>
                    <circle 
                      r={isSelected ? 24 : 18} 
                      fill={colors.bg} 
                      stroke={isSelected ? "#000" : colors.border} 
                      strokeWidth={isSelected ? 3 : 1.5} 
                    />
                    <text x="0" y="32" fontSize="11" fontWeight="700" textAnchor="middle" fill="#0f172a" style={{ textShadow: '1px 1px 0 #fff, -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff' }}>
                      {node.name}
                    </text>
                    {node.threatLevel === 'CRITICAL' && (
                      <circle cx="12" cy="-12" r="5" fill="#ef4444" stroke="#fff" strokeWidth="1.5" />
                    )}
                  </g>
                );
              })}
            </g>
          </svg>
        )}
      </div>
    </div>
  );
};
