/**
 * SIH26189 — Unit Tests for Universal Frontend Contracts & Deterministic Mocks
 * Validates Phase 0 / Step 1 contract foundation deliverables.
 */

import { describe, it, expect } from 'vitest';
import {
  MasterStates,
  DocumentStates,
  RelationshipStates,
  ReviewStates,
  ReviewActions,
  ReviewTargetTypes,
  UserRoles,
  EntityTypes,
  RelationshipTypes,
  ErrorCodes,
  ApiSuccessResponse,
  ApiErrorResponse,
  CaseDetailResponse,
  CaseGraphResponse,
  EntityDetailResponse,
  RelationshipDetailResponse,
  EntityReviewQueueResponse,
} from '../types/contracts';

import {
  MOCK_CASE_ID,
  MOCK_CASE_CODE,
  MOCK_CASE_DETAIL,
  MOCK_CASE_LIST,
  MOCK_CASE_MEMBERS,
  MOCK_CASE_LIST_RESPONSE,
} from '../mocks/caseMock';

import {
  MOCK_GRAPH,
  MOCK_GRAPH_NODES,
  MOCK_GRAPH_EDGES,
} from '../mocks/graphMock';

import {
  MOCK_ENTITY_DETAIL_TARIQ,
  MOCK_ENTITY_DETAIL_VIKRAM,
  MOCK_RELATIONSHIP_DETAIL_FACTUAL,
  MOCK_RELATIONSHIP_DETAIL_PREDICTED,
  MOCK_ENTITY_REVIEW_ITEMS,
  MOCK_ENTITY_REVIEW_QUEUE,
  MOCK_DOCUMENTS,
  MOCK_PROVENANCE_FIR,
  MOCK_PROVENANCE_CDR,
  MOCK_PROVENANCE_BANK,
} from '../mocks/evidenceMock';

describe('Phase 0 / Step 1: Universal Frontend Contracts Validation', () => {
  it('should verify all canonical lifecycle enums from 01_SHARED_TYPES.md', () => {
    // Master states
    expect(MasterStates.UNAUTHENTICATED).toBe('UNAUTHENTICATED');
    expect(MasterStates.AUTHENTICATED).toBe('AUTHENTICATED');
    expect(MasterStates.CASE_SELECTED).toBe('CASE_SELECTED');
    expect(MasterStates.INGESTION).toBe('INGESTION');
    expect(MasterStates.PROCESSING).toBe('PROCESSING');
    expect(MasterStates.REVIEW).toBe('REVIEW');
    expect(MasterStates.GRAPH_READY).toBe('GRAPH_READY');
    expect(MasterStates.ANALYSIS).toBe('ANALYSIS');
    expect(MasterStates.INVESTIGATOR_REVIEW).toBe('INVESTIGATOR_REVIEW');
    expect(MasterStates.REPORTING_AUDIT).toBe('REPORTING/AUDIT');

    // Document states
    expect(DocumentStates.RECEIVED).toBe('RECEIVED');
    expect(DocumentStates.VALIDATED).toBe('VALIDATED');
    expect(DocumentStates.PROCESSING).toBe('PROCESSING');
    expect(DocumentStates.EXTRACTED).toBe('EXTRACTED');
    expect(DocumentStates.REVIEW_REQUIRED).toBe('REVIEW_REQUIRED');
    expect(DocumentStates.ACCEPTED).toBe('ACCEPTED');
    expect(DocumentStates.REJECTED).toBe('REJECTED');
    expect(DocumentStates.FAILED).toBe('FAILED');

    // Relationship states
    expect(RelationshipStates.OBSERVED).toBe('OBSERVED');
    expect(RelationshipStates.CORROBORATED).toBe('CORROBORATED');
    expect(RelationshipStates.CONFIRMED).toBe('CONFIRMED');
    expect(RelationshipStates.REJECTED).toBe('REJECTED');
    expect(RelationshipStates.INFERRED).toBe('INFERRED');

    // Review states & actions
    expect(ReviewStates.NEW).toBe('NEW');
    expect(ReviewStates.REVIEWED).toBe('REVIEWED');
    expect(ReviewStates.CONFIRMED).toBe('CONFIRMED');
    expect(ReviewStates.REJECTED).toBe('REJECTED');
    expect(ReviewActions.CONFIRM).toBe('CONFIRM');
    expect(ReviewActions.REJECT).toBe('REJECT');
    expect(ReviewActions.MERGE).toBe('MERGE');

    // Review target types
    expect(ReviewTargetTypes.ENTITY_RESOLUTION).toBe('ENTITY_RESOLUTION');
    expect(ReviewTargetTypes.PREDICTION).toBe('PREDICTION');
    expect(ReviewTargetTypes.EXTRACTION).toBe('EXTRACTION');

    // Roles
    expect(UserRoles.INVESTIGATOR).toBe('INVESTIGATOR');
    expect(UserRoles.ANALYST).toBe('ANALYST');
    expect(UserRoles.SUPERVISOR).toBe('SUPERVISOR');
  });

  it('should verify canonical entity and relationship types', () => {
    expect(EntityTypes.PERSON).toBe('PERSON');
    expect(EntityTypes.PHONE).toBe('PHONE');
    expect(EntityTypes.BANK_ACCOUNT).toBe('BANK_ACCOUNT');
    expect(EntityTypes.VEHICLE).toBe('VEHICLE');
    expect(EntityTypes.ORGANIZATION).toBe('ORGANIZATION');
    expect(EntityTypes.LOCATION).toBe('LOCATION');

    expect(RelationshipTypes.ACCUSED_IN).toBe('ACCUSED_IN');
    expect(RelationshipTypes.KNOWS).toBe('KNOWS');
    expect(RelationshipTypes.CONTACTED).toBe('CONTACTED');
    expect(RelationshipTypes.LOCATED_AT).toBe('LOCATED_AT');
    expect(RelationshipTypes.OWNS).toBe('OWNS');
    expect(RelationshipTypes.COMMUNICATED_WITH).toBe('COMMUNICATED_WITH');
    expect(RelationshipTypes.TRANSFERRED_TO).toBe('TRANSFERRED_TO');
  });

  it('should verify universal API response envelope contract', () => {
    const successSample: ApiSuccessResponse<{ count: number }> = {
      success: true,
      data: { count: 42 },
      error: null,
      request_id: '12345678-1234-1234-1234-123456789012',
      tracking_id: '12345678-1234-1234-1234-123456789012',
    };
    expect(successSample.success).toBe(true);
    expect(successSample.data.count).toBe(42);
    expect(successSample.error).toBeNull();
    expect(successSample.tracking_id).toBeDefined();

    const errorSample: ApiErrorResponse = {
      success: false,
      data: null,
      error: {
        code: ErrorCodes.RESOURCE_NOT_FOUND,
        message: 'Requested case entity not found within authorized tenant scope',
        details: { case_id: MOCK_CASE_ID },
      },
      request_id: '87654321-4321-4321-4321-210987654321',
      tracking_id: '87654321-4321-4321-4321-210987654321',
    };
    expect(errorSample.success).toBe(false);
    expect(errorSample.data).toBeNull();
    expect(errorSample.error.code).toBe(ErrorCodes.RESOURCE_NOT_FOUND);
  });
});

describe('Phase 0 / Step 1: Deterministic Case Mocks Validation', () => {
  it('should validate MOCK_CASE_DETAIL conforms strictly to CaseDetailResponse', () => {
    const caseDetail: CaseDetailResponse = MOCK_CASE_DETAIL;
    expect(caseDetail.case_id).toBe(MOCK_CASE_ID);
    expect(caseDetail.case_code).toBe(MOCK_CASE_CODE);
    expect(caseDetail.status).toBe('ACTIVE');
    expect(caseDetail.document_count).toBeGreaterThan(0);
    expect(caseDetail.entity_count).toBeGreaterThan(0);
    expect(caseDetail.created_by).toBeDefined();
    expect(caseDetail.jurisdiction).toContain('Delhi Police');
  });

  it('should validate MOCK_CASE_MEMBERS and authorization roles', () => {
    expect(MOCK_CASE_MEMBERS.length).toBe(3);
    const roles = MOCK_CASE_MEMBERS.map((m) => m.role_in_case);
    expect(roles).toContain(UserRoles.INVESTIGATOR);
    expect(roles).toContain(UserRoles.ANALYST);
    expect(roles).toContain(UserRoles.SUPERVISOR);
  });

  it('should validate MOCK_CASE_LIST_RESPONSE conforms to list structure', () => {
    expect(MOCK_CASE_LIST_RESPONSE.cases.length).toBe(MOCK_CASE_LIST.length);
    expect(MOCK_CASE_LIST_RESPONSE.total).toBe(3);
    expect(MOCK_CASE_LIST_RESPONSE.limit).toBe(10);
  });
});

describe('Phase 0 / Step 1: Deterministic Graph Mocks Validation', () => {
  it('should validate MOCK_GRAPH conforms strictly to CaseGraphResponse', () => {
    const graph: CaseGraphResponse = MOCK_GRAPH;
    expect(graph.nodes.length).toBe(MOCK_GRAPH_NODES.length);
    expect(graph.edges.length).toBe(MOCK_GRAPH_EDGES.length);
    expect(graph.stats.node_count).toBe(10);
    expect(graph.stats.edge_count).toBe(11);
    expect(graph.stats.predicted_edge_count).toBe(2);
  });

  it('INVARIANT: solid edges must be strictly observed evidence, dashed edges must be AI predicted', () => {
    const solidEdges = MOCK_GRAPH.edges.filter((e) => e.data.style_line === 'solid');
    const dashedEdges = MOCK_GRAPH.edges.filter((e) => e.data.style_line === 'dashed');

    expect(solidEdges.length).toBe(9);
    expect(dashedEdges.length).toBe(2);

    // Verify all solid edges
    solidEdges.forEach((e) => {
      expect(e.data.is_predicted).toBe(false);
      expect(e.data.factual_evidence).toBeDefined();
      expect(e.data.inference_prediction).toBeUndefined();
      expect(e.data.provenance_count).toBeGreaterThan(0);
      expect(
        [
          RelationshipStates.OBSERVED,
          RelationshipStates.CORROBORATED,
          RelationshipStates.CONFIRMED,
        ]
      ).toContain(e.data.factual_evidence?.status);
    });

    // Verify all dashed edges
    dashedEdges.forEach((e) => {
      expect(e.data.is_predicted).toBe(true);
      expect(e.data.inference_prediction).toBeDefined();
      expect(e.data.factual_evidence).toBeUndefined();
      expect(e.data.inference_prediction?.model_name).toBe('GATv2-Supervised-LinkPredictor');
      expect(e.data.inference_prediction?.score).toBeGreaterThan(0);
      expect(e.data.inference_prediction?.score).toBeLessThanOrEqual(1);
    });
  });

  it('should verify all graph edges point to valid nodes in the graph', () => {
    const nodeIds = new Set(MOCK_GRAPH.nodes.map((n) => n.data.id));
    MOCK_GRAPH.edges.forEach((e) => {
      expect(nodeIds.has(e.data.source)).toBe(true);
      expect(nodeIds.has(e.data.target)).toBe(true);
    });
  });

  it('INVARIANT: Node scores must be non-accusatory priority rankings, not guilt probabilities', () => {
    MOCK_GRAPH.nodes.forEach((n) => {
      if (n.data.priority_score !== undefined && n.data.priority_score !== null) {
        expect(n.data.priority_score).toBeGreaterThanOrEqual(0);
        expect(n.data.priority_score).toBeLessThanOrEqual(1);
        expect(n.data).not.toHaveProperty('guilt_probability');
        expect(n.data).not.toHaveProperty('kingpin_score');
      }
    });
  });
});

describe('Phase 0 / Step 1: Deterministic Evidence & Provenance Mocks Validation', () => {
  it('should validate character-level provenance spans across multiple document types', () => {
    // FIR PDF provenance
    expect(MOCK_PROVENANCE_FIR.document_id).toBe('doc-001-fir-42-2024');
    expect(MOCK_PROVENANCE_FIR.file_name).toBe('FIR_42_2026_Special_Cell.pdf');
    expect(MOCK_PROVENANCE_FIR.page_number).toBe(2);
    expect(MOCK_PROVENANCE_FIR.character_start).toBe(340);
    expect(MOCK_PROVENANCE_FIR.character_end).toBe(495);
    expect(MOCK_PROVENANCE_FIR.support_type).toBe('SUPPORTS');

    // CDR CSV provenance
    expect(MOCK_PROVENANCE_CDR.file_name).toContain('.csv');
    expect(MOCK_PROVENANCE_CDR.source_ref).toContain('row819');

    // Bank Statement PDF provenance
    expect(MOCK_PROVENANCE_BANK.page_number).toBe(5);
    expect(MOCK_PROVENANCE_BANK.snippet).toContain('NEFT/RTGS');
  });

  it('should validate entity drill-down detail fixtures (MOCK_ENTITY_DETAIL_TARIQ & VIKRAM)', () => {
    const entity: EntityDetailResponse = MOCK_ENTITY_DETAIL_TARIQ;
    expect(entity.entity_id).toBe('node-person-1');
    expect(entity.canonical_name).toBe('Tariq Khan');
    expect(entity.entity_type).toBe(EntityTypes.PERSON);
    expect(entity.aliases.length).toBe(2);
    expect(entity.identifiers.length).toBe(2);
    expect(entity.risk_score?.score_type).toBe('INVESTIGATIVE_PRIORITY');
    expect(entity.provenance_spans.length).toBe(2);

    const entityVikram: EntityDetailResponse = MOCK_ENTITY_DETAIL_VIKRAM;
    expect(entityVikram.entity_id).toBe('node-person-2');
    expect(entityVikram.canonical_name).toBe('Vikram Sharma');
    expect(entityVikram.aliases[0].alias_text).toBe('Vicky Delhi');
  });

  it('should validate factual vs predicted relationship drill-down details', () => {
    const factualRel: RelationshipDetailResponse = MOCK_RELATIONSHIP_DETAIL_FACTUAL;
    expect(factualRel.is_predicted).toBe(false);
    expect(factualRel.style_line).toBe('solid');
    expect(factualRel.evidence_citations.length).toBeGreaterThan(0);
    expect(factualRel.factual_evidence).toBeDefined();
    expect(factualRel.inference_prediction).toBeUndefined();

    const predictedRel: RelationshipDetailResponse = MOCK_RELATIONSHIP_DETAIL_PREDICTED;
    expect(predictedRel.is_predicted).toBe(true);
    expect(predictedRel.style_line).toBe('dashed');
    expect(predictedRel.inference_prediction).toBeDefined();
    expect(predictedRel.inference_prediction?.model_name).toContain('GATv2');
    expect(predictedRel.inference_prediction?.explanation).toContain('financial transaction path');
  });

  it('should validate Entity Review Queue fixtures for ambiguous entity resolution', () => {
    const queue: EntityReviewQueueResponse = MOCK_ENTITY_REVIEW_QUEUE;
    expect(queue.total).toBe(3);
    expect(queue.pending_count).toBe(2);

    // Check item 1 (Vikram S. ambiguous candidate)
    const item1 = MOCK_ENTITY_REVIEW_ITEMS[0];
    expect(item1.target_type).toBe('ENTITY_RESOLUTION');
    expect(item1.source_mention.extracted_text).toBe('Vikram S.');
    expect(item1.candidate_entity.canonical_name).toBe('Vikram Sharma');
    expect(item1.match_metadata.similarity_score).toBe(0.78);
    expect(item1.match_metadata.match_algorithm).toBe('JARO_WINKLER');
    expect(item1.match_metadata.threshold_applied).toBe(0.85);
    expect(item1.review_status).toBe(ReviewStates.NEW);
    expect(item1.provenance.page_number).toBe(3);
    expect(item1.provenance.character_start).toBe(1042);
  });

  it('should validate mock documents list fixtures', () => {
    expect(MOCK_DOCUMENTS.length).toBe(4);
    const hashes = MOCK_DOCUMENTS.map((d) => d.file_hash);
    expect(new Set(hashes).size).toBe(4); // All file hashes unique within case scope
  });
});
