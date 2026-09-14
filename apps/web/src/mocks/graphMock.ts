/**
 * SIH26189 — Deterministic Graph Mock Fixtures
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
