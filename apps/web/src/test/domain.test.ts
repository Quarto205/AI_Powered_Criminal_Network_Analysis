import { describe, it, expect } from 'vitest';
import {
  INITIAL_CASES,
  MOCK_ENTITIES,
  MOCK_EDGES,
  MOCK_EVIDENCE_DOCS,
  MOCK_PRIORITY_LEADS,
} from '../mocks/data';

describe('CNAS Forensic Domain Data Architecture', () => {
  it('loads active case Operation Hawala Nexus with full metadata', () => {
    const activeCase = INITIAL_CASES[0];
    expect(activeCase.caseNumber).toBe('CASE-2026-DEL-0891');
    expect(activeCase.status).toBe('ACTIVE');
    expect(activeCase.leadInvestigator.name).toBe('Insp. Ananya Roy');
  });

  it('strictly segregates verified observed edges from AI inferred edges', () => {
    const verifiedEdges = MOCK_EDGES.filter((e) => e.epistemicType === 'VERIFIED_OBSERVED');
    const inferredEdges = MOCK_EDGES.filter((e) => e.epistemicType === 'AI_INFERRED');

    expect(verifiedEdges.length).toBeGreaterThan(0);
    expect(inferredEdges.length).toBeGreaterThan(0);

    // AI inferred edges must have valid confidence scores
    inferredEdges.forEach((edge) => {
      expect(edge.confidence).toBeGreaterThanOrEqual(0.85);
    });
  });

  it('strictly adheres to non-accusatory terminology', () => {
    const forbiddenTerms = ['guilt', 'guilty', 'kingpin', 'crime probability'];

    MOCK_PRIORITY_LEADS.forEach((lead) => {
      forbiddenTerms.forEach((term) => {
        expect(lead.title.toLowerCase()).not.toContain(term);
        expect(lead.description.toLowerCase()).not.toContain(term);
      });
      // Expected analytical category
      expect(['GNN_ASSOCIATION', 'FAN_OUT', 'GEO_FENCE', 'SMURFING']).toContain(lead.category);
    });
  });

  it('guarantees Section 65B cryptographic attestation on evidentiary files', () => {
    MOCK_EVIDENCE_DOCS.forEach((doc) => {
      expect(doc.sha256).toBeDefined();
      expect(doc.sha256.length).toBeGreaterThan(16);
      expect(doc.section65BCertified).toBe(true);
    });
  });

  it('contains target facilitator Tariq M. with biometric verification', () => {
    const tariq = MOCK_ENTITIES.find((e) => e.id === 'ent-tariq');
    expect(tariq).toBeDefined();
    expect(tariq?.biometricVerified).toBe(true);
    expect(tariq?.threatLevel).toBe('CRITICAL');
  });
});
