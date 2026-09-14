/**
 * Deterministic Synthetic Graph Fixture (SIH26189)
 * 
 * DISCLAIMER: This is synthetic fixture data for frontend visualization prototyping.
 * It is NOT live operational police CDR, IPDR, or banking intelligence.
 */

import { CytoscapeNodeElement, CytoscapeEdgeElement } from '../types/contracts';

export const SYNTHETIC_DEMO_CASE_ID = 'c0000000-0000-4000-8000-000000000001';

export const SYNTHETIC_GRAPH_NODES: CytoscapeNodeElement[] = [
  {
    data: {
      id: 'n1-person-rajesh',
      label: 'Suspect A (Rajesh Kumar)',
      category: 'Person',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      statusBadge: 'Primary Target',
      isConfirmed: true,
      metadata: { role: 'Coordinator', aliases: ['Raju', 'RK'] }
    }
  },
  {
    data: {
      id: 'n2-phone-rajesh',
      label: '+91-98765-43210',
      category: 'Phone',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      statusBadge: 'Active CDR',
      metadata: { imsi: '40445XXXXXXXXXX', provider: 'Airtel' }
    }
  },
  {
    data: {
      id: 'n3-person-vikram',
      label: 'Associate B (Vikram Singh)',
      category: 'Person',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      statusBadge: 'Suspect',
      metadata: { role: 'Courier' }
    }
  },
  {
    data: {
      id: 'n4-account-mule',
      label: 'HDFC AC **4921',
      category: 'BankAccount',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      statusBadge: 'Flagged Mule Account',
      metadata: { branch: 'Connaught Place', ifsc: 'HDFC0000123' }
    }
  },
  {
    data: {
      id: 'n5-location-delhi',
      label: 'Warehouse (Okhla Phase III)',
      category: 'Location',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      statusBadge: 'Meeting Point',
      metadata: { city: 'New Delhi', lat: 28.5355, lng: 77.2711 }
    }
  }
];

export const SYNTHETIC_GRAPH_EDGES: CytoscapeEdgeElement[] = [
  // 1. Source-backed evidence: Phone ownership (OBSERVED -> Solid Line)
  {
    data: {
      id: 'e1-rajesh-phone',
      source: 'n1-person-rajesh',
      target: 'n2-phone-rajesh',
      type: 'USES_PHONE',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      evidenceState: 'OBSERVED',
      sourceExcerpt: 'SIM registration form seized under Panchnama Memo P-12.',
      provenanceDocumentId: 'd0000000-0000-4000-8000-000000000001'
    }
  },
  // 2. Source-backed evidence: Bank transaction (CONFIRMED -> Solid Line)
  {
    data: {
      id: 'e2-rajesh-account',
      source: 'n1-person-rajesh',
      target: 'n4-account-mule',
      type: 'TRANSACTED_WITH',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      evidenceState: 'CONFIRMED',
      sourceExcerpt: 'Bank statement line item TXN994821 confirmed by SBI nodal officer.',
      provenanceDocumentId: 'd0000000-0000-4000-8000-000000000002'
    }
  },
  // 3. AI-Inferred Link: GATv2 association prediction (INFERRED -> DASHED LINE)
  {
    data: {
      id: 'e3-rajesh-vikram-inferred',
      source: 'n1-person-rajesh',
      target: 'n3-person-vikram',
      type: 'ASSOCIATED_WITH',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      evidenceState: 'INFERRED',
      confidence: {
        modelConfidence: 0.82,
        investigationPriority: 0.76
      },
      sourceExcerpt: 'GATv2 link-prediction model inferred co-travel pattern and shared mule account bridge.'
    }
  },
  // 4. Source-backed evidence: Location visit (OBSERVED -> Solid Line)
  {
    data: {
      id: 'e4-vikram-location',
      source: 'n3-person-vikram',
      target: 'n5-location-delhi',
      type: 'VISITED',
      caseId: SYNTHETIC_DEMO_CASE_ID,
      evidenceState: 'OBSERVED',
      sourceExcerpt: 'Tower CDR dump indicates cell ID matching Okhla tower on 2026-03-01.'
    }
  }
];

export const SYNTHETIC_GRAPH_DATASET = {
  caseId: SYNTHETIC_DEMO_CASE_ID,
  nodes: SYNTHETIC_GRAPH_NODES,
  edges: SYNTHETIC_GRAPH_EDGES
};
