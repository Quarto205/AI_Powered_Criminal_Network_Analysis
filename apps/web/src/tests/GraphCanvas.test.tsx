import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GraphCanvas } from '../components/tabs/GraphCanvas';
import { SelectionProvider } from '../context/SelectionContext';
import { DEMO_GRAPH } from '../fixtures/demoGraph';
import { EntityTypes } from '../contracts/common';

describe('GraphCanvas Component Tests', () => {
  it('renders graph canvas container with accessibility legend', () => {
    render(
      <SelectionProvider>
        <GraphCanvas
          nodes={DEMO_GRAPH.nodes}
          edges={DEMO_GRAPH.edges}
          selectedEntityTypes={new Set(Object.values(EntityTypes))}
          showPredictedEdges={true}
          activeLayout="preset"
        />
      </SelectionProvider>
    );

    expect(screen.getByTestId('cytoscape-container')).toBeInTheDocument();
    expect(screen.getByText(/Observed \/ Factual Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/\[AI INFERRED\] Predicted Association/i)).toBeInTheDocument();
  });

  it('notifies onStatsChange with visible node and edge counts', () => {
    const handleStatsChange = vi.fn();

    render(
      <SelectionProvider>
        <GraphCanvas
          nodes={DEMO_GRAPH.nodes}
          edges={DEMO_GRAPH.edges}
          selectedEntityTypes={new Set(Object.values(EntityTypes))}
          showPredictedEdges={true}
          activeLayout="preset"
          onStatsChange={handleStatsChange}
        />
      </SelectionProvider>
    );

    expect(handleStatsChange).toHaveBeenCalledWith(
      expect.objectContaining({
        visibleNodes: DEMO_GRAPH.nodes.length,
        visibleEdges: DEMO_GRAPH.edges.length,
      })
    );
  });
});
