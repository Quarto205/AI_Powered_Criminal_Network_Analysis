/**
 * Deterministic Synthetic Cytoscape Graph Fixture
 * Strictly adheres to 03_GRAPH_SCHEMA.md, 04_API_SPEC.md, and 08_UI_DATA_CONTRACT.md.
 * Factual edges use 'solid' style_line; AI-inferred edges use 'dashed' style_line.
 */

import { CaseGraphResponse } from '../contracts/graph';
import { DEMO_CASE_ID } from './demoCase';

export const DEMO_GRAPH: CaseGraphResponse = {
  nodes: [
    {
      data: {
        id: 'ent-person-001',
        label: 'Rajesh Sharma',
        entity_type: 'PERSON',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        risk_score: 0.89,
        alias_count: 2,
        notes: 'Primary subject under surveillance for coordinated Hawala transfers',
      },
      position: { x: 150, y: 180 },
    },
    {
      data: {
        id: 'ent-person-002',
        label: 'Amitabh Sen',
        entity_type: 'PERSON',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        risk_score: 0.76,
        alias_count: 1,
        notes: 'Identified mule network coordinator and shell company director',
      },
      position: { x: 420, y: 120 },
    },
    {
      data: {
        id: 'ent-person-003',
        label: 'Vikram Verma',
        entity_type: 'PERSON',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        risk_score: 0.62,
        alias_count: 0,
        notes: 'Cash delivery courier operating around North Delhi distribution points',
      },
      position: { x: 300, y: 420 },
    },
    {
      data: {
        id: 'ent-phone-001',
        label: '+91 9811XXXX54',
        entity_type: 'PHONE',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        masked_identifier: '+91 9811XXXX54',
      },
      position: { x: 260, y: 80 },
    },
    {
      data: {
        id: 'ent-phone-002',
        label: '+91 9872XXXX19',
        entity_type: 'PHONE',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        masked_identifier: '+91 9872XXXX19',
      },
      position: { x: 360, y: 60 },
    },
    {
      data: {
        id: 'ent-bank-001',
        label: 'HDFC-XXXX8921',
        entity_type: 'BANK_ACCOUNT',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        provider: 'HDFC Bank',
        risk_score: 0.84,
      },
      position: { x: 550, y: 220 },
    },
    {
      data: {
        id: 'ent-bank-002',
        label: 'ICICI-XXXX4410',
        entity_type: 'BANK_ACCOUNT',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        provider: 'ICICI Bank',
        risk_score: 0.68,
      },
      position: { x: 480, y: 340 },
    },
    {
      data: {
        id: 'ent-bank-003',
        label: 'SBI-XXXX1102',
        entity_type: 'BANK_ACCOUNT',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        provider: 'State Bank of India',
        risk_score: 0.55,
      },
      position: { x: 350, y: 320 },
    },
    {
      data: {
        id: 'ent-veh-001',
        label: 'DL 01 XX 4412',
        entity_type: 'VEHICLE',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        type: 'Mahindra Scorpio (Black)',
      },
      position: { x: 80, y: 300 },
    },
    {
      data: {
        id: 'ent-org-001',
        label: 'Zenith Logistics Pvt Ltd',
        entity_type: 'ORGANIZATION',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
        type: 'Cargo & Freight Forwarding',
      },
      position: { x: 580, y: 110 },
    },
    {
      data: {
        id: 'ent-loc-001',
        label: 'Chandni Chowk Hawala Hub',
        entity_type: 'LOCATION',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
      },
      position: { x: 80, y: 110 },
    },
    {
      data: {
        id: 'ent-loc-002',
        label: 'Karol Bagh Safehouse',
        entity_type: 'LOCATION',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
      },
      position: { x: 180, y: 450 },
    },
    {
      data: {
        id: 'ent-off-001',
        label: 'FIR 104/2026 IPC 420/120B',
        entity_type: 'OFFENSE',
        case_id: DEMO_CASE_ID,
        status: 'ACTIVE',
      },
      position: { x: 180, y: 20 },
    },
  ],
  edges: [
    // Factual Evidence Edges (Solid Lines)
    {
      data: {
        id: 'rel-001',
        source: 'ent-person-001',
        target: 'ent-phone-001',
        type: 'OWNS',
        confidence_score: 1.0,
        is_predicted: false,
        provenance_count: 2,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-002',
        source: 'ent-phone-001',
        target: 'ent-phone-002',
        type: 'COMMUNICATED_WITH',
        confidence_score: 1.0,
        is_predicted: false,
        provenance_count: 4,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-003',
        source: 'ent-phone-002',
        target: 'ent-person-002',
        type: 'USED_BY',
        confidence_score: 0.92,
        is_predicted: false,
        provenance_count: 2,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-004',
        source: 'ent-person-002',
        target: 'ent-bank-001',
        type: 'OWNS',
        confidence_score: 1.0,
        is_predicted: false,
        provenance_count: 3,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-005',
        source: 'ent-bank-001',
        target: 'ent-bank-002',
        type: 'TRANSFERRED_TO',
        confidence_score: 1.0,
        is_predicted: false,
        provenance_count: 5,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-006',
        source: 'ent-bank-002',
        target: 'ent-bank-003',
        type: 'TRANSFERRED_TO',
        confidence_score: 1.0,
        is_predicted: false,
        provenance_count: 3,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-007',
        source: 'ent-bank-003',
        target: 'ent-person-003',
        type: 'OWNED_BY',
        confidence_score: 0.95,
        is_predicted: false,
        provenance_count: 2,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-008',
        source: 'ent-person-001',
        target: 'ent-veh-001',
        type: 'OWNS',
        confidence_score: 0.98,
        is_predicted: false,
        provenance_count: 1,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-009',
        source: 'ent-person-001',
        target: 'ent-loc-001',
        type: 'LOCATED_AT',
        confidence_score: 0.90,
        is_predicted: false,
        provenance_count: 2,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-010',
        source: 'ent-person-003',
        target: 'ent-loc-002',
        type: 'LOCATED_AT',
        confidence_score: 0.85,
        is_predicted: false,
        provenance_count: 1,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-011',
        source: 'ent-person-002',
        target: 'ent-org-001',
        type: 'AFFILIATED_WITH',
        confidence_score: 0.94,
        is_predicted: false,
        provenance_count: 2,
        style_line: 'solid',
      },
    },
    {
      data: {
        id: 'rel-012',
        source: 'ent-person-001',
        target: 'ent-off-001',
        type: 'ACCUSED_IN',
        confidence_score: 1.0,
        is_predicted: false,
        provenance_count: 3,
        style_line: 'solid',
      },
    },

    // AI-Inferred / Machine-Learning Predicted Associations (Dashed Lines)
    {
      data: {
        id: 'pred-001',
        source: 'ent-person-001',
        target: 'ent-person-003',
        type: 'CONTACTED',
        confidence_score: 0.82,
        is_predicted: true,
        provenance_count: 0,
        style_line: 'dashed',
        model_name: 'GATv2 Link Predictor',
        model_version: 'v1.0.4',
        explanation: 'Model predicted latent coordination based on shared transactional destinations and synchronized tower pings.',
      },
    },
    {
      data: {
        id: 'pred-002',
        source: 'ent-bank-003',
        target: 'ent-bank-001',
        type: 'TRANSFERRED_TO',
        confidence_score: 0.74,
        is_predicted: true,
        provenance_count: 0,
        style_line: 'dashed',
        model_name: 'Hawala Cycle Motif Detector',
        model_version: 'v2.1',
        explanation: 'Rapid circular fund return pattern suspected across intermediary cash settlement agents.',
      },
    },
  ],
  stats: {
    node_count: 13,
    edge_count: 14,
    predicted_edge_count: 2,
  },
};
