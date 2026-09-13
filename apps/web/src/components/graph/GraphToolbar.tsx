import React, { useState, useRef, useEffect } from 'react';
import {
  GraphFilterState,
  LayoutType,
  EntityType,
  RelationshipStatus,
  ALL_ENTITY_TYPES,
  ALL_RELATIONSHIP_STATUSES
} from '../../types/graph';

export interface GraphToolbarProps {
  filterState: GraphFilterState;
  onFilterChange: (newFilters: GraphFilterState) => void;
  onResetFilters: () => void;
  onClearSelection: () => void;
  hasSelection: boolean;
  totalNodesCount?: number;
  visibleNodesCount?: number;
  totalEdgesCount?: number;
  visibleEdgesCount?: number;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({
  filterState,
  onFilterChange,
  onResetFilters,
  onClearSelection,
  hasSelection,
  totalNodesCount,
  visibleNodesCount,
  totalEdgesCount,
  visibleEdgesCount
}) => {
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState<boolean>(false);
  const popoverRef = useRef<HTMLDivElement | null>(null);
  const filterBtnRef = useRef<HTMLButtonElement | null>(null);

  // Close filter popover on outside click or Escape
  useEffect(() => {
    if (!isFilterPanelOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        filterBtnRef.current &&
        !filterBtnRef.current.contains(e.target as Node)
      ) {
        setIsFilterPanelOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsFilterPanelOpen(false);
        filterBtnRef.current?.focus();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isFilterPanelOpen]);

  // Handlers for granular filter mutations
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filterState,
      searchTerm: e.target.value
    });
  };

  const handleClearSearch = () => {
    onFilterChange({
      ...filterState,
      searchTerm: ''
    });
  };

  const handleToggleEntityType = (type: EntityType) => {
    const isSelected = filterState.selectedEntityTypes.includes(type);
    const newTypes = isSelected
      ? filterState.selectedEntityTypes.filter((t) => t !== type)
      : [...filterState.selectedEntityTypes, type];

    onFilterChange({
      ...filterState,
      selectedEntityTypes: newTypes
    });
  };

  const handleSelectAllEntities = () => {
    onFilterChange({
      ...filterState,
      selectedEntityTypes: [...ALL_ENTITY_TYPES]
    });
  };

  const handleClearAllEntities = () => {
    onFilterChange({
      ...filterState,
      selectedEntityTypes: []
    });
  };

  const handleToggleStatus = (status: RelationshipStatus) => {
    const isSelected = filterState.selectedStatuses.includes(status);
    const newStatuses = isSelected
      ? filterState.selectedStatuses.filter((s) => s !== status)
      : [...filterState.selectedStatuses, status];

    onFilterChange({
      ...filterState,
      selectedStatuses: newStatuses
    });
  };

  const handleSelectAllStatuses = () => {
    onFilterChange({
      ...filterState,
      selectedStatuses: [...ALL_RELATIONSHIP_STATUSES]
    });
  };

  const handleClearAllStatuses = () => {
    onFilterChange({
      ...filterState,
      selectedStatuses: []
    });
  };

  const handleToggleInferredEdges = () => {
    onFilterChange({
      ...filterState,
      showInferredEdges: !filterState.showInferredEdges
    });
  };

  const handleLayoutChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const layout = e.target.value as LayoutType;
    onFilterChange({
      ...filterState,
      layout
    });
  };

  const handleHopDepthChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const hopDepth = parseInt(e.target.value, 10) || 1;
    onFilterChange({
      ...filterState,
      hopDepth
    });
  };

  const activeEntityCount = filterState.selectedEntityTypes.length;
  const totalEntityTypes = ALL_ENTITY_TYPES.length;
  const activeStatusCount = filterState.selectedStatuses.length;
  const totalStatuses = ALL_RELATIONSHIP_STATUSES.length;

  return (
    <div
      className="graph-toolbar"
      role="toolbar"
      aria-label="Graph visualization controls and filters"
    >
      {/* 1. Node Search Input */}
      <div className="graph-toolbar-group graph-search-group">
        <label htmlFor="graph-search-input" className="visually-hidden">
          Search nodes in canvas
        </label>
        <div className="graph-search-box">
          <span className="search-icon" aria-hidden="true">🔍</span>
          <input
            id="graph-search-input"
            type="search"
            className="graph-search-input"
            placeholder="Search nodes in canvas..."
            value={filterState.searchTerm}
            onChange={handleSearchChange}
            aria-label="Search nodes in canvas"
          />
          {filterState.searchTerm && (
            <button
              type="button"
              className="search-clear-btn"
              onClick={handleClearSearch}
              aria-label="Clear search text"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* 2. Filter Panel Trigger Popover */}
      <div className="graph-toolbar-group graph-filter-anchor">
        <button
          ref={filterBtnRef}
          type="button"
          className={`btn btn-toolbar ${isFilterPanelOpen ? 'active' : ''}`}
          onClick={() => setIsFilterPanelOpen((prev) => !prev)}
          aria-expanded={isFilterPanelOpen}
          aria-controls="graph-filter-popover"
          aria-label={`Filters: ${activeEntityCount} of ${totalEntityTypes} entities, ${activeStatusCount} of ${totalStatuses} statuses`}
        >
          <span aria-hidden="true">⚙</span> Filters{' '}
          <span className="filter-count-badge">
            {activeEntityCount}/{totalEntityTypes}
          </span>
        </button>

        {isFilterPanelOpen && (
          <div
            ref={popoverRef}
            id="graph-filter-popover"
            className="graph-filter-popover"
            role="dialog"
            aria-label="Graph Filter Options"
          >
            <div className="filter-popover-header">
              <span className="filter-popover-title">FILTER GRAPH ELEMENTS</span>
              <button
                type="button"
                className="popover-close-btn"
                onClick={() => setIsFilterPanelOpen(false)}
                aria-label="Close filter panel"
              >
                ×
              </button>
            </div>

            {/* Entity Types Section */}
            <div className="filter-section">
              <div className="filter-section-header">
                <span className="filter-section-title">
                  Entity Types ({activeEntityCount}/{totalEntityTypes})
                </span>
                <div className="filter-section-actions">
                  <button
                    type="button"
                    className="filter-link-btn"
                    onClick={handleSelectAllEntities}
                  >
                    Select All
                  </button>
                  <span aria-hidden="true">·</span>
                  <button
                    type="button"
                    className="filter-link-btn"
                    onClick={handleClearAllEntities}
                  >
                    Clear
                  </button>
                </div>
              </div>
              <div className="filter-options-grid">
                {ALL_ENTITY_TYPES.map((type) => {
                  const isSelected = filterState.selectedEntityTypes.includes(type);
                  return (
                    <button
                      key={type}
                      type="button"
                      className={`filter-pill-btn ${isSelected ? 'selected' : 'unselected'}`}
                      onClick={() => handleToggleEntityType(type)}
                      aria-pressed={isSelected}
                      aria-label={`${type}: ${isSelected ? 'Selected' : 'Not selected'}`}
                    >
                      <span className="pill-indicator" aria-hidden="true">
                        {isSelected ? '✓' : '+'}
                      </span>{' '}
                      {type}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Relationship Statuses Section */}
            <div className="filter-section">
              <div className="filter-section-header">
                <span className="filter-section-title">
                  Evidence Statuses ({activeStatusCount}/{totalStatuses})
                </span>
                <div className="filter-section-actions">
                  <button
                    type="button"
                    className="filter-link-btn"
                    onClick={handleSelectAllStatuses}
                  >
                    Select All
                  </button>
                  <span aria-hidden="true">·</span>
                  <button
                    type="button"
                    className="filter-link-btn"
                    onClick={handleClearAllStatuses}
                  >
                    Clear
                  </button>
                </div>
              </div>
              <div className="filter-options-grid">
                {ALL_RELATIONSHIP_STATUSES.map((status) => {
                  const isSelected = filterState.selectedStatuses.includes(status);
                  return (
                    <button
                      key={status}
                      type="button"
                      className={`filter-pill-btn ${isSelected ? 'selected' : 'unselected'}`}
                      onClick={() => handleToggleStatus(status)}
                      aria-pressed={isSelected}
                      aria-label={`${status}: ${isSelected ? 'Selected' : 'Not selected'}`}
                    >
                      <span className="pill-indicator" aria-hidden="true">
                        {isSelected ? '✓' : '+'}
                      </span>{' '}
                      {status}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. AI Predicted Edges Toggle */}
      <div className="graph-toolbar-group">
        <button
          type="button"
          className={`btn btn-toolbar ai-toggle-btn ${filterState.showInferredEdges ? 'active' : ''}`}
          onClick={handleToggleInferredEdges}
          aria-pressed={filterState.showInferredEdges}
          aria-label={`AI Predicted Edges: ${filterState.showInferredEdges ? 'On' : 'Off'}`}
        >
          <span className="ai-dashed-preview" aria-hidden="true">---</span>
          <span>AI Predicted Edges: {filterState.showInferredEdges ? 'On' : 'Off'}</span>
        </button>
      </div>

      {/* 4. Layout Selector */}
      <div className="graph-toolbar-group select-group">
        <label htmlFor="graph-layout-select" className="select-label">
          Layout:
        </label>
        <select
          id="graph-layout-select"
          className="graph-select"
          value={filterState.layout}
          onChange={handleLayoutChange}
          aria-label="Cytoscape layout algorithm"
        >
          <option value="cose">Force Directed (COSE)</option>
          <option value="concentric">Concentric Circles</option>
          <option value="grid">Structured Grid</option>
          <option value="circle">Circular Ring</option>
        </select>
      </div>

      {/* 5. Hop Depth Selector (In-memory UI Exploration State) */}
      <div className="graph-toolbar-group select-group">
        <label htmlFor="graph-hop-select" className="select-label">
          Hop Depth:
        </label>
        <select
          id="graph-hop-select"
          className="graph-select"
          value={filterState.hopDepth}
          onChange={handleHopDepthChange}
          aria-label="Neighborhood exploration hop depth"
        >
          <option value="1">1 Hop</option>
          <option value="2">2 Hops</option>
          <option value="3">3 Hops</option>
        </select>
      </div>

      {/* 6. Selection & Reset Action Buttons */}
      <div className="graph-toolbar-group graph-toolbar-actions">
        <button
          type="button"
          className="btn btn-secondary btn-toolbar-action"
          onClick={onClearSelection}
          disabled={!hasSelection}
          aria-label="Clear active graph element selection"
        >
          Clear Selection
        </button>

        <button
          type="button"
          className="btn btn-secondary btn-toolbar-action"
          onClick={onResetFilters}
          aria-label="Reset all filters and layout to default"
        >
          Reset Filters
        </button>
      </div>

      {/* 7. Compact Element Counter Summary */}
      {visibleNodesCount !== undefined && totalNodesCount !== undefined && (
        <div
          className="graph-toolbar-metrics"
          role="status"
          aria-label={`Graph elements: ${visibleNodesCount} of ${totalNodesCount} nodes, ${visibleEdgesCount ?? 0} of ${totalEdgesCount ?? 0} edges visible`}
        >
          <span className="metric-pill">
            Nodes: <strong>{visibleNodesCount}</strong>/{totalNodesCount}
          </span>
          <span className="metric-pill">
            Edges: <strong>{visibleEdgesCount ?? 0}</strong>/{totalEdgesCount ?? 0}
          </span>
        </div>
      )}
    </div>
  );
};
