import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  GraphCanvas,
  getEdgeVisualState,
  validateGraphData
} from './GraphCanvas';
import { mockGraphPayload, PIVOT_NODE_ID } from '../../mocks/graphMock';
import { GraphDataPayload } from '../../types/graph';

describe('GraphCanvas Component — Step 2 Viewport', () => {
  it('mounts and renders cytoscape container and accessible visual legend', () => {
    render(<GraphCanvas graphData={mockGraphPayload} />);

    expect(screen.getByTestId('cytoscape-container')).toBeInTheDocument();
    expect(screen.getByText('EVIDENCE CLASSIFICATION')).toBeInTheDocument();
    expect(screen.getByText(/Source-backed Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/AI-Inferred Link/i)).toBeInTheDocument();
    expect(screen.getByText(/Reference Pivot Entity/i)).toBeInTheDocument();
  });

  it('renders neutral empty state when nodes array is empty', () => {
    const emptyPayload: GraphDataPayload = { nodes: [], edges: [] };
    render(<GraphCanvas graphData={emptyPayload} />);

    expect(
      screen.getByText('No graph relationships available for current pivot.')
    ).toBeInTheDocument();
  });

  it('renders contained error boundary when malformed graph data is supplied', () => {
    const malformedPayload: GraphDataPayload = {
      nodes: [
        {
          data: {
            id: 'valid-node-1',
            label: 'Node 1',
            entity_type: 'Person',
            status: 'ACTIVE'
          }
        }
      ],
      edges: [
        {
          data: {
            id: 'bad-edge-1',
            source: 'valid-node-1',
            target: 'non-existent-node-2',
            relationship_type: 'CONTACTED',
            status: 'OBSERVED',
            is_inferred: false
          }
        }
      ]
    };

    render(<GraphCanvas graphData={malformedPayload} />);
    expect(screen.getByText('Graph Rendering Unavailable')).toBeInTheDocument();
    expect(screen.getByText(/does not exist in nodes/i)).toBeInTheDocument();
  });

  it('unmounts cleanly without throwing or leaking instances', () => {
    const { unmount } = render(<GraphCanvas graphData={mockGraphPayload} />);
    expect(() => unmount()).not.toThrow();
  });
});

describe('Graph Visual Invariants & Semantic Edge Mapping', () => {
  it('maps factual evidence states (OBSERVED, CORROBORATED, CONFIRMED) strictly to SOLID lines', () => {
    expect(getEdgeVisualState('OBSERVED', false)).toBe('solid');
    expect(getEdgeVisualState('CORROBORATED', false)).toBe('solid');
    expect(getEdgeVisualState('CONFIRMED', false)).toBe('solid');
  });

  it('maps machine-predicted links (INFERRED / is_inferred) strictly to DASHED lines', () => {
    expect(getEdgeVisualState('INFERRED', true)).toBe('dashed');
    expect(getEdgeVisualState('INFERRED', false)).toBe('dashed');
    expect(getEdgeVisualState('CORROBORATED', true)).toBe('dashed'); // Defensive: any inferred flag forces dashed
  });

  it('maps investigator-rejected relationships to DOTTED lines', () => {
    expect(getEdgeVisualState('REJECTED', false)).toBe('dotted');
  });
});

describe('Graph Data Integrity & Pre-render Validation', () => {
  it('validates deterministic mock graph payload as 100% compliant', () => {
    const result = validateGraphData(mockGraphPayload);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('detects duplicate node identifiers', () => {
    const duplicatePayload: GraphDataPayload = {
      nodes: [
        {
          data: {
            id: PIVOT_NODE_ID,
            label: 'Node 1',
            entity_type: 'Person',
            status: 'ACTIVE'
          }
        },
        {
          data: {
            id: PIVOT_NODE_ID,
            label: 'Duplicate Node',
            entity_type: 'Person',
            status: 'ACTIVE'
          }
        }
      ],
      edges: []
    };

    const result = validateGraphData(duplicatePayload);
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain('Duplicate node ID');
  });

  it('detects edges pointing to missing source or target nodes', () => {
    const orphanedEdgePayload: GraphDataPayload = {
      nodes: [
        {
          data: {
            id: 'node-a',
            label: 'Node A',
            entity_type: 'Person',
            status: 'ACTIVE'
          }
        }
      ],
      edges: [
        {
          data: {
            id: 'edge-ab',
            source: 'node-a',
            target: 'missing-node-b',
            relationship_type: 'KNOWS',
            status: 'OBSERVED',
            is_inferred: false
          }
        }
      ]
    };

    const result = validateGraphData(orphanedEdgePayload);
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain('does not exist in nodes');
  });
});

describe('Selection & Callback Safety', () => {
  it('accepts stable callbacks without triggering errors on rerender', () => {
    const onNodeSelect = vi.fn();
    const onEdgeSelect = vi.fn();

    const { rerender } = render(
      <GraphCanvas
        graphData={mockGraphPayload}
        onNodeSelect={onNodeSelect}
        onEdgeSelect={onEdgeSelect}
      />
    );

    // Changing callback reference does not crash or recreate instance
    const newOnNodeSelect = vi.fn();
    rerender(
      <GraphCanvas
        graphData={mockGraphPayload}
        onNodeSelect={newOnNodeSelect}
        onEdgeSelect={onEdgeSelect}
      />
    );

    expect(screen.getByTestId('cytoscape-container')).toBeInTheDocument();
  });
});
