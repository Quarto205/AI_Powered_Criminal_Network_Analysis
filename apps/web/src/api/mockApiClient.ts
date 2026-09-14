/**
 * Deterministic Mock API Client implementing IApiClient.
 * Uses synthetic fixtures and strict API envelope formatting.
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
import {
  DEMO_CASE_ID,
  DEMO_CASE_DETAIL,
  DEMO_CASES_LIST,
  DEMO_GRAPH,
  DEMO_ENTITIES_DETAIL,
  DEMO_RELATIONSHIPS_DETAIL,
  DEMO_EVIDENCE_SPANS,
  DEMO_ALERTS,
  DEMO_SCORES,
  DEMO_TIMELINE,
  DEMO_AUDIT_LOGS,
} from '../fixtures';

function makeEnvelope<T>(data: T): ApiSuccessResponse<T> {
  return {
    success: true,
    data,
    error: null,
    tracking_id: 'mock-tracking-' + Math.random().toString(36).substring(2, 10),
  };
}

export class MockApiClient implements IApiClient {
  private latencyMs: number;

  constructor(latencyMs: number = 0) {
    this.latencyMs = latencyMs;
  }

  private async delay(): Promise<void> {
    if (this.latencyMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, this.latencyMs));
    }
  }

  async listCases(params?: PaginationParams): Promise<ApiSuccessResponse<CaseListResponse>> {
    await this.delay();
    const limit = params?.limit ?? 10;
    const offset = params?.offset ?? 0;
    const paginated = DEMO_CASES_LIST.slice(offset, offset + limit);

    return makeEnvelope<CaseListResponse>({
      cases: paginated,
      total: DEMO_CASES_LIST.length,
      limit,
      offset,
    });
  }

  async getCase(caseId: string): Promise<ApiSuccessResponse<CaseDetailResponse>> {
    await this.delay();
    if (caseId === DEMO_CASE_ID) {
      return makeEnvelope<CaseDetailResponse>(DEMO_CASE_DETAIL);
    }
    // Return dummy detail for other valid case list items or 404 simulation
    const found = DEMO_CASES_LIST.find((c) => c.case_id === caseId);
    if (found) {
      return makeEnvelope<CaseDetailResponse>({
        case_id: found.case_id,
        case_code: found.case_code,
        title: found.title,
        description: 'Case description',
        status: found.status,
        jurisdiction: found.jurisdiction,
        created_by: 'mock-user-id',
        created_at: found.created_at,
        document_count: 3,
        entity_count: 6,
      });
    }
    throw new Error(`RESOURCE_NOT_FOUND: Case ${caseId} does not exist or access is unauthorized.`);
  }

  async createCase(payload: CaseCreateRequest): Promise<ApiSuccessResponse<CaseCreateResponse>> {
    await this.delay();
    const newCase: CaseCreateResponse = {
      case_id: 'new-' + Math.random().toString(36).substring(2, 9),
      case_code: payload.case_code,
      title: payload.title,
      status: 'ACTIVE',
      jurisdiction: payload.jurisdiction,
      created_at: new Date().toISOString(),
      created_by: 'current-user-uuid',
    };
    return makeEnvelope<CaseCreateResponse>(newCase);
  }

  async getCaseGraph(_caseId: string, params?: GraphQueryParams): Promise<ApiSuccessResponse<CaseGraphResponse>> {
    await this.delay();
    let graph = { ...DEMO_GRAPH };

    // Optional filtering simulation if pivot or filters provided
    if (params?.pivot_entity_id) {
      const pivot = params.pivot_entity_id;
      const relevantEdges = graph.edges.filter(
        (e) => e.data.source === pivot || e.data.target === pivot
      );
      const connectedNodeIds = new Set<string>([pivot]);
      relevantEdges.forEach((e) => {
        connectedNodeIds.add(e.data.source);
        connectedNodeIds.add(e.data.target);
      });
      const relevantNodes = graph.nodes.filter((n) => connectedNodeIds.has(n.data.id));

      graph = {
        nodes: relevantNodes,
        edges: relevantEdges,
        stats: {
          node_count: relevantNodes.length,
          edge_count: relevantEdges.length,
          predicted_edge_count: relevantEdges.filter((e) => e.data.is_predicted).length,
        },
      };
    }

    return makeEnvelope<CaseGraphResponse>(graph);
  }

  async triggerGraphRebuild(caseId: string): Promise<ApiSuccessResponse<GraphRebuildResponse>> {
    await this.delay();
    return makeEnvelope<GraphRebuildResponse>({
      case_id: caseId,
      job_id: 'job-rebuild-' + Math.random().toString(36).substring(2, 8),
      status: 'REBUILDING',
      created_at: new Date().toISOString(),
    });
  }

  async getEntityDetail(_caseId: string, entityId: string): Promise<ApiSuccessResponse<EntityDetailResponse>> {
    await this.delay();
    const entity = DEMO_ENTITIES_DETAIL[entityId];
    if (entity) {
      return makeEnvelope<EntityDetailResponse>(entity);
    }
    // Fallback dynamic entity detail matching graph node
    const graphNode = DEMO_GRAPH.nodes.find((n) => n.data.id === entityId);
    if (graphNode) {
      return makeEnvelope<EntityDetailResponse>({
        entity_id: graphNode.data.id,
        case_id: DEMO_CASE_ID,
        canonical_name: graphNode.data.label,
        entity_type: graphNode.data.entity_type,
        status: graphNode.data.status ?? 'ACTIVE',
        aliases: [],
        identifiers: [],
        risk_score: graphNode.data.risk_score
          ? {
              score_id: 'sc-dyn-' + graphNode.data.id,
              score_type: 'PRIORITY_RANKING',
              value: graphNode.data.risk_score,
            }
          : null,
        provenance_spans: [],
        created_at: '2026-08-14T10:00:00Z',
      });
    }
    throw new Error(`RESOURCE_NOT_FOUND: Entity ${entityId} not found.`);
  }

  async getRelationshipDetail(_caseId: string, relationshipId: string): Promise<ApiSuccessResponse<RelationshipDetailResponse>> {
    await this.delay();
    const rel = DEMO_RELATIONSHIPS_DETAIL[relationshipId];
    if (rel) {
      return makeEnvelope<RelationshipDetailResponse>(rel);
    }
    const graphEdge = DEMO_GRAPH.edges.find((e) => e.data.id === relationshipId);
    if (graphEdge) {
      return makeEnvelope<RelationshipDetailResponse>({
        relationship_id: graphEdge.data.id,
        case_id: DEMO_CASE_ID,
        source_entity: {
          entity_id: graphEdge.data.source,
          canonical_name: graphEdge.data.source,
          entity_type: 'ENTITY',
        },
        target_entity: {
          entity_id: graphEdge.data.target,
          canonical_name: graphEdge.data.target,
          entity_type: 'ENTITY',
        },
        type: graphEdge.data.type,
        status: graphEdge.data.is_predicted ? 'INFERRED' : 'OBSERVED',
        confidence_score: graphEdge.data.confidence_score,
        is_predicted: graphEdge.data.is_predicted,
        evidence_citations: [],
        created_at: '2026-08-14T11:00:00Z',
      });
    }
    throw new Error(`RESOURCE_NOT_FOUND: Relationship ${relationshipId} not found.`);
  }

  async getEvidenceDetail(_caseId: string, evidenceId: string): Promise<ApiSuccessResponse<ProvenanceSpan>> {
    await this.delay();
    const span = DEMO_EVIDENCE_SPANS[evidenceId];
    if (span) {
      return makeEnvelope<ProvenanceSpan>(span);
    }
    return makeEnvelope<ProvenanceSpan>({
      chunk_id: 'chk-default',
      document_id: 'doc-default',
      file_name: 'Case_Evidence_Log.pdf',
      page_number: 1,
      source_ref: evidenceId,
      support_type: 'INVESTIGATIVE_RECORD',
      snippet: 'Supporting case documentation verified by assigned case investigator.',
    });
  }

  async triggerAnalysis(caseId: string, payload: AnalysisTriggerRequest): Promise<ApiSuccessResponse<AnalysisTriggerResponse>> {
    await this.delay();
    return makeEnvelope<AnalysisTriggerResponse>({
      run_id: 'run-' + Math.random().toString(36).substring(2, 9),
      case_id: caseId,
      status: 'PENDING',
      pipelines: payload.pipelines,
      triggered_at: new Date().toISOString(),
    });
  }

  async getCaseAlerts(_caseId: string, params?: { severity?: string; status?: string }): Promise<ApiSuccessResponse<CaseAlertsResponse>> {
    await this.delay();
    let list = DEMO_ALERTS.alerts;
    if (params?.severity) {
      list = list.filter((a) => a.severity === params.severity);
    }
    if (params?.status) {
      list = list.filter((a) => a.status === params.status);
    }
    return makeEnvelope<CaseAlertsResponse>({
      case_id: DEMO_CASE_ID,
      alerts: list,
      total: list.length,
    });
  }

  async getCaseScores(_caseId: string): Promise<ApiSuccessResponse<CaseScoresResponse>> {
    await this.delay();
    return makeEnvelope<CaseScoresResponse>(DEMO_SCORES);
  }

  async submitReview(_caseId: string, payload: ReviewRequest): Promise<ApiSuccessResponse<ReviewResponse>> {
    await this.delay();
    return makeEnvelope<ReviewResponse>({
      review_id: 'rev-' + Math.random().toString(36).substring(2, 9),
      target_type: payload.target_type,
      target_id: payload.target_id,
      action: payload.action,
      resulting_status: payload.action === 'CONFIRM' ? 'CONFIRMED' : 'REJECTED',
      secondary_target_id: payload.secondary_target_id ?? null,
      applied_at: new Date().toISOString(),
      reason: payload.reason,
    });
  }

  async getCaseAudit(_caseId: string): Promise<ApiSuccessResponse<CaseAuditResponse>> {
    await this.delay();
    return makeEnvelope<CaseAuditResponse>({
      audit_logs: DEMO_AUDIT_LOGS,
      total: DEMO_AUDIT_LOGS.length,
    });
  }

  async getTimelineEvents(_caseId: string): Promise<ApiSuccessResponse<{ events: TimelineEventItem[]; total: number }>> {
    await this.delay();
    return makeEnvelope<{ events: TimelineEventItem[]; total: number }>({
      events: DEMO_TIMELINE,
      total: DEMO_TIMELINE.length,
    });
  }

  async exportReport(caseId: string, payload: ExportRequest): Promise<ApiSuccessResponse<ExportResponse>> {
    await this.delay();
    return makeEnvelope<ExportResponse>({
      export_id: 'exp-' + Math.random().toString(36).substring(2, 9),
      download_url: `/api/v1/cases/${caseId}/exports/download?format=${payload.export_format}`,
      hash: 'sha256:88fa2901bce47101ef',
    });
  }
}
