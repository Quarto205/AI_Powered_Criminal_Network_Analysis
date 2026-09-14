import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GraphToolbar } from './GraphToolbar';
import { filterGraphData } from './graphFilter';
import {
  DEFAULT_FILTER_STATE,
  GraphFilterState,
  ALL_ENTITY_TYPES,
  ALL_RELATIONSHIP_STATUSES
} from '../../types/graph';
import { mockGraphPayload } from '../../mocks/graphMock';

describe('In-Memory Pure Filter Function (graphFilter.ts)', () => {
  it('returns all fixture nodes and edges under DEFAULT_FILTER_STATE', () => {
    const result = filterGraphData(mockGraphPayload, DEFAULT_FILTER_STATE);

    expect(result.nodes).toHaveLength(mockGraphPayload.nodes.length);
    expect(result.edges).toHaveLength(mockGraphPayload.edges.length);
  });

  it('filters out nodes of unselected entity types and strictly removes orphaned edges', () => {
    // Disable 'Phone' entity type
    const filterState: GraphFilterState = {
      ...DEFAULT_FILTER_STATE,
      selectedEntityTypes: ALL_ENTITY_TYPES.filter((t) => t !== 'Phone')
    };

    const result = filterGraphData(mockGraphPayload, filterState);

    // No Phone nodes remain
    const phoneNodes = result.nodes.filter((n) => n.data.entity_type === 'Phone');
    expect(phoneNodes).toHaveLength(0);

    // Endpoint integrity: all remaining edges connect visible nodes
    const validNodeIds = new Set(result.nodes.map((n) => n.data.id));
    for (const edge of result.edges) {
      expect(validNodeIds.has(edge.data.source)).toBe(true);
      expect(validNodeIds.has(edge.data.target)).toBe(true);
    }
  });

  it('filters nodes by search term (case-insensitive & trimmed) and enforces endpoint integrity', () => {
    // Search for 'Person A' (matches 'Person A')
    const filterState: GraphFilterState = {
      ...DEFAULT_FILTER_STATE,
      searchTerm: '  person a   '
    };

    const result = filterGraphData(mockGraphPayload, filterState);

    expect(result.nodes.length).toBeGreaterThan(0);
    for (const node of result.nodes) {
      expect(node.data.label.toLowerCase()).toContain('person a');
    }

    // Only edges between matching nodes remain
    const validNodeIds = new Set(result.nodes.map((n) => n.data.id));
    for (const edge of result.edges) {
      expect(validNodeIds.has(edge.data.source)).toBe(true);
      expect(validNodeIds.has(edge.data.target)).toBe(true);
    }
  });

  it('filters edges by unselected relationship evidence status', () => {
    // Deselect 'CORROBORATED'
    const filterState: GraphFilterState = {
      ...DEFAULT_FILTER_STATE,
      selectedStatuses: ALL_RELATIONSHIP_STATUSES.filter((s) => s !== 'CORROBORATED')
    };

    const result = filterGraphData(mockGraphPayload, filterState);

    const corroboratedEdges = result.edges.filter((e) => e.data.status === 'CORROBORATED');
    expect(corroboratedEdges).toHaveLength(0);
  });

  it('filters out AI-inferred edges when showInferredEdges is false without hiding nodes', () => {
    const filterState: GraphFilterState = {
      ...DEFAULT_FILTER_STATE,
      showInferredEdges: false
    };

    const result = filterGraphData(mockGraphPayload, filterState);

    // Nodes count remains unchanged
    expect(result.nodes).toHaveLength(mockGraphPayload.nodes.length);

    // No edge with is_inferred === true or status === 'INFERRED' remains
    const inferredEdges = result.edges.filter(
      (e) => e.data.is_inferred === true || e.data.status === 'INFERRED'
    );
    expect(inferredEdges).toHaveLength(0);
  });

  it('handles empty results gracefully without throwing when all entity types are disabled', () => {
    const filterState: GraphFilterState = {
      ...DEFAULT_FILTER_STATE,
      selectedEntityTypes: []
    };

    const result = filterGraphData(mockGraphPayload, filterState);

    expect(result.nodes).toEqual([]);
    expect(result.edges).toEqual([]);
  });

  it('preserves rawGraphData immutability and returns a fresh view', () => {
    const rawNodesBefore = JSON.stringify(mockGraphPayload.nodes);
    const rawEdgesBefore = JSON.stringify(mockGraphPayload.edges);

    const filterState: GraphFilterState = {
      ...DEFAULT_FILTER_STATE,
      searchTerm: 'non-existent-xyz-label'
    };

    const result = filterGraphData(mockGraphPayload, filterState);
    expect(result.nodes).toHaveLength(0);

    // Raw payload is completely untouched
    expect(JSON.stringify(mockGraphPayload.nodes)).toBe(rawNodesBefore);
    expect(JSON.stringify(mockGraphPayload.edges)).toBe(rawEdgesBefore);
  });
});

describe('GraphToolbar Component — UI Controls & Accessibility', () => {
  it('renders search input with accessible label and placeholder', () => {
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={vi.fn()}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search nodes in canvas...');
    expect(searchInput).toBeInTheDocument();
    expect(searchInput).toHaveAttribute('type', 'search');
  });

  it('calls onFilterChange when user types in search input', () => {
    const onFilterChange = vi.fn();
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search nodes in canvas...');
    fireEvent.change(searchInput, { target: { value: 'Hawala' } });

    expect(onFilterChange).toHaveBeenCalledTimes(1);
    expect(onFilterChange).toHaveBeenCalledWith({
      ...DEFAULT_FILTER_STATE,
      searchTerm: 'Hawala'
    });
  });

  it('clears search text when clear button is clicked', () => {
    const onFilterChange = vi.fn();
    render(
      <GraphToolbar
        filterState={{ ...DEFAULT_FILTER_STATE, searchTerm: 'Hawala' }}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const clearBtn = screen.getByRole('button', { name: /Clear search text/i });
    fireEvent.click(clearBtn);

    expect(onFilterChange).toHaveBeenCalledWith({
      ...DEFAULT_FILTER_STATE,
      searchTerm: ''
    });
  });

  it('toggles filter popover and displays canonical entity and status options', () => {
    const onFilterChange = vi.fn();
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const filterBtn = screen.getByRole('button', { name: /Filters:/i });
    expect(filterBtn).toHaveAttribute('aria-expanded', 'false');

    // Open popover
    fireEvent.click(filterBtn);
    expect(filterBtn).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('dialog', { name: 'Graph Filter Options' })).toBeInTheDocument();

    // Toggle entity type button (e.g. Person)
    const personBtn = screen.getByRole('button', { name: /^Person:/i });
    expect(personBtn).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(personBtn);

    expect(onFilterChange).toHaveBeenCalledWith({
      ...DEFAULT_FILTER_STATE,
      selectedEntityTypes: ALL_ENTITY_TYPES.filter((t) => t !== 'Person')
    });
  });

  it('toggles relationship evidence status filter', () => {
    const onFilterChange = vi.fn();
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    // Open popover
    const filterBtn = screen.getByRole('button', { name: /Filters:/i });
    fireEvent.click(filterBtn);

    // Toggle status (e.g. INFERRED)
    const inferredBtn = screen.getByRole('button', { name: /^INFERRED:/i });
    expect(inferredBtn).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(inferredBtn);

    expect(onFilterChange).toHaveBeenCalledWith({
      ...DEFAULT_FILTER_STATE,
      selectedStatuses: ALL_RELATIONSHIP_STATUSES.filter((s) => s !== 'INFERRED')
    });
  });

  it('toggles AI Predicted Edges state with accessible aria-pressed attribute', () => {
    const onFilterChange = vi.fn();
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const aiToggleBtn = screen.getByRole('button', { name: /AI Predicted Edges: On/i });
    expect(aiToggleBtn).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(aiToggleBtn);
    expect(onFilterChange).toHaveBeenCalledWith({
      ...DEFAULT_FILTER_STATE,
      showInferredEdges: false
    });
  });

  it('changes Cytoscape layout algorithm selection', () => {
    const onFilterChange = vi.fn();
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const layoutSelect = screen.getByLabelText(/Layout:/i);
    fireEvent.change(layoutSelect, { target: { value: 'grid' } });

    expect(onFilterChange).toHaveBeenCalledWith({
      ...DEFAULT_FILTER_STATE,
      layout: 'grid'
    });
  });

  it('changes hop-depth exploration setting', () => {
    const onFilterChange = vi.fn();
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const hopSelect = screen.getByLabelText(/Hop Depth:/i);
    fireEvent.change(hopSelect, { target: { value: '2' } });

    expect(onFilterChange).toHaveBeenCalledWith({
      ...DEFAULT_FILTER_STATE,
      hopDepth: 2
    });
  });

  it('triggers onResetFilters when Reset Filters button is clicked', () => {
    const onResetFilters = vi.fn();
    render(
      <GraphToolbar
        filterState={{
          searchTerm: 'Custom search',
          selectedEntityTypes: ['Person'],
          selectedStatuses: ['CONFIRMED'],
          showInferredEdges: false,
          hopDepth: 3,
          layout: 'grid'
        }}
        onFilterChange={vi.fn()}
        onResetFilters={onResetFilters}
        onClearSelection={vi.fn()}
        hasSelection={false}
      />
    );

    const resetBtn = screen.getByRole('button', { name: /Reset all filters and layout to default/i });
    fireEvent.click(resetBtn);

    expect(onResetFilters).toHaveBeenCalledTimes(1);
  });

  it('disables Clear Selection button when hasSelection is false and triggers onClearSelection when true', () => {
    const onClearSelection = vi.fn();
    const { rerender } = render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={vi.fn()}
        onResetFilters={vi.fn()}
        onClearSelection={onClearSelection}
        hasSelection={false}
      />
    );

    const clearSelectionBtn = screen.getByRole('button', { name: /Clear active graph element selection/i });
    expect(clearSelectionBtn).toBeDisabled();

    // Re-render with active selection
    rerender(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={vi.fn()}
        onResetFilters={vi.fn()}
        onClearSelection={onClearSelection}
        hasSelection={true}
      />
    );

    expect(clearSelectionBtn).not.toBeDisabled();
    fireEvent.click(clearSelectionBtn);
    expect(onClearSelection).toHaveBeenCalledTimes(1);
  });

  it('displays accurate node and edge count metrics when provided', () => {
    render(
      <GraphToolbar
        filterState={DEFAULT_FILTER_STATE}
        onFilterChange={vi.fn()}
        onResetFilters={vi.fn()}
        onClearSelection={vi.fn()}
        hasSelection={false}
        totalNodesCount={9}
        visibleNodesCount={7}
        totalEdgesCount={12}
        visibleEdgesCount={8}
      />
    );

    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
  });
});
