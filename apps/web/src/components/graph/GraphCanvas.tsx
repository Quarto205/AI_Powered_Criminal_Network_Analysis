import React, { useEffect, useRef, useState, useMemo } from 'react';
import cytoscape, { Core, EventObject, StylesheetStyle } from 'cytoscape';
import {
  GraphDataPayload,
  GraphNodeData,
  GraphEdgeData,
  RelationshipStatus,
  EntityType,
  LayoutType
} from '../../types/graph';

export interface GraphCanvasProps {
  graphData: GraphDataPayload;
  onNodeSelect?: (nodeData: GraphNodeData) => void;
  onEdgeSelect?: (edgeData: GraphEdgeData) => void;
  layoutName?: LayoutType;
  selectedElementId?: string | null;
}

/**
 * Pure helper for edge line style determination (08_UI_DATA_CONTRACT.md).
 * Invariant:
 * Source-backed relationships -> SOLID line.
 * AI-inferred relationships -> DASHED line.
 */
export function getEdgeVisualState(
  status: RelationshipStatus,
  isInferred?: boolean
): 'solid' | 'dashed' | 'dotted' {
  if (status === 'REJECTED') {
    return 'dotted';
  }
  if (status === 'INFERRED' || isInferred === true) {
    return 'dashed';
  }
  return 'solid';
}

/**
 * Pure helper to validate graph payload integrity before Cytoscape initialization.
 */
export function validateGraphData(graphData: GraphDataPayload): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  const nodeIds = new Set<string>();

  for (const node of graphData.nodes) {
    if (!node.data || !node.data.id) {
      errors.push('Encountered node without a valid ID.');
      continue;
    }
    if (nodeIds.has(node.data.id)) {
      errors.push(`Duplicate node ID detected: ${node.data.id}`);
    }
    nodeIds.add(node.data.id);
  }

  for (const edge of graphData.edges) {
    if (!edge.data || !edge.data.id) {
      errors.push('Encountered edge without a valid ID.');
      continue;
    }
    if (!nodeIds.has(edge.data.source)) {
      errors.push(
        `Edge ${edge.data.id} source (${edge.data.source}) does not exist in nodes.`
      );
    }
    if (!nodeIds.has(edge.data.target)) {
      errors.push(
        `Edge ${edge.data.id} target (${edge.data.target}) does not exist in nodes.`
      );
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Node category color palette (aligned with apps/web/src/styles/graphStyles.ts)
 */
export const NODE_CATEGORY_COLORS: Record<EntityType, { bg: string; border: string }> = {
  Person: { bg: '#1d4ed8', border: '#60a5fa' },
  Phone: { bg: '#047857', border: '#34d399' },
  BankAccount: { bg: '#b45309', border: '#fbbf24' },
  Vehicle: { bg: '#6d28d9', border: '#a78bfa' },
  Location: { bg: '#be123c', border: '#fb7185' },
  Organization: { bg: '#0891b2', border: '#22d3ee' },
  Case: { bg: '#334155', border: '#94a3b8' },
  Evidence: { bg: '#475569', border: '#cbd5e1' },
  Offense: { bg: '#991b1b', border: '#f87171' }
};

/**
 * Cytoscape stylesheet enforcing canonical visual invariants
 */
export const CYTOSCAPE_CANVAS_STYLES: StylesheetStyle[] = [
  // 1. Base Node Styles
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'color': '#f8fafc',
      'font-size': '11px',
      'font-family': 'Inter, system-ui, sans-serif',
      'text-valign': 'bottom',
      'text-margin-y': 6,
      'background-color': '#1e293b',
      'border-width': 2,
      'border-color': '#475569',
      'width': 44,
      'height': 44,
      'text-background-opacity': 0.85,
      'text-background-color': '#090d16',
      'text-background-padding': '2px',
      'text-background-shape': 'roundrectangle'
    }
  },
  // 2. Entity Categories
  {
    selector: 'node[entity_type = "Person"]',
    style: {
      'background-color': '#1d4ed8',
      'border-color': '#60a5fa'
    }
  },
  {
    selector: 'node[entity_type = "Phone"]',
    style: {
      'background-color': '#047857',
      'border-color': '#34d399'
    }
  },
  {
    selector: 'node[entity_type = "BankAccount"]',
    style: {
      'background-color': '#b45309',
      'border-color': '#fbbf24'
    }
  },
  {
    selector: 'node[entity_type = "Vehicle"]',
    style: {
      'background-color': '#6d28d9',
      'border-color': '#a78bfa'
    }
  },
  {
    selector: 'node[entity_type = "Location"]',
    style: {
      'background-color': '#be123c',
      'border-color': '#fb7185'
    }
  },
  {
    selector: 'node[entity_type = "Organization"]',
    style: {
      'background-color': '#0891b2',
      'border-color': '#22d3ee'
    }
  },
  // 3. Pivot Node Distinct Visual Marker (Section 29)
  {
    selector: 'node[?is_pivot]',
    style: {
      'border-width': 4,
      'border-color': '#f59e0b',
      'width': 52,
      'height': 52,
      'font-weight': 'bold',
      'text-background-color': '#1e3a8a',
      'text-background-opacity': 1
    }
  },
  // 4. Node Selected State (Section 73)
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#ffffff'
    }
  },
  // 5. Base Edge Styles
  {
    selector: 'edge',
    style: {
      'width': 2,
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.2,
      'label': 'data(relationship_type)',
      'font-size': '10px',
      'font-family': 'Inter, system-ui, sans-serif',
      'color': '#94a3b8',
      'text-background-opacity': 0.85,
      'text-background-color': '#090d16',
      'text-background-padding': '3px',
      'text-background-shape': 'roundrectangle'
    }
  },
  // 6. Visual Invariant 1: Source-Backed Evidence (SOLID LINE)
  {
    selector: 'edge[status = "OBSERVED"], edge[status = "CORROBORATED"], edge[status = "CONFIRMED"]',
    style: {
      'line-style': 'solid',
      'line-color': '#64748b',
      'target-arrow-color': '#64748b',
      'width': 2.5
    }
  },
  {
    selector: 'edge[status = "CONFIRMED"]',
    style: {
      'line-color': '#22c55e',
      'target-arrow-color': '#22c55e',
      'width': 3
    }
  },
  // 7. Visual Invariant 2: AI-Inferred Link (DASHED LINE + Redundant Accessibility Indicator)
  {
    selector: 'edge[?is_inferred], edge[status = "INFERRED"]',
    style: {
      'line-style': 'dashed',
      'line-dash-pattern': [6, 4],
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
      'width': 2.5,
      'label': 'data(relationship_type) [INFERRED]'
    }
  },
  // 8. Rejected Evidence State (DOTTED LINE)
  {
    selector: 'edge[status = "REJECTED"]',
    style: {
      'line-style': 'dotted',
      'line-dash-pattern': [2, 3],
      'line-color': '#ef4444',
      'target-arrow-color': '#ef4444',
      'opacity': 0.5,
      'label': 'data(relationship_type) [REJECTED]'
    }
  },
  // 9. Selected Edge State (Preserves Dashed / Solid Semantics)
  {
    selector: 'edge:selected',
    style: {
      'width': 4
    }
  }
];

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  graphData,
  onNodeSelect,
  onEdgeSelect,
  layoutName = 'cose',
  selectedElementId
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  // Stable callback refs to prevent stale closures without forcing Cytoscape recreation
  const onNodeSelectRef = useRef(onNodeSelect);
  const onEdgeSelectRef = useRef(onEdgeSelect);

  useEffect(() => {
    onNodeSelectRef.current = onNodeSelect;
    onEdgeSelectRef.current = onEdgeSelect;
  }, [onNodeSelect, onEdgeSelect]);

  // Validation
  const validation = useMemo(() => validateGraphData(graphData), [graphData]);

  // Cytoscape Mount & Teardown Lifecycle
  const isInitialMountRef = useRef(true);
  const currentLayoutRef = useRef<LayoutType>(layoutName);

  useEffect(() => {
    if (!containerRef.current) return;
    if (!validation.valid) {
      setInitError(`Malformed graph payload: ${validation.errors.join('; ')}`);
      return;
    }
    if (graphData.nodes.length === 0) {
      return;
    }

    try {
      const containerWidth = containerRef.current.clientWidth || 800;
      const containerHeight = containerRef.current.clientHeight || 600;

      // Initialize Cytoscape
      const cy = cytoscape({
        container: containerRef.current,
        elements: [
          ...graphData.nodes.map((n) => ({ data: { ...n.data } })),
          ...graphData.edges.map((e) => ({ data: { ...e.data } }))
        ],
        style: CYTOSCAPE_CANVAS_STYLES,
        layout: {
          name: layoutName,
          animate: false,
          boundingBox: {
            x1: 0,
            y1: 0,
            w: containerWidth,
            h: containerHeight
          }
        } as cytoscape.LayoutOptions,
        minZoom: 0.2,
        maxZoom: 3.0
      });

      // Register Event Listeners
      cy.on('tap', 'node', (evt: EventObject) => {
        const node = evt.target;
        const data = node.data() as GraphNodeData;
        onNodeSelectRef.current?.(data);
      });

      cy.on('tap', 'edge', (evt: EventObject) => {
        const edge = evt.target;
        const data = edge.data() as GraphEdgeData;
        onEdgeSelectRef.current?.(data);
      });

      // ResizeObserver for responsive viewport adjustment
      const resizeObserver = new ResizeObserver(() => {
        if (cyRef.current) {
          cyRef.current.resize();
        }
      });
      resizeObserver.observe(containerRef.current);

      cyRef.current = cy;
      currentLayoutRef.current = layoutName;
      setInitError(null);

      // Teardown
      return () => {
        resizeObserver.disconnect();
        cy.destroy();
        cyRef.current = null;
      };
    } catch (err) {
      setInitError(
        err instanceof Error ? err.message : 'Failed to initialize GraphCanvas viewport.'
      );
    }
  }, [validation.valid, graphData.nodes.length === 0]);

  // Update Cytoscape elements when graphData changes without destroying instance
  useEffect(() => {
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      return;
    }

    const cy = cyRef.current;
    if (!cy || !validation.valid || graphData.nodes.length === 0) return;

    const containerWidth = containerRef.current?.clientWidth || 800;
    const containerHeight = containerRef.current?.clientHeight || 600;

    cy.batch(() => {
      cy.elements().remove();
      cy.add([
        ...graphData.nodes.map((n) => ({ data: { ...n.data } })),
        ...graphData.edges.map((e) => ({ data: { ...e.data } }))
      ]);
    });

    const layout = cy.layout({
      name: layoutName,
      animate: false,
      boundingBox: {
        x1: 0,
        y1: 0,
        w: containerWidth,
        h: containerHeight
      }
    } as cytoscape.LayoutOptions);
    layout.run();

    if (selectedElementId) {
      const target = cy.$(`#${selectedElementId}`);
      if (target.length > 0) {
        target.select();
      }
    }
  }, [graphData]);

  // Change layout algorithm without destroying Cytoscape or reloading data
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !containerRef.current || graphData.nodes.length === 0) return;
    if (currentLayoutRef.current === layoutName) return;

    currentLayoutRef.current = layoutName;
    const containerWidth = containerRef.current.clientWidth || 800;
    const containerHeight = containerRef.current.clientHeight || 600;

    const layout = cy.layout({
      name: layoutName,
      animate: false,
      boundingBox: {
        x1: 0,
        y1: 0,
        w: containerWidth,
        h: containerHeight
      }
    } as cytoscape.LayoutOptions);
    layout.run();

    if (selectedElementId) {
      const target = cy.$(`#${selectedElementId}`);
      if (target.length > 0) {
        target.select();
      }
    }
  }, [layoutName, selectedElementId]);

  // Element Selection Synchronization
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.elements().unselect();
    if (selectedElementId) {
      const target = cy.$(`#${selectedElementId}`);
      if (target.length > 0) {
        target.select();
      }
    }
  }, [selectedElementId]);

  if (initError) {
    return (
      <div className="graph-error-boundary" role="alert">
        <h4 className="graph-error-title">Graph Rendering Unavailable</h4>
        <p className="graph-error-message">{initError}</p>
      </div>
    );
  }

  if (graphData.nodes.length === 0) {
    return (
      <div className="graph-empty-state" role="status">
        <p className="graph-empty-text">No graph relationships available for current pivot.</p>
      </div>
    );
  }

  return (
    <div
      className="graph-canvas-wrapper"
      role="region"
      aria-label="Case relationship graph visualization"
    >
      {/* Cytoscape Mount Target */}
      <div
        ref={containerRef}
        className="graph-cytoscape-container"
        data-testid="cytoscape-container"
      />

      {/* Accessible Graph Legend Overlay (Section 41, 42, 72) */}
      <div className="graph-legend" role="region" aria-label="Graph Visual Legend">
        <div className="legend-title">EVIDENCE CLASSIFICATION</div>

        <div className="legend-item">
          <span className="legend-line legend-line-solid" aria-hidden="true" />
          <span className="legend-text">
            <strong>Solid:</strong> Source-backed Evidence (<code>OBSERVED</code> / <code>CORROBORATED</code> / <code>CONFIRMED</code>)
          </span>
        </div>

        <div className="legend-item">
          <span className="legend-line legend-line-dashed" aria-hidden="true" />
          <span className="legend-text">
            <strong>Dashed:</strong> AI-Inferred Link (<code>INFERRED</code> Link Prediction)
          </span>
        </div>

        <div className="legend-item">
          <span className="legend-node-pivot" aria-hidden="true" />
          <span className="legend-text">
            <strong>Double Border:</strong> Reference Pivot Entity
          </span>
        </div>
      </div>
    </div>
  );
};
