/**
 * SIH26189 Canonical Shared Types & Contracts
 * Source: docs/contracts/01_SHARED_TYPES.md & docs/contracts/08_UI_DATA_CONTRACT.md
 * 
 * Freeze interfaces, not internal implementations.
 * No speculative or convenience fields.
 */

// 1.1 Identifiers
export type UUID = string; // Standard UUID-v4 format

// 1.2 System Master States
export type SystemMasterState =
  | 'UNAUTHENTICATED'
  | 'AUTHENTICATED'
  | 'CASE_SELECTED'
  | 'INGESTION'
  | 'PROCESSING'
  | 'REVIEW'
  | 'GRAPH_READY'
  | 'ANALYSIS'
  | 'INVESTIGATOR_REVIEW'
  | 'REPORTING/AUDIT';

// 1.3 Document Lifecycle States
export type DocumentLifecycleState =
  | 'RECEIVED'
  | 'VALIDATED'
  | 'PROCESSING'
  | 'EXTRACTED'
  | 'REVIEW_REQUIRED'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'FAILED';

// 1.4 Relationship Evidence States
export type RelationshipEvidenceState =
  | 'OBSERVED'      // Explicitly found in raw, unprocessed source files
  | 'CORROBORATED'  // Confirmed by multiple independent source files or data categories
  | 'CONFIRMED'     // Manually verified and locked by an investigator
  | 'REJECTED'      // Flagged as false or untrustworthy by an investigator
  | 'INFERRED';     // Machine-learning generated (GATv2 or heuristic link prediction)

// 1.5 Review States
export type ReviewState =
  | 'NEW'
  | 'REVIEWED'
  | 'CONFIRMED'
  | 'REJECTED';

// 1.6 Confidence & Belief Semantics
export interface ConfidenceMetrics {
  extractionConfidence?: number;   // Float 0.0 - 1.0 (NLP model certainty)
  entityMatchConfidence?: number;  // Float 0.0 - 1.0 (Resolution similarity)
  relationshipConfidence?: number; // Calculated strength indicator
  modelConfidence?: number;        // Float 0.0 - 1.0 (GATv2 link prediction)
  anomalyScore?: number;           // Transaction pattern rating
  investigationPriority?: number;  // Derived multi-signal ranking value
  subjectiveLogic?: {
    b: number; // Belief
    d: number; // Disbelief
    u: number; // Uncertainty
    a?: number; // Base rate
  };
}

// 3.1 Graph Node Categories (Neo4j Analytical Projection)
export type NodeCategory =
  | 'Person'
  | 'Phone'
  | 'BankAccount'
  | 'Vehicle'
  | 'Organization'
  | 'Location'
  | 'Case'
  | 'Evidence'
  | 'Offense';

// 4.1 Canonical API Envelope
export interface APIResponseEnvelope<T> {
  success: boolean;
  data: T | null;
  error: APIErrorDetails | null;
  request_id: string;
}

export interface APIErrorDetails {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

// 8.2 Graph Canvas & Cytoscape Data Contracts
export interface GraphNodeData {
  id: UUID;
  label: string;
  category: NodeCategory;
  caseId: UUID;
  statusBadge?: string;
  isConfirmed?: boolean;
  provenanceDocumentId?: UUID;
  metadata?: Record<string, unknown>;
}

export interface GraphEdgeData {
  id: UUID;
  source: UUID;
  target: UUID;
  type: string;
  caseId: UUID;
  evidenceState: RelationshipEvidenceState;
  confidence?: ConfidenceMetrics;
  provenanceDocumentId?: UUID;
  sourceExcerpt?: string;
}

export interface CytoscapeNodeElement {
  data: GraphNodeData;
}

export interface CytoscapeEdgeElement {
  data: GraphEdgeData;
}

export interface CaseSummary {
  caseId: UUID;
  caseCode: string;
  title: string;
  jurisdiction: string;
  state: SystemMasterState;
  nodeCount: number;
  edgeCount: number;
  createdAt: string;
  updatedAt: string;
}
