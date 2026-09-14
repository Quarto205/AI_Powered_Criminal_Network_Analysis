import { describe, it, expect } from 'vitest';
import { MockApiClient } from '../api/mockApiClient';
import { DEMO_CASE_ID } from '../fixtures';

describe('MockApiClient Endpoint Tests', () => {
  const client = new MockApiClient(0);

  it('should list cases wrapped in ApiSuccessResponse envelope', async () => {
    const res = await client.listCases();
    expect(res.success).toBe(true);
    expect(res.error).toBeNull();
    expect(res.tracking_id).toBeDefined();
    expect(res.data.cases.length).toBeGreaterThan(0);
    expect(res.data.cases[0].case_code).toBe('CR-2026-DEL-0891');
  });

  it('should get case detail by valid caseId', async () => {
    const res = await client.getCase(DEMO_CASE_ID);
    expect(res.success).toBe(true);
    expect(res.data.case_id).toBe(DEMO_CASE_ID);
    expect(res.data.title).toContain('Operation Hawala Nexus');
  });

  it('should reject non-existent caseId with error', async () => {
    await expect(client.getCase('non-existent-case-id')).rejects.toThrow('RESOURCE_NOT_FOUND');
  });

  it('should get case graph with Cytoscape formatted nodes and edges', async () => {
    const res = await client.getCaseGraph(DEMO_CASE_ID);
    expect(res.success).toBe(true);
    expect(res.data.nodes.length).toBeGreaterThan(0);
    expect(res.data.edges.length).toBeGreaterThan(0);

    // Verify Cytoscape.js structure: { data: { id, label, ... } }
    const sampleNode = res.data.nodes[0];
    expect(sampleNode.data.id).toBeDefined();
    expect(sampleNode.data.entity_type).toBeDefined();

    const sampleEdge = res.data.edges[0];
    expect(sampleEdge.data.source).toBeDefined();
    expect(sampleEdge.data.target).toBeDefined();
    expect(sampleEdge.data.style_line).toMatch(/solid|dashed/);
  });

  it('should retrieve detailed entity metadata and provenance spans', async () => {
    const res = await client.getEntityDetail(DEMO_CASE_ID, 'ent-person-001');
    expect(res.success).toBe(true);
    expect(res.data.canonical_name).toBe('Rajesh Sharma');
    expect(res.data.aliases.length).toBeGreaterThan(0);
    expect(res.data.provenance_spans.length).toBeGreaterThan(0);
  });

  it('should submit human review override', async () => {
    const res = await client.submitReview(DEMO_CASE_ID, {
      target_type: 'ENTITY',
      target_id: 'ent-person-001',
      action: 'CONFIRM',
      reason: 'Verified against FIR report',
    });
    expect(res.success).toBe(true);
    expect(res.data.resulting_status).toBe('CONFIRMED');
  });

  it('should retrieve immutable audit logs', async () => {
    const res = await client.getCaseAudit(DEMO_CASE_ID);
    expect(res.success).toBe(true);
    expect(res.data.audit_logs.length).toBeGreaterThan(0);
    expect(res.data.audit_logs[0].action).toBeDefined();
  });
});
