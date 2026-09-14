/**
 * Canonical API Client Interface for SIH26189.
 * Strictly adheres to 04_API_SPEC.md. No invented endpoints.
 */

import {
  ApiSuccessResponse,
  PaginationParams,
  CaseCreateRequest,
  CaseCreateResponse,
  CaseDetailResponse,
  CaseListResponse,
  CaseGraphResponse,
  GraphQueryParams,
  GraphRebuildResponse,
  EntityDetailResponse,
  RelationshipDetailResponse,
  ProvenanceSpan,
  CaseAlertsResponse,
  CaseScoresResponse,
  ReviewRequest,
  ReviewResponse,
  CaseAuditResponse,
  TimelineEventItem,
  AnalysisTriggerRequest,
  AnalysisTriggerResponse,
  ExportRequest,
  ExportResponse,
} from '../contracts';

export interface IApiClient {
  // Case endpoints
  listCases(params?: PaginationParams): Promise<ApiSuccessResponse<CaseListResponse>>;
  getCase(caseId: string): Promise<ApiSuccessResponse<CaseDetailResponse>>;
  createCase(payload: CaseCreateRequest): Promise<ApiSuccessResponse<CaseCreateResponse>>;

  // Graph endpoints
  getCaseGraph(caseId: string, params?: GraphQueryParams): Promise<ApiSuccessResponse<CaseGraphResponse>>;
  triggerGraphRebuild(caseId: string): Promise<ApiSuccessResponse<GraphRebuildResponse>>;

  // Entity & Relationship detail
  getEntityDetail(caseId: string, entityId: string): Promise<ApiSuccessResponse<EntityDetailResponse>>;
  getRelationshipDetail(caseId: string, relationshipId: string): Promise<ApiSuccessResponse<RelationshipDetailResponse>>;
  getEvidenceDetail(caseId: string, evidenceId: string): Promise<ApiSuccessResponse<ProvenanceSpan>>;

  // Analysis, Scores & Alerts
  triggerAnalysis(caseId: string, payload: AnalysisTriggerRequest): Promise<ApiSuccessResponse<AnalysisTriggerResponse>>;
  getCaseAlerts(caseId: string, params?: { severity?: string; status?: string }): Promise<ApiSuccessResponse<CaseAlertsResponse>>;
  getCaseScores(caseId: string): Promise<ApiSuccessResponse<CaseScoresResponse>>;

  // Human Review & Audit
  submitReview(caseId: string, payload: ReviewRequest): Promise<ApiSuccessResponse<ReviewResponse>>;
  getCaseAudit(caseId: string): Promise<ApiSuccessResponse<CaseAuditResponse>>;
  getTimelineEvents(caseId: string): Promise<ApiSuccessResponse<{ events: TimelineEventItem[]; total: number }>>;

  // Export
  exportReport(caseId: string, payload: ExportRequest): Promise<ApiSuccessResponse<ExportResponse>>;
}
