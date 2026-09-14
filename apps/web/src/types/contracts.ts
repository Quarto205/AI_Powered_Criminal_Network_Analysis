/**
 * SIH26189 — Universal Frontend TypeScript Contracts
 *
 * Canonical Contract Foundation for SIH26189 Criminal Network Analysis System.
 * Strictly adheres to:
 * - 01_SHARED_TYPES.md (Master lifecycle states, document states, relationship evidence states, review states, confidence semantics)
 * - 02_DATABASE_SCHEMA.md (Authoritative relational entities, cases, evidence, audit)
 * - 03_GRAPH_SCHEMA.md (Neo4j projection, nodes, factual edges vs predicted links)
 * - 04_API_SPEC.md (Universal API response envelope, endpoint request/response models)
 * - 05_AI_CONTRACTS.md (Agent boundaries, SNA metrics, motif alerts, GATv2 link prediction, explanation metadata)
 * - 07_AUTH_SECURITY.md (RBAC roles, case isolation boundaries)
 * - 08_UI_DATA_CONTRACT.md (Cytoscape styling, solid vs dashed edges, accessibility, panels)
 * - 09_NAMING_CONVENTIONS.md (Universal UUID-v4, snake_case API payload fields)
 *
 * NON-NEGOTIABLE INVARIANTS:
 * 1. Freeze interfaces, not implementations.
 * 2. Hard separation between source/observed evidence and AI-inferred predictions.
 * 3. Never conflate extraction confidence, entity similarity, relationship confidence, or GATv2 probability.
 * 4. Graph centrality / GATv2 predictions are NEVER presented as guilt or kingpin status.
 * 5. Full provenance chain (document_id, chunk_id, file_name, version_hash, page_number, character_start, character_end).
 */

// ============================================================================
// 1. IDENTIFIERS & BASE PRIMITIVES
// ============================================================================

/** Canonical UUID-v4 string representation */
export type UUID = string;

/** ISO-8601 formatted datetime string (UTC) */
export type ISODateTime = string;

// ============================================================================
// 2. MASTER LIFECYCLE & SYSTEM ENUMS
// ============================================================================

/** Section 1.2: System Master States */
export const MasterStates = {
  UNAUTHENTICATED: 'UNAUTHENTICATED',
  AUTHENTICATED: 'AUTHENTICATED',
  CASE_SELECTED: 'CASE_SELECTED',
  INGESTION: 'INGESTION',
  PROCESSING: 'PROCESSING',
  REVIEW: 'REVIEW',
  GRAPH_READY: 'GRAPH_READY',
  ANALYSIS: 'ANALYSIS',
  INVESTIGATOR_REVIEW: 'INVESTIGATOR_REVIEW',
  REPORTING_AUDIT: 'REPORTING/AUDIT',
} as const;

export type MasterState = (typeof MasterStates)[keyof typeof MasterStates];

/** Section 1.3: Document Lifecycle States */
export const DocumentStates = {
  RECEIVED: 'RECEIVED',
  VALIDATED: 'VALIDATED',
  PROCESSING: 'PROCESSING',
  EXTRACTED: 'EXTRACTED',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED',
  ACCEPTED: 'ACCEPTED',
  REJECTED: 'REJECTED',
  FAILED: 'FAILED',
} as const;

export type DocumentState = (typeof DocumentStates)[keyof typeof DocumentStates];

/** Section 1.4: Relationship Evidence States */
export const RelationshipStates = {
  OBSERVED: 'OBSERVED',
  CORROBORATED: 'CORROBORATED',
  CONFIRMED: 'CONFIRMED',
  REJECTED: 'REJECTED',
  INFERRED: 'INFERRED',
} as const;

export type RelationshipState = (typeof RelationshipStates)[keyof typeof RelationshipStates];

/** Section 1.5: Review States */
export const ReviewStates = {
  NEW: 'NEW',
  REVIEWED: 'REVIEWED',
  CONFIRMED: 'CONFIRMED',
  REJECTED: 'REJECTED',
} as const;

export type ReviewState = (typeof ReviewStates)[keyof typeof ReviewStates];

/** Section 1.5 & 4.2: Review Actions */
export const ReviewActions = {
  CONFIRM: 'CONFIRM',
  REJECT: 'REJECT',
  MERGE: 'MERGE',
} as const;

export type ReviewAction = (typeof ReviewActions)[keyof typeof ReviewActions];

/** Review Target Types */
export const ReviewTargetTypes = {
  ENTITY_RESOLUTION: 'ENTITY_RESOLUTION',
  PREDICTION: 'PREDICTION',
  EXTRACTION: 'EXTRACTION',
  ENTITY: 'ENTITY',
  RELATIONSHIP: 'RELATIONSHIP',
} as const;

export type ReviewTargetType = (typeof ReviewTargetTypes)[keyof typeof ReviewTargetTypes];

/** Section 7.1: RBAC Roles */
export const UserRoles = {
  INVESTIGATOR: 'INVESTIGATOR',
  ANALYST: 'ANALYST',
  SUPERVISOR: 'SUPERVISOR',
} as const;

export type UserRole = (typeof UserRoles)[keyof typeof UserRoles];

/** Section 3.1: Canonical Node Entity Types */
export const EntityTypes = {
  PERSON: 'PERSON',
  PHONE: 'PHONE',
  BANK_ACCOUNT: 'BANK_ACCOUNT',
  VEHICLE: 'VEHICLE',
  ORGANIZATION: 'ORGANIZATION',
  LOCATION: 'LOCATION',
  CASE: 'CASE',
  EVIDENCE: 'EVIDENCE',
  OFFENSE: 'OFFENSE',
} as const;

export type EntityType = (typeof EntityTypes)[keyof typeof EntityTypes];

/** Section 3.2: Canonical Relationship Types */
export const RelationshipTypes = {
  ACCUSED_IN: 'ACCUSED_IN',
  KNOWS: 'KNOWS',
  CONTACTED: 'CONTACTED',
  LOCATED_AT: 'LOCATED_AT',
  OWNS: 'OWNS',
  USED_BY: 'USED_BY',
  COMMUNICATED_WITH: 'COMMUNICATED_WITH',
  PINGED_TOWER: 'PINGED_TOWER',
  TRANSFERRED_TO: 'TRANSFERRED_TO',
  OWNED_BY: 'OWNED_BY',
  REGISTERED_TO: 'REGISTERED_TO',
  SCANNED_AT: 'SCANNED_AT',
  AFFILIATED_WITH: 'AFFILIATED_WITH',
  CONTAINS: 'CONTAINS',
  SUPPORTS: 'SUPPORTS',
  REFUTES: 'REFUTES',
} as const;

export type RelationshipType = (typeof RelationshipTypes)[keyof typeof RelationshipTypes];

// ============================================================================
// 3. API RESPONSE & ERROR ENVELOPES
// ============================================================================

export const ErrorCodes = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  CONFLICT: 'CONFLICT',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
  ERR_INVALID_PAYLOAD: 'ERR_INVALID_PAYLOAD',
} as const;

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/** Canonical API Success Response Envelope (04_API_SPEC.md 4.1 & backend envelope.py) */
export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  error: null;
  request_id?: UUID;
  tracking_id: UUID;
}

/** Canonical API Error Response Envelope (04_API_SPEC.md 4.1 & backend envelope.py) */
export interface ApiErrorResponse {
  success: false;
  data: null;
  error: ApiErrorDetail;
  request_id?: UUID;
  tracking_id: UUID;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

// ============================================================================
// 4. CONFIDENCE, UNCERTAINTY & BELIEF SEMANTICS
// ============================================================================

/**
 * Section 1.6: Explicit Confidence Semantics
 * These forms of uncertainty are NOT interchangeable.
 */
export interface ConfidenceSemantics {
  /** AI extraction model certainty from unstructured text (0.0 - 1.0) */
  extraction_confidence?: number;
  /** Entity matching similarity likelihood (0.0 - 1.0) */
  similarity_score?: number;
  /** Calculated indicator for observed association strength (0.0 - 1.0) */
  relationship_confidence?: number;
  /** GATv2 model-predicted association probability (0.0 - 1.0) */
  model_confidence?: number;
  /** Rules-engine transactional pattern suspicion rating (0.0 - 1.0) */
  anomaly_score?: number;
  /** Multi-signal derived investigative ranking value (0.0 - 1.0) */
  priority_score?: number;
}

/** Section 1.6: Subjective Logic Consensus Tuple (b + d + u = 1.0) */
export interface SubjectiveLogicTuple {
  belief: number;
  disbelief: number;
  uncertainty: number;
}

// ============================================================================
// 5. CASE MANAGEMENT CONTRACTS
// ============================================================================

export interface CaseCreateRequest {
  case_code: string;
  title: string;
  description?: string;
  jurisdiction: string;
}

export interface CaseCreateResponse {
  case_id: UUID;
  case_code: string;
  title: string;
  status: string;
  jurisdiction: string;
  created_at: ISODateTime;
  created_by: UUID;
}

export interface CaseUpdateRequest {
  title?: string;
  description?: string;
  jurisdiction?: string;
  status?: 'ACTIVE' | 'ARCHIVED' | 'CLOSED' | 'PENDING_REVIEW' | string;
}

export interface CaseDetailResponse {
  case_id: UUID;
  case_code: string;
  title: string;
  description?: string | null;
  status: string;
  jurisdiction: string;
  created_by: UUID;
  created_at: ISODateTime;
  document_count: number;
  entity_count: number;
}

export interface CaseListItem {
  case_id: UUID;
  case_code: string;
  title: string;
  status: string;
  jurisdiction: string;
  member_role: UserRole | string;
  created_at: ISODateTime;
}

export interface CaseListResponse {
  cases: CaseListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CaseMemberItem {
  user_id: UUID;
  username: string;
  email: string;
  role_in_case: UserRole | string;
}

export interface CaseMemberAddRequest {
  user_id: UUID;
  role_in_case: UserRole;
}

// ============================================================================
// 6. PROVENANCE & EVIDENCE TRACEABILITY CONTRACTS
// ============================================================================

export interface ProvenanceSpan {
  chunk_id?: UUID | null;
  document_id?: UUID | null;
  file_name?: string | null;
  version_hash?: string | null;
  page_number?: number | null;
  character_start?: number | null;
  character_end?: number | null;
  source_ref: string;
  support_type: 'SUPPORTS' | 'REFUTES' | string;
  snippet?: string | null;
}

export interface EvidenceCitation {
  evidence_id: UUID;
  source_ref: string;
  support_type: 'SUPPORTS' | 'REFUTES' | string;
  snippet?: string | null;
  document_id?: UUID | null;
  file_name?: string | null;
  page_number?: number | null;
}

export interface RelationshipEndpointSummary {
  entity_id: UUID;
  canonical_name: string;
  entity_type: EntityType | string;
}

// ============================================================================
// 7. ENTITY CONTRACTS
// ============================================================================

export interface EntityAliasInfo {
  alias_id: UUID;
  alias_text: string;
  source_ref?: string | null;
}

export interface EntityIdentifierInfo {
  identifier_id: UUID;
  type: string;
  masked_value: string;
  value_policy?: string | null;
}

export interface RiskScoreInfo {
  score_id: UUID;
  score_type: string;
  value: number;
  features_summary?: Record<string, unknown> | null;
}

export interface EntityDetailResponse {
  entity_id: UUID;
  case_id: UUID;
  canonical_name: string;
  entity_type: EntityType | string;
  status: string;
  aliases: EntityAliasInfo[];
  identifiers: EntityIdentifierInfo[];
  risk_score?: RiskScoreInfo | null;
  provenance_spans: ProvenanceSpan[];
  created_at: ISODateTime;
}

export interface EntityListQueryParams {
  type?: string;
  normalized_name?: string;
  limit?: number;
}

// ============================================================================
// 8. GRAPH CONTRACTS (CYTOSCAPE FORMATTING & ANALYTICAL PROJECTION)
// ============================================================================

export interface CytoscapeNodeData {
  id: string;
  label: string;
  entity_type: EntityType | string;
  case_id: string;
  status?: string;
  risk_score?: number | null;
  priority_score?: number | null;
  alias_count?: number;
  masked_identifier?: string;
  properties?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface CytoscapeNode {
  data: CytoscapeNodeData;
  position?: { x: number; y: number };
}

/** Section 3.3: Properties of Factual, Source-Backed Evidence Edges */
export interface FactualEvidenceEdgeProperties {
  relationship_id: UUID;
  status: 'OBSERVED' | 'CORROBORATED' | 'CONFIRMED' | 'REJECTED';
  source_ref_count: number;
  relationship_confidence: number;
  confidence_type?: string;
  belief?: number;
  disbelief?: number;
  uncertainty?: number;
  observed_at?: ISODateTime;
  created_at?: ISODateTime;
  source_system?: string;
  evidence_ids: string[];
}

/** Section 3.3: Properties of AI-Inferred / Predicted Edges */
export interface InferredPredictionEdgeProperties {
  prediction_id: UUID;
  model_run_id: UUID;
  score: number;
  calibration_status: string;
  expiry_status?: string;
  review_status: ReviewState;
  model_name?: string;
  model_version?: string;
  explanation?: string;
}

export interface CytoscapeEdgeData {
  id: string;
  source: string;
  target: string;
  type: RelationshipType | string;
  confidence_score: number;
  is_predicted: boolean;
  provenance_count: number;
  /** Visual accessibility invariant: solid = observed evidence, dashed = predicted */
  style_line: 'solid' | 'dashed';
  factual_evidence?: FactualEvidenceEdgeProperties;
  inference_prediction?: InferredPredictionEdgeProperties;
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
  created_at: ISODateTime;
}

// ============================================================================
// 9. RELATIONSHIP DETAIL & EVIDENCE DRILL-DOWN
// ============================================================================

export interface RelationshipDetailResponse {
  relationship_id: UUID;
  case_id: UUID;
  source_entity: RelationshipEndpointSummary;
  target_entity: RelationshipEndpointSummary;
  type: RelationshipType | string;
  status: RelationshipState | string;
  confidence_score: number;
  is_predicted: boolean;
  style_line: 'solid' | 'dashed';
  evidence_citations: EvidenceCitation[];
  factual_evidence?: FactualEvidenceEdgeProperties;
  inference_prediction?: InferredPredictionEdgeProperties;
  created_at: ISODateTime;
}

export interface DocumentUploadResponse {
  document_id: UUID;
  job_id: UUID;
  status: DocumentState | string;
}

export interface DocumentListItem {
  document_id: UUID;
  case_id: UUID;
  file_type: string;
  file_hash: string;
  status: DocumentState | string;
  created_at: ISODateTime;
}

// ============================================================================
// 10. ENTITY REVIEW QUEUE (AMBIGUOUS RESOLUTION SUPPORT)
// ============================================================================

export interface SourceEntityMention {
  temp_id: string;
  entity_type: EntityType | string;
  extracted_text: string;
  character_start: number;
  character_end: number;
  document_id: UUID;
  chunk_id?: UUID | null;
  file_name?: string | null;
}

export interface CandidateCanonicalEntity {
  canonical_entity_id: UUID;
  canonical_name: string;
  entity_type: EntityType | string;
  existing_identifiers: string[];
  existing_aliases: string[];
}

export interface EntityMatchMetadata {
  similarity_score: number;
  match_algorithm: 'EXACT' | 'JARO_WINKLER' | 'LEVENSHTEIN' | 'COMPOSITE' | string;
  match_reasons: string[];
  threshold_applied: number;
}

export interface EntityReviewItem {
  review_id: UUID;
  case_id: UUID;
  target_type: 'ENTITY_RESOLUTION';
  source_mention: SourceEntityMention;
  candidate_entity: CandidateCanonicalEntity;
  match_metadata: EntityMatchMetadata;
  review_status: ReviewState;
  decision?: ReviewAction | null;
  reviewer_id?: UUID | null;
  reviewer_notes?: string | null;
  provenance: ProvenanceSpan;
  created_at: ISODateTime;
  updated_at?: ISODateTime;
}

export interface EntityReviewQueueResponse {
  reviews: EntityReviewItem[];
  total: number;
  pending_count: number;
}

// ============================================================================
// 11. ANALYSIS, MOTIF ALERTS & EXPLAINABILITY CONTRACTS
// ============================================================================

export const AnalysisPipelines = {
  SNA: 'SNA',
  PATTERN_MOTIFS: 'PATTERN_MOTIFS',
  GAT_LINK_PREDICTION: 'GAT_LINK_PREDICTION',
} as const;

export type AnalysisPipeline = (typeof AnalysisPipelines)[keyof typeof AnalysisPipelines];

export interface AnalysisParameters {
  time_window_days?: number;
  min_confidence_threshold?: number;
}

export interface AnalysisTriggerRequest {
  pipelines: string[];
  parameters?: AnalysisParameters;
}

export interface AnalysisTriggerResponse {
  run_id: UUID;
  case_id: UUID;
  status: string;
  pipelines: string[];
  triggered_at: ISODateTime;
}

export interface AnalysisRunDetailResponse {
  run_id: UUID;
  case_id?: UUID | null;
  model_name: string;
  version: string;
  task_type: string;
  status: string;
  input_snapshot_checksum: string;
  created_at: ISODateTime;
}

/** SNA Centrality & Investigative Priority Score */
export interface ScoreItem {
  score_id: UUID;
  entity_id: UUID;
  canonical_name: string;
  entity_type: string;
  score_type: string;
  value: number;
  features_summary?: {
    degree?: number;
    betweenness?: number;
    pagerank?: number;
    community_id?: number;
    temporal_recency?: number;
    alert_count?: number;
    reasoning?: string;
    [key: string]: unknown;
  } | null;
}

export interface CaseScoresResponse {
  case_id: UUID;
  scores: ScoreItem[];
  total: number;
}

export interface AlertContributingEntity {
  entity_id: UUID;
  canonical_name: string;
  role?: string;
}

/** Deterministic Motif Pattern Alert */
export interface AlertItem {
  alert_id: UUID;
  case_id: UUID;
  alert_type: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  rule_id: string;
  status: 'NEW' | 'REVIEWED' | string;
  contributing_entities: AlertContributingEntity[];
  description?: string;
  created_at?: ISODateTime;
  evidence_context?: Record<string, unknown>;
}

export interface CaseAlertsResponse {
  case_id: UUID;
  alerts: AlertItem[];
  total: number;
}

/** Section 5.4.E: AI Model Explanation Metadata */
export interface AIExplanationMetadata {
  model_name: string;
  model_version: string;
  task_type: string;
  calibration_status: string;
  contributing_features: Record<string, number | string>;
  confidence_semantics: string;
  limitations: string;
  generated_at: ISODateTime;
}

// ============================================================================
// 12. AUDIT, TIMELINE & EXPORT CONTRACTS
// ============================================================================

export interface ReviewRequest {
  target_type: ReviewTargetType | string;
  target_id: UUID;
  action: ReviewAction | string;
  secondary_target_id?: UUID | null;
  reason: string;
}

export interface ReviewResponse {
  review_id: UUID;
  target_type: string;
  target_id: UUID;
  action: string;
  resulting_status: string;
  secondary_target_id?: UUID | null;
  applied_at: ISODateTime;
  reason: string;
}

export interface AuditLogItem {
  audit_id: UUID;
  actor: string;
  action: string;
  target_item?: string | null;
  timestamp: ISODateTime;
  outcome: string;
}

export interface CaseAuditResponse {
  audit_logs: AuditLogItem[];
  total: number;
}

export interface ExportRequest {
  export_format: 'PDF' | 'CSV';
  include_audit_trail: boolean;
}

export interface ExportResponse {
  export_id: UUID;
  download_url: string;
  hash: string;
}

export interface TimelineEventItem {
  event_id: UUID;
  case_id: UUID;
  event_type: 'COMMUNICATION' | 'TRANSACTION' | 'MOVEMENT' | 'DOCUMENT_OBSERVATION';
  timestamp: ISODateTime;
  description: string;
  entities_involved: Array<{
    entity_id: UUID;
    canonical_name: string;
    role: string;
  }>;
  source_ref?: string;
  details?: Record<string, unknown>;
}
