/**
 * Real HTTP API Client implementing IApiClient.
 * Communicates with backend endpoints defined in 04_API_SPEC.md.
 */

import { IApiClient } from './clientInterface';
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

export class RealApiClient implements IApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = (import.meta.env?.VITE_API_BASE_URL as string) || '/api/v1') {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiSuccessResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const body = await response.json();

    if (!response.ok || !body.success) {
      const errorMsg = body?.error?.message || `HTTP error ${response.status}`;
      throw new Error(errorMsg);
    }

    return body as ApiSuccessResponse<T>;
  }

  async listCases(params?: PaginationParams): Promise<ApiSuccessResponse<CaseListResponse>> {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request<CaseListResponse>(`/cases${qs}`);
  }

  async getCase(caseId: string): Promise<ApiSuccessResponse<CaseDetailResponse>> {
    return this.request<CaseDetailResponse>(`/cases/${caseId}`);
  }

  async createCase(payload: CaseCreateRequest): Promise<ApiSuccessResponse<CaseCreateResponse>> {
    return this.request<CaseCreateResponse>('/cases', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getCaseGraph(caseId: string, params?: GraphQueryParams): Promise<ApiSuccessResponse<CaseGraphResponse>> {
    const query = new URLSearchParams();
    if (params?.pivot_entity_id) query.set('pivot_entity_id', params.pivot_entity_id);
    if (params?.hop_depth) query.set('hop_depth', params.hop_depth.toString());
    if (params?.filters) query.set('filters', params.filters);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request<CaseGraphResponse>(`/cases/${caseId}/graph${qs}`);
  }

  async triggerGraphRebuild(caseId: string): Promise<ApiSuccessResponse<GraphRebuildResponse>> {
    return this.request<GraphRebuildResponse>(`/cases/${caseId}/graph/rebuild`, {
      method: 'POST',
    });
  }

  async getEntityDetail(caseId: string, entityId: string): Promise<ApiSuccessResponse<EntityDetailResponse>> {
    return this.request<EntityDetailResponse>(`/cases/${caseId}/entities/${entityId}`);
  }

  async getRelationshipDetail(caseId: string, relationshipId: string): Promise<ApiSuccessResponse<RelationshipDetailResponse>> {
    return this.request<RelationshipDetailResponse>(`/cases/${caseId}/relationships/${relationshipId}`);
  }

  async getEvidenceDetail(caseId: string, evidenceId: string): Promise<ApiSuccessResponse<ProvenanceSpan>> {
    return this.request<ProvenanceSpan>(`/cases/${caseId}/evidence/${evidenceId}`);
  }

  async triggerAnalysis(caseId: string, payload: AnalysisTriggerRequest): Promise<ApiSuccessResponse<AnalysisTriggerResponse>> {
    return this.request<AnalysisTriggerResponse>(`/cases/${caseId}/analysis`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getCaseAlerts(caseId: string, params?: { severity?: string; status?: string }): Promise<ApiSuccessResponse<CaseAlertsResponse>> {
    const query = new URLSearchParams();
    if (params?.severity) query.set('severity', params.severity);
    if (params?.status) query.set('status', params.status);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request<CaseAlertsResponse>(`/cases/${caseId}/alerts${qs}`);
  }

  async getCaseScores(caseId: string): Promise<ApiSuccessResponse<CaseScoresResponse>> {
    return this.request<CaseScoresResponse>(`/cases/${caseId}/scores`);
  }

  async submitReview(caseId: string, payload: ReviewRequest): Promise<ApiSuccessResponse<ReviewResponse>> {
    return this.request<ReviewResponse>(`/cases/${caseId}/reviews`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getCaseAudit(caseId: string): Promise<ApiSuccessResponse<CaseAuditResponse>> {
    return this.request<CaseAuditResponse>(`/cases/${caseId}/audit`);
  }

  async getTimelineEvents(caseId: string): Promise<ApiSuccessResponse<{ events: TimelineEventItem[]; total: number }>> {
    return this.request<{ events: TimelineEventItem[]; total: number }>(`/cases/${caseId}/timeline`);
  }

  async exportReport(caseId: string, payload: ExportRequest): Promise<ApiSuccessResponse<ExportResponse>> {
    return this.request<ExportResponse>(`/cases/${caseId}/exports`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}
