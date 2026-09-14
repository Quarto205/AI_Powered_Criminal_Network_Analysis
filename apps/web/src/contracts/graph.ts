/**
 * Canonical Graph API Schemas for SIH26189.
 * Strictly adheres to 03_GRAPH_SCHEMA.md, 04_API_SPEC.md, 08_UI_DATA_CONTRACT.md,
 * and main/backend/schemas/graph.py.
 */

import { UUID, EntityType, RelationshipType } from './common';

export interface CytoscapeNodeData {
  id: string;
  label: string;
  entity_type: EntityType | string;
  case_id: string;
  status?: string;
  risk_score?: number | null;
  [key: string]: unknown;
}

export interface CytoscapeNode {
  data: CytoscapeNodeData;
  position?: { x: number; y: number };
}

export interface CytoscapeEdgeData {
  id: string;
  source: string;
  target: string;
  type: RelationshipType | string;
  confidence_score: number;
  is_predicted: boolean;
  provenance_count: number;
  style_line: 'solid' | 'dashed';
  [key: string]: unknown;
}

export interface CytoscapeEdge {
  data: CytoscapeEdgeData;
}

export interface GraphStats {
  node_count: number;
  edge_count: number;
  predicted_edge_count: number;
}

export interface CaseGraphResponse {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
  stats: GraphStats;
}

export interface GraphQueryParams {
  pivot_entity_id?: UUID;
  hop_depth?: number;
  filters?: string;
}

export interface GraphRebuildResponse {
  case_id: UUID;
  job_id: UUID;
  status: string;
  created_at: string;
}
