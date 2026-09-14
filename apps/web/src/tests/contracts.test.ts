import { describe, it, expect } from 'vitest';
import {
  MasterStates,
  DocumentStates,
  RelationshipStates,
  ReviewStates,
  UserRoles,
  EntityTypes,
  RelationshipTypes,
} from '../contracts/common';
import { ErrorCodes } from '../contracts/api';
import { DEMO_CASE_DETAIL, DEMO_GRAPH, DEMO_ALERTS } from '../fixtures';

describe('Contracts & Shared Types Validation', () => {
  it('should verify canonical master lifecycle states', () => {
    expect(MasterStates.UNAUTHENTICATED).toBe('UNAUTHENTICATED');
    expect(MasterStates.CASE_SELECTED).toBe('CASE_SELECTED');
    expect(MasterStates.GRAPH_READY).toBe('GRAPH_READY');
    expect(MasterStates.REPORTING_AUDIT).toBe('REPORTING/AUDIT');
  });

  it('should verify canonical document states progression', () => {
    expect(DocumentStates.RECEIVED).toBe('RECEIVED');
    expect(DocumentStates.VALIDATED).toBe('VALIDATED');
    expect(DocumentStates.PROCESSING).toBe('PROCESSING');
    expect(DocumentStates.EXTRACTED).toBe('EXTRACTED');
    expect(DocumentStates.REVIEW_REQUIRED).toBe('REVIEW_REQUIRED');
    expect(DocumentStates.ACCEPTED).toBe('ACCEPTED');
    expect(DocumentStates.REJECTED).toBe('REJECTED');
    expect(DocumentStates.FAILED).toBe('FAILED');
  });

  it('should verify relationship evidence states', () => {
    expect(RelationshipStates.OBSERVED).toBe('OBSERVED');
    expect(RelationshipStates.CORROBORATED).toBe('CORROBORATED');
    expect(RelationshipStates.CONFIRMED).toBe('CONFIRMED');
    expect(RelationshipStates.REJECTED).toBe('REJECTED');
    expect(RelationshipStates.INFERRED).toBe('INFERRED');
  });

  it('should verify RBAC roles', () => {
    expect(UserRoles.INVESTIGATOR).toBe('INVESTIGATOR');
    expect(UserRoles.ANALYST).toBe('ANALYST');
    expect(UserRoles.SUPERVISOR).toBe('SUPERVISOR');
  });

  it('should verify review states and error codes', () => {
    expect(ReviewStates.NEW).toBe('NEW');
    expect(ReviewStates.REVIEWED).toBe('REVIEWED');
    expect(ReviewStates.CONFIRMED).toBe('CONFIRMED');
    expect(ReviewStates.REJECTED).toBe('REJECTED');
    expect(ErrorCodes.UNAUTHORIZED).toBe('UNAUTHORIZED');
    expect(ErrorCodes.RESOURCE_NOT_FOUND).toBe('RESOURCE_NOT_FOUND');
  });

  it('should verify canonical entity and relationship types', () => {
    expect(EntityTypes.PERSON).toBe('PERSON');
    expect(EntityTypes.PHONE).toBe('PHONE');
    expect(EntityTypes.BANK_ACCOUNT).toBe('BANK_ACCOUNT');
    expect(EntityTypes.VEHICLE).toBe('VEHICLE');
    expect(EntityTypes.ORGANIZATION).toBe('ORGANIZATION');
    expect(EntityTypes.LOCATION).toBe('LOCATION');

    expect(RelationshipTypes.OWNS).toBe('OWNS');
    expect(RelationshipTypes.COMMUNICATED_WITH).toBe('COMMUNICATED_WITH');
    expect(RelationshipTypes.TRANSFERRED_TO).toBe('TRANSFERRED_TO');
  });

  it('should verify demo case fixture conforms to contract', () => {
    expect(DEMO_CASE_DETAIL.case_id).toBeDefined();
    expect(DEMO_CASE_DETAIL.case_code).toBe('CR-2026-DEL-0891');
    expect(DEMO_CASE_DETAIL.document_count).toBeGreaterThan(0);
    expect(DEMO_CASE_DETAIL.entity_count).toBeGreaterThan(0);
  });

  it('should verify Cytoscape graph fixture contains solid and dashed edges', () => {
    const solidEdges = DEMO_GRAPH.edges.filter((e) => e.data.style_line === 'solid');
    const dashedEdges = DEMO_GRAPH.edges.filter((e) => e.data.style_line === 'dashed');

    expect(solidEdges.length).toBeGreaterThan(0);
    expect(dashedEdges.length).toBeGreaterThan(0);

    // All solid edges must NOT be predicted
    solidEdges.forEach((e) => {
      expect(e.data.is_predicted).toBe(false);
    });

    // All dashed edges must be marked as predicted
    dashedEdges.forEach((e) => {
      expect(e.data.is_predicted).toBe(true);
    });
  });

  it('should verify non-accusatory language in alert rules', () => {
    DEMO_ALERTS.alerts.forEach((alert) => {
      expect(alert.alert_type).not.toContain('CRIMINAL');
      expect(alert.alert_type).not.toContain('GUILT');
      expect(alert.alert_type).not.toContain('KINGPIN');
    });
  });
});
