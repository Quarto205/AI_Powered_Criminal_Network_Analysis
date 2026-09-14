/**
 * SIH26189 â€” Deterministic Graph Mock Fixture
 * Strictly adheres to 03_GRAPH_SCHEMA.md, 08_UI_DATA_CONTRACT.md, and contracts.ts.
 *
 * NOTE: For frontend development and testing only.
 * Demonstrates:
 * - Solid edges for observed evidence (with source provenance)
 * - Dashed edges for AI-inferred link predictions (with GATv2 metadata)
 * - Multi-type entity nodes (PERSON, PHONE, BANK_ACCOUNT, VEHICLE, LOCATION)
 * - Non-accusatory priority score attributes
 */

import {
  CaseGraphResponse,
  CytoscapeNode,
  CytoscapeEdge,
  EntityTypes,
  RelationshipTypes,
  RelationshipStates,
  ReviewStates,
} from '../types/contracts';
import { MOCK_CASE_ID } from './caseMock';

export const MOCK_GRAPH_NODES: CytoscapeNode[] = [
  {
    data: {
      id: 'node-person-1',
      label: 'Tariq Khan',
      entity_type: EntityTypes.PERSON,
      case_id: MOCK_CASE_ID,
      status: 'UNDER_SURVEILLANCE',
      priority_score: 0.89,
      alias_count: 2,
      properties: {
        aliases: ['Bhaijaan', 'TK'],
        jurisdiction: 'Special Cell North',
      },
    },
    position: { x: 250, y: 150 },
  },
  {
    data: {
      id: 'node-person-2',
      label: 'Vikram Sharma',
      entity_type: EntityTypes.PERSON,
      case_id: MOCK_CASE_ID,
      status: 'IDENTIFIED',
      priority_score: 0.68,
      alias_count: 1,
      properties: {
        aliases: ['Vicky Delhi'],
      },
    },
    position: { x: 500, y: 150 },
  },
  {
    data: {
      id: 'node-person-3',
      label: 'Rajesh Gupta',
      entity_type: EntityTypes.PERSON,
      case_id: MOCK_CASE_ID,
      status: 'ASSOCIATE',
      priority_score: 0.54,
      alias_count: 0,
      properties: {
        occupation: 'Hawala Operator / Courier',
      },
    },
    position: { x: 380, y: 380 },
  },
  {
    data: {
      id: 'node-phone-1',
      label: '+91 98110 XXXXX',
      entity_type: EntityTypes.PHONE,
      case_id: MOCK_CASE_ID,
      status: 'ACTIVE_INTERCEPT',
      masked_identifier: '+91 98110 •••••',
    },
    position: { x: 180, y: 270 },
  },
  {
    data: {
      id: 'node-phone-2',
      label: '+91 98731 XXXXX',
      entity_type: EntityTypes.PHONE,
      case_id: MOCK_CASE_ID,
      status: 'CONFIRMED',
      masked_identifier: '+91 98731 •••••',
    },
    position: { x: 560, y: 270 },
  },
  {
    data: {
      id: 'node-phone-3',
      label: '+91 98200 XXXXX',
      entity_type: EntityTypes.PHONE,
      case_id: MOCK_CASE_ID,
      status: 'BURNER_SUSPECTED',
      masked_identifier: '+91 98200 •••••',
    },
    position: { x: 680, y: 200 },
  },
  {
    data: {
      id: 'node-bank-1',
      label: 'HDFC AC-••••4819',
      entity_type: EntityTypes.BANK_ACCOUNT,
      case_id: MOCK_CASE_ID,
      status: 'FLAGGED_TRANSACTIONS',
      masked_identifier: 'HDFC-••••-4819',
    },
    position: { x: 180, y: 420 },
  },
  {
    data: {
      id: 'node-bank-2',
      label: 'ICICI AC-••••9102',
      entity_type: EntityTypes.BANK_ACCOUNT,
      case_id: MOCK_CASE_ID,
      status: 'UNDER_SCRUTINY',
      masked_identifier: 'ICICI-••••-9102',
    },
    position: { x: 520, y: 420 },
  },
  {
    data: {
      id: 'node-loc-1',
      label: 'Jamia Nagar, Delhi',
      entity_type: EntityTypes.LOCATION,
      case_id: MOCK_CASE_ID,
      status: 'TOWER_CLUSTER',
      properties: {
        coordinates: '28.5612, 77.2801',
      },
    },
    position: { x: 380, y: 40 },
  },
  {
    data: {
      id: 'node-veh-1',
      label: 'DL 01 AB ••••',
      entity_type: EntityTypes.VEHICLE,
      case_id: MOCK_CASE_ID,
      status: 'SURVEILLANCE_FLAG',
      masked_identifier: 'DL 01 AB ••••',
    },
    position: { x: 80, y: 150 },
  },
];

export const MOCK_GRAPH_EDGES: CytoscapeEdge[] = [
  // Factual, source-backed evidence edges (SOLID line, is_predicted = false)
  {
    data: {
      id: 'edge-1',
      source: 'node-person-1',
      target: 'node-phone-1',
      type: RelationshipTypes.OWNS,
      confidence_score: 0.98,
      is_predicted: false,
      provenance_count: 2,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0001-fact-owns-phone1',
        status: RelationshipStates.CONFIRMED,
        source_ref_count: 2,
        relationship_confidence: 0.98,
        confidence_type: 'OBSERVED_CAF_AND_CDR',
        observed_at: '2026-02-10T14:30:00Z',
        source_system: 'TELECOM_CAF_REGISTRY',
        evidence_ids: ['ev-001', 'ev-002'],
      },
    },
  },
  {
    data: {
      id: 'edge-2',
      source: 'node-person-2',
      target: 'node-phone-2',
      type: RelationshipTypes.OWNS,
      confidence_score: 0.95,
      is_predicted: false,
      provenance_count: 2,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0002-fact-owns-phone2',
        status: RelationshipStates.CONFIRMED,
        source_ref_count: 2,
        relationship_confidence: 0.95,
        confidence_type: 'OBSERVED_KYC',
        observed_at: '2026-02-11T10:15:00Z',
        source_system: 'TELCO_VERIFICATION',
        evidence_ids: ['ev-003'],
      },
    },
  },
  {
    data: {
      id: 'edge-3',
      source: 'node-phone-1',
      target: 'node-phone-2',
      type: RelationshipTypes.COMMUNICATED_WITH,
      confidence_score: 0.92,
      is_predicted: false,
      provenance_count: 4,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0003-fact-comm-phone1-phone2',
        status: RelationshipStates.CORROBORATED,
        source_ref_count: 4,
        relationship_confidence: 0.92,
        confidence_type: 'CDR_EXCHANGE',
        belief: 0.85,
        disbelief: 0.05,
        uncertainty: 0.10,
        observed_at: '2026-02-12T22:18:00Z',
        source_system: 'CDR_INGESTION_PIPELINE',
        evidence_ids: ['ev-004', 'ev-005'],
      },
    },
  },
  {
    data: {
      id: 'edge-4',
      source: 'node-person-1',
      target: 'node-bank-1',
      type: RelationshipTypes.OWNS,
      confidence_score: 0.99,
      is_predicted: false,
      provenance_count: 3,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0004-fact-owns-bank1',
        status: RelationshipStates.CONFIRMED,
        source_ref_count: 3,
        relationship_confidence: 0.99,
        confidence_type: 'BANKING_KYC',
        observed_at: '2026-01-15T09:00:00Z',
        source_system: 'CBS_INTELLIGENCE_EXTRACT',
        evidence_ids: ['ev-006'],
      },
    },
  },
  {
    data: {
      id: 'edge-5',
      source: 'node-person-3',
      target: 'node-bank-2',
      type: RelationshipTypes.OWNS,
      confidence_score: 0.96,
      is_predicted: false,
      provenance_count: 2,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0005-fact-owns-bank2',
        status: RelationshipStates.CONFIRMED,
        source_ref_count: 2,
        relationship_confidence: 0.96,
        confidence_type: 'BANKING_KYC',
        observed_at: '2026-01-18T11:45:00Z',
        source_system: 'CBS_INTELLIGENCE_EXTRACT',
        evidence_ids: ['ev-007'],
      },
    },
  },
  {
    data: {
      id: 'edge-6',
      source: 'node-bank-1',
      target: 'node-bank-2',
      type: RelationshipTypes.TRANSFERRED_TO,
      confidence_score: 0.98,
      is_predicted: false,
      provenance_count: 3,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0006-fact-transfer-bank1-bank2',
        status: RelationshipStates.CORROBORATED,
        source_ref_count: 3,
        relationship_confidence: 0.98,
        confidence_type: 'NEFT_RTGS_OBSERVATION',
        observed_at: '2026-02-13T16:20:00Z',
        source_system: 'FINANCIAL_INTELLIGENCE_UNIT',
        evidence_ids: ['ev-008'],
      },
    },
  },
  {
    data: {
      id: 'edge-7',
      source: 'node-person-1',
      target: 'node-loc-1',
      type: RelationshipTypes.LOCATED_AT,
      confidence_score: 0.88,
      is_predicted: false,
      provenance_count: 2,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0007-fact-located-tariq-jamia',
        status: RelationshipStates.OBSERVED,
        source_ref_count: 2,
        relationship_confidence: 0.88,
        confidence_type: 'CELL_TOWER_TRIANGULATION',
        observed_at: '2026-02-12T22:25:00Z',
        source_system: 'TOWER_DUMP_ANALYZER',
        evidence_ids: ['ev-009'],
      },
    },
  },
  {
    data: {
      id: 'edge-8',
      source: 'node-person-1',
      target: 'node-veh-1',
      type: RelationshipTypes.OWNS,
      confidence_score: 0.94,
      is_predicted: false,
      provenance_count: 1,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0008-fact-owns-veh1',
        status: RelationshipStates.CONFIRMED,
        source_ref_count: 1,
        relationship_confidence: 0.94,
        confidence_type: 'VAHAN_REGISTRATION_EXTRACT',
        observed_at: '2026-02-05T08:30:00Z',
        source_system: 'VAHAN_PORTAL',
        evidence_ids: ['ev-010'],
      },
    },
  },
  {
    data: {
      id: 'edge-9',
      source: 'node-person-2',
      target: 'node-phone-3',
      type: RelationshipTypes.USED_BY,
      confidence_score: 0.85,
      is_predicted: false,
      provenance_count: 1,
      style_line: 'solid',
      factual_evidence: {
        relationship_id: 'rel-0009-fact-used-phone3',
        status: RelationshipStates.OBSERVED,
        source_ref_count: 1,
        relationship_confidence: 0.85,
        confidence_type: 'IMEI_HANDSET_SHARING',
        observed_at: '2026-02-14T19:00:00Z',
        source_system: 'IMEI_LINK_ANALYZER',
        evidence_ids: ['ev-011'],
      },
    },
  },

  // AI-Inferred / Link Prediction edges (DASHED line, is_predicted = true)
  {
    data: {
      id: 'edge-predicted-1',
      source: 'node-person-1',
      target: 'node-person-3',
      type: RelationshipTypes.KNOWS,
      confidence_score: 0.84,
      is_predicted: true,
      provenance_count: 0,
      style_line: 'dashed',
      inference_prediction: {
        prediction_id: 'pred-001-gat-tariq-rajesh',
        model_run_id: 'run-gatv2-20260215-01',
        score: 0.84,
        calibration_status: 'ISOTONIC_CALIBRATED',
        review_status: ReviewStates.NEW,
        model_name: 'GATv2-Supervised-LinkPredictor',
        model_version: 'v1.4.0',
        explanation:
          'High structural similarity via shared financial transaction path (Bank-1 -> Bank-2) and co-located mobile tower activity.',
      },
    },
  },
  {
    data: {
      id: 'edge-predicted-2',
      source: 'node-phone-2',
      target: 'node-phone-3',
      type: RelationshipTypes.COMMUNICATED_WITH,
      confidence_score: 0.76,
      is_predicted: true,
      provenance_count: 0,
      style_line: 'dashed',
      inference_prediction: {
        prediction_id: 'pred-002-gat-phone2-phone3',
        model_run_id: 'run-gatv2-20260215-01',
        score: 0.76,
        calibration_status: 'ISOTONIC_CALIBRATED',
        review_status: ReviewStates.REVIEWED,
        model_name: 'GATv2-Supervised-LinkPredictor',
        model_version: 'v1.4.0',
        explanation:
          'Candidate burner phone correlation based on IMEI sharing pattern and synchronized dormant periods.',
      },
    },
  },
];

export const MOCK_GRAPH: CaseGraphResponse = {
  nodes: MOCK_GRAPH_NODES,
  edges: MOCK_GRAPH_EDGES,
  stats: {
    node_count: MOCK_GRAPH_NODES.length,
    edge_count: MOCK_GRAPH_EDGES.length,
    predicted_edge_count: MOCK_GRAPH_EDGES.filter((e) => e.data.is_predicted).length,
  },
};

// --- Track A Compatibility Mocks ---
/**
 * SIH26189 â€” Deterministic Graph Mock Fixtures
 * Source: docs/contracts/03_GRAPH_SCHEMA.md, 04_API_SPEC.md, 08_UI_DATA_CONTRACT.md
 * 
 * Invariants:
 * 1. Deterministic synthetic data: no dynamic generators, no Math.random().
 * 2. Every node and edge ID is a valid UUID-v4 format.
 * 3. Non-accusatory, evidence-aware labeling (Person A, Phone ••••5678).
 * 4. Distinct evidence states:
 *    - Source-backed evidence: CONFIRMED, CORROBORATED (is_inferred = false)
 *    - Model prediction: INFERRED (is_inferred = true, normalized confidence score)
 */

import { GraphDataPayload, GraphApiResponse } from '../types/graph';

export const PIVOT_NODE_ID = 'e2b8c9d4-1a3f-4e7b-8c5d-9a0f1b2c3d4e';
export const PHONE_NODE_ID = 'f3c9d0e5-2b4a-4f8c-9d6e-0b1a2c3d4e5f';
export const BANK_NODE_ID = 'a4d0e1f6-3c5b-4a9d-0e7f-1c2b3d4e5f6a';
export const PERSON_B_NODE_ID = 'b5e1f2a7-4d6c-4b0e-1f8a-2d3c4e5f6a7b';

export const mockGraphPayload: GraphDataPayload = {
  nodes: [
    {
      data: {
        id: PIVOT_NODE_ID,
        label: 'Person A',
        entity_type: 'Person',
        status: 'VERIFIED',
        alias_count: 2,
        is_pivot: true
      }
    },
    {
      data: {
        id: PHONE_NODE_ID,
        label: 'Phone ••••5678',
        entity_type: 'Phone',
        status: 'ACTIVE',
        masked_identifier: '+91-XXXXX-5678'
      }
    },
    {
      data: {
        id: BANK_NODE_ID,
        label: 'Account ••••4921',
        entity_type: 'BankAccount',
        status: 'FLAGGED',
        masked_identifier: 'SBIN000XXXX4921'
      }
    },
    {
      data: {
        id: PERSON_B_NODE_ID,
        label: 'Person B',
        entity_type: 'Person',
        status: 'UNDER_INQUIRY',
        alias_count: 0
      }
    }
  ],
  edges: [
    {
      data: {
        id: 'c6f2a3b8-5e7d-4c1f-2a9b-3e4d5f6a7b8c',
        source: PIVOT_NODE_ID,
        target: PHONE_NODE_ID,
        relationship_type: 'OWNS',
        status: 'CONFIRMED',
        is_inferred: false
      }
    },
    {
      data: {
        id: 'd7a3b4c9-6f8e-4d2a-3b0c-4f5e6a7b8c9d',
        source: PIVOT_NODE_ID,
        target: BANK_NODE_ID,
        relationship_type: 'OWNS',
        status: 'CORROBORATED',
        is_inferred: false
      }
    },
    {
      data: {
        id: 'e8b4c5d0-7a9f-4e3b-4c1d-5a6f7b8c9d0e',
        source: PERSON_B_NODE_ID,
        target: BANK_NODE_ID,
        relationship_type: 'TRANSFERRED_TO',
        status: 'INFERRED',
        confidence: 0.84,
        is_inferred: true
      }
    }
  ]
};

export const mockGraphResponse: GraphApiResponse = {
  success: true,
  data: mockGraphPayload,
  request_id: '8a1b2c3d-4e5f-4a0b-9c8d-7e6f5a4b3c2d'
};
