/**
 * SIH26189 — In-Memory Graph Filter Engine
 * Contract: docs/contracts/08_UI_DATA_CONTRACT.md, 03_GRAPH_SCHEMA.md
 * 
 * Rules:
 * 1. Pure function with ZERO side effects.
 * 2. In-memory only: no API requests, no Cypher, no mutation of raw graph data.
 * 3. Edge endpoint integrity: every visible edge must connect two visible nodes.
 * 4. Deterministic filtering pipeline:
 *    rawGraphData
 *      ↓
 *    node entity-type filter
 *      ↓
 *    node search filter (by label, case-insensitive)
 *      ↓
 *    validNodeIds Set
 *      ↓
 *    edge endpoint integrity check
 *      ↓
 *    edge relationship status filter
 *      ↓
 *    AI inferred edge filter
 *      ↓
 *    filteredGraphData
 */

import { GraphDataPayload, GraphFilterState } from '../../types/graph';

export function filterGraphData(
  graphData: GraphDataPayload,
  filterState: GraphFilterState
): GraphDataPayload {
  if (!graphData || !graphData.nodes) {
    return { nodes: [], edges: [] };
  }

  const normalizedSearch = filterState.searchTerm.trim().toLowerCase();
  const selectedEntitySet = new Set(filterState.selectedEntityTypes);
  const selectedStatusSet = new Set(filterState.selectedStatuses);

  // 1. Filter Nodes by entity type and search term
  const filteredNodes = graphData.nodes.filter((node) => {
    if (!node.data) return false;

    // Entity type check
    if (!selectedEntitySet.has(node.data.entity_type)) {
      return false;
    }

    // Search term check against node label
    if (normalizedSearch.length > 0) {
      const label = (node.data.label || '').toLowerCase();
      if (!label.includes(normalizedSearch)) {
        return false;
      }
    }

    return true;
  });

  // 2. Build Set of valid visible node IDs for strict edge endpoint integrity
  const validNodeIds = new Set<string>(filteredNodes.map((n) => n.data.id));

  // 3. Filter Edges
  const filteredEdges = (graphData.edges || []).filter((edge) => {
    if (!edge.data) return false;

    // Invariant: Edge endpoint integrity (Section 18, 45, 74)
    if (!validNodeIds.has(edge.data.source) || !validNodeIds.has(edge.data.target)) {
      return false;
    }

    // Relationship status check
    if (!selectedStatusSet.has(edge.data.status)) {
      return false;
    }

    // AI Inferred edge visibility check (Section 16, 17)
    if (!filterState.showInferredEdges) {
      if (edge.data.is_inferred === true || edge.data.status === 'INFERRED') {
        return false;
      }
    }

    return true;
  });

  return {
    nodes: filteredNodes,
    edges: filteredEdges
  };
}
