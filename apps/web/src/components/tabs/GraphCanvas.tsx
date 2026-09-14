/**
 * Cytoscape.js Graph Canvas Component
 * Strictly adheres to 03_GRAPH_SCHEMA.md, 08_UI_DATA_CONTRACT.md, and 05_AI_CONTRACTS.md.
 * Factual edges = Solid lines. AI-Inferred links = Dashed lines + Non-color indicators.
 */

import React, { useEffect, useRef } from 'react';
import cytoscape, { Core, NodeSingular, EdgeSingular, EventObject } from 'cytoscape';
import { CytoscapeNode, CytoscapeEdge, CytoscapeNodeData, CytoscapeEdgeData } from '../../contracts/graph';
import { useSelection } from '../../context/SelectionContext';

interface GraphCanvasProps {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
  selectedEntityTypes: Set<string>;
  showPredictedEdges: boolean;
  activeLayout: string;
  onStatsChange?: (stats: { visibleNodes: number; visibleEdges: number }) => void;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes,
  edges,
  selectedEntityTypes,
  showPredictedEdges,
  activeLayout,
  onStatsChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const { selectNode, selectEdge } = useSelection();

  useEffect(() => {
    if (!containerRef.current) return;

    // Filter elements based on active toolbar settings
    const filteredNodes = nodes.filter((n) =>
      selectedEntityTypes.has(n.data.entity_type)
    );
    const visibleNodeIds = new Set(filteredNodes.map((n) => n.data.id));

    const filteredEdges = edges.filter((e) => {
      if (!showPredictedEdges && e.data.is_predicted) return false;
      return visibleNodeIds.has(e.data.source) && visibleNodeIds.has(e.data.target);
    });

    onStatsChange?.({
      visibleNodes: filteredNodes.length,
      visibleEdges: filteredEdges.length,
    });

    const elements = [
      ...filteredNodes.map((n) => ({ data: n.data, position: n.position })),
      ...filteredEdges.map((e) => ({ data: e.data })),
    ];

    // Initialize or re-render Cytoscape instance
    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        style: [
          // Default Node Styles
          {
            selector: 'node',
            style: {
              label: 'data(label)',
              color: '#f8fafc',
              'font-size': '11px',
              'font-family': 'Inter, sans-serif',
              'font-weight': 500,
              'text-valign': 'bottom',
              'text-margin-y': 6,
              'background-color': '#475569',
              width: 32,
              height: 32,
              'border-width': 2,
              'border-color': '#64748b',
              'transition-property': 'background-color, border-color, border-width',
              'transition-duration': 150,
            },
          },
          // Entity-Type Specialized Styles
          {
            selector: 'node[entity_type = "PERSON"]',
            style: {
              'background-color': '#4338ca',
              'border-color': '#818cf8',
              shape: 'ellipse',
            },
          },
          {
            selector: 'node[entity_type = "PHONE"]',
            style: {
              'background-color': '#0e7490',
              'border-color': '#22d3ee',
              shape: 'round-rectangle',
            },
          },
          {
            selector: 'node[entity_type = "BANK_ACCOUNT"]',
            style: {
              'background-color': '#065f46',
              'border-color': '#34d399',
              shape: 'round-hexagon',
            },
          },
          {
            selector: 'node[entity_type = "VEHICLE"]',
            style: {
              'background-color': '#92400e',
              'border-color': '#fbbf24',
              shape: 'barrel',
            },
          },
          {
            selector: 'node[entity_type = "ORGANIZATION"]',
            style: {
              'background-color': '#5b21b6',
              'border-color': '#a78bfa',
              shape: 'round-diamond',
            },
          },
          {
            selector: 'node[entity_type = "LOCATION"]',
            style: {
              'background-color': '#9f1239',
              'border-color': '#fb7185',
              shape: 'tag',
            },
          },
          {
            selector: 'node[entity_type = "OFFENSE"]',
            style: {
              'background-color': '#881337',
              'border-color': '#f43f5e',
              shape: 'octagon',
            },
          },
          // Selected Node State
          {
            selector: 'node:selected',
            style: {
              'border-width': 4,
              'border-color': '#38bdf8',
              'underlay-color': '#38bdf8',
              'underlay-padding': 6,
              'underlay-opacity': 0.3,
            },
          },

          // -------------------------------------------------------------
          // Edge Presentation Contract: Observed (Solid) vs Inferred (Dashed)
          // -------------------------------------------------------------
          {
            selector: 'edge',
            style: {
              width: 2,
              'curve-style': 'bezier',
              'target-arrow-shape': 'triangle',
              'arrow-scale': 1.1,
              'font-size': '9px',
              'font-family': 'JetBrains Mono, monospace',
              color: '#94a3b8',
              'text-rotation': 'autorotate',
              'text-margin-y': -8,
              label: 'data(type)',
            },
          },
          // Factual Evidence Edges -> Solid line
          {
            selector: 'edge[style_line = "solid"]',
            style: {
              'line-style': 'solid',
              'line-color': '#64748b',
              'target-arrow-color': '#64748b',
            },
          },
          // AI-Inferred / Predicted Edges -> Dashed line + distinctive dash spacing + non-color indicator
          {
            selector: 'edge[style_line = "dashed"]',
            style: {
              'line-style': 'dashed',
              'line-dash-pattern': [6, 4],
              'line-color': '#f472b6',
              'target-arrow-color': '#f472b6',
              label: 'data(type)',
              'text-background-color': '#1e1b4b',
              'text-background-opacity': 0.8,
              'text-background-padding': '2px',
            },
          },
          // Selected Edge State
          {
            selector: 'edge:selected',
            style: {
              width: 4,
              'line-color': '#38bdf8',
              'target-arrow-color': '#38bdf8',
            },
          },
        ],
        layout: {
          name: activeLayout,
          animate: true,
          animationDuration: 300,
        } as cytoscape.LayoutOptions,
        wheelSensitivity: 0.2,
      });

      // Bind node click -> open EntityDrawer
      cyRef.current.on('tap', 'node', (evt: EventObject) => {
        const node = evt.target as NodeSingular;
        selectNode(node.data() as CytoscapeNodeData);
      });

      // Bind edge click -> open EvidencePanel
      cyRef.current.on('tap', 'edge', (evt: EventObject) => {
        const edge = evt.target as EdgeSingular;
        selectEdge(edge.data() as CytoscapeEdgeData);
      });
    } else {
      // Diff and update Cytoscape elements
      const cy = cyRef.current;
      cy.batch(() => {
        cy.elements().remove();
        cy.add(elements);
      });

      // Run layout
      const layoutInstance = cy.layout({
        name: activeLayout,
        animate: false,
      } as cytoscape.LayoutOptions);
      layoutInstance.run();
    }
  }, [nodes, edges, selectedEntityTypes, showPredictedEdges, activeLayout, selectNode, selectEdge, onStatsChange]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, []);

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        background: '#0a0f1d',
      }}
    >
      <div
        ref={containerRef}
        data-testid="cytoscape-container"
        style={{
          width: '100%',
          height: '100%',
          outline: 'none',
        }}
      />
      {/* Visual Legend for Observed vs Inferred Accessibility */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #1e293b',
          borderRadius: '6px',
          padding: '8px 12px',
          fontSize: '11px',
          display: 'flex',
          gap: '16px',
          color: '#cbd5e1',
          zIndex: 10,
          pointerEvents: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '20px',
              height: '2px',
              backgroundColor: '#94a3b8',
              display: 'inline-block',
            }}
          />
          <span>Observed / Factual Evidence</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '20px',
              height: '2px',
              borderTop: '2px dashed #f472b6',
              display: 'inline-block',
            }}
          />
          <span style={{ color: '#f472b6' }}>[AI INFERRED] Predicted Association</span>
        </div>
      </div>
    </div>
  );
};
