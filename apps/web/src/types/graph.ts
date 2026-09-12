/**
 * SIH26189 — Graph Data Contracts
 * Source: docs/contracts/03_GRAPH_SCHEMA.md, 04_API_SPEC.md, 08_UI_DATA_CONTRACT.md
 * 
 * Invariants:
 * 1. Strictly typed Cytoscape.js payload structures.
 * 2. Node & edge IDs must be valid UUID-v4 format.
 * 3. Canonical relationship evidence states strictly enforced.
 * 4. Reuses shared ApiResponse envelope from types/shell.ts.
 */

import { ApiResponse, UUID } from './shell';

/**
 * Canonical analytical graph node categories (03_GRAPH_SCHEMA.md Section 3.1)
 */
export type EntityType =
  | 'Person'
  | 'Phone'
  | 'BankAccount'
  | 'Vehicle'
  | 'Organization'
  | 'Location'
  | 'Case'
  | 'Evidence'
  | 'Offense';

/**
 * 1.4 Relationship Evidence States (01_SHARED_TYPES.md)
 */
export type RelationshipStatus =
  | 'OBSERVED'
  | 'CORROBORATED'
  | 'CONFIRMED'
  | 'REJECTED'
  | 'INFERRED';

/**
 * Graph node payload data
 */
export interface GraphNodeData {
  id: UUID;
  label: string;
  entity_type: EntityType;
  status: string;
  alias_count?: number;
  is_pivot?: boolean;
  masked_identifier?: string;
}

/**
 * Graph edge payload data
 */
export interface GraphEdgeData {
  id: UUID;
  source: UUID;
  target: UUID;
  relationship_type: string;
  status: RelationshipStatus;
  confidence?: number; // Normalized float 0.0 - 1.0
  is_inferred: boolean;
}

/**
 * Cytoscape element containers
 */
export interface CytoscapeNodeElement {
  data: GraphNodeData;
}

export interface CytoscapeEdgeElement {
  data: GraphEdgeData;
}

/**
 * Bounded graph neighborhood payload (GET /api/v1/cases/{case_id}/graph)
 */
export interface GraphDataPayload {
  nodes: CytoscapeNodeElement[];
  edges: CytoscapeEdgeElement[];
}

export type GraphApiResponse = ApiResponse<GraphDataPayload>;
