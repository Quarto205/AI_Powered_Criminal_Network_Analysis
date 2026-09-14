/**
 * SIH26189 — Deterministic Timeline Mock Fixtures
 * Source: docs/contracts/04_API_SPEC.md, 08_UI_DATA_CONTRACT.md
 * 
 * Invariants:
 * 1. Strictly deterministic fixtures: no dynamic timestamps, no Math.random().
 * 2. Valid UUID-v4 IDs for all events and referenced entities.
 * 3. Aligned with caseMock.ts and graphMock.ts entity identities.
 * 4. Rich channel & event-type coverage with realistic masked values.
 * 5. Explicit [INSUFFICIENT TEMPORAL DATA] test case included.
 * 6. Earliest <= valid event timestamps <= Latest.
 */

import { TimelinePayload, TimelineApiResponse, TimelineEvent } from '../types/timeline';
import { PIVOT_NODE_ID, PHONE_NODE_ID, BANK_NODE_ID, PERSON_B_NODE_ID } from './graphMock';
import { mockActiveCase, mockCasesList } from './caseMock';

export const mockTimelineEvents: TimelineEvent[] = [
  {
    event_id: '1c9a1d2e-3f4b-4a5c-8d6e-7f8a9b0c1d2e',
    event_type: 'INCIDENT',
    channel: 'FIR_LOG',
    timestamp: '2026-08-10T08:30:00Z',
    source_entity_id: PIVOT_NODE_ID,
    source_label: 'Person A',
    summary: 'Preliminary offense report logged regarding suspicious cash deposits at Rohini branch.',
    metadata: {
      location_label: 'Rohini Sector 7, Delhi',
      amount: 450000,
      currency: 'INR'
    }
  },
  {
    event_id: '2d0b2e3f-4a5c-4b6d-9e7f-8a9b0c1d2e3f',
    event_type: 'COMMUNICATION',
    channel: 'CALL',
    timestamp: '2026-08-12T14:22:10Z',
    source_entity_id: PIVOT_NODE_ID,
    target_entity_id: PHONE_NODE_ID,
    source_label: 'Person A',
    target_label: 'Phone ••••5678',
    summary: 'Outbound voice call lasting 184 seconds from primary handset to carrier node.',
    metadata: {
      duration_seconds: 184,
      location_label: 'Connaught Place Tower 3'
    }
  },
  {
    event_id: '3e1c3f4a-5b6d-4c7e-0f8a-9b0c1d2e3f4a',
    event_type: 'TRANSACTION',
    channel: 'BANK_TRANSFER',
    timestamp: '2026-08-15T11:05:00Z',
    source_entity_id: PIVOT_NODE_ID,
    target_entity_id: BANK_NODE_ID,
    source_label: 'Person A',
    target_label: 'Account ••••4921',
    summary: 'NEFT credit to corporate proxy account with memo "Trade Clearance Fee".',
    metadata: {
      amount: 850000,
      currency: 'INR'
    }
  },
  {
    event_id: '4f2d4a5b-6c7e-4d8f-1a9b-0c1d2e3f4a5b',
    event_type: 'COMMUNICATION',
    channel: 'SMS',
    timestamp: '2026-08-17T09:12:45Z',
    source_entity_id: PHONE_NODE_ID,
    source_label: 'Phone ••••5678',
    summary: 'Automated banking OTP notification received regarding bulk transfer activation.',
    metadata: {
      location_label: 'Noida Sector 62'
    }
  },
  {
    event_id: '5a3e5b6c-7d8f-4e9a-2b0c-1d2e3f4a5b6c',
    event_type: 'MOVEMENT',
    channel: 'TOWER_PING',
    timestamp: '2026-08-19T16:45:00Z',
    source_entity_id: PHONE_NODE_ID,
    source_label: 'Phone ••••5678',
    summary: 'Cellular tower handover triangulation detected along GT Karnal Road corridor.',
    metadata: {
      location_label: 'GT Karnal Road Tollway, Delhi'
    }
  },
  {
    event_id: '6b4f6c7d-8e9a-4f0b-3c1d-2e3f4a5b6c7d',
    event_type: 'TRANSACTION',
    channel: 'UPI',
    timestamp: '2026-08-21T18:30:22Z',
    source_entity_id: PERSON_B_NODE_ID,
    target_entity_id: BANK_NODE_ID,
    source_label: 'Person B',
    target_label: 'Account ••••4921',
    summary: 'Structured peer-to-peer micro-remittance routed via merchant QR code.',
    metadata: {
      amount: 98000,
      currency: 'INR'
    }
  },
  {
    event_id: '7c5a7d8e-9f0b-4a1c-4d2e-3f4a5b6c7d8e',
    event_type: 'COMMUNICATION',
    channel: 'WHATSAPP',
    timestamp: '2026-08-23T20:10:00Z',
    source_entity_id: PERSON_B_NODE_ID,
    target_entity_id: PIVOT_NODE_ID,
    source_label: 'Person B',
    target_label: 'Person A',
    summary: 'Encrypted message session metadata observed during coordinate shift.',
    metadata: {
      duration_seconds: 45
    }
  },
  {
    event_id: '8d6b8e9f-0a1c-4b2d-5e3f-4a5b6c7d8e9f',
    event_type: 'OBSERVATION',
    channel: 'FIR_LOG',
    timestamp: '2026-08-24T12:00:00Z',
    source_entity_id: PIVOT_NODE_ID,
    source_label: 'Person A',
    summary: 'Physical surveillance log recording meeting outside Aerocity hospitality terminal.',
    metadata: {
      location_label: 'Terminal 3 Aerocity, New Delhi',
      has_incomplete_timestamp: true
    }
  }
];

export const mockTimelinePayload: TimelinePayload = {
  case_id: mockActiveCase.case_id,
  time_bounds: {
    earliest: '2026-08-10T00:00:00Z',
    latest: '2026-08-25T23:59:59Z'
  },
  total_events: mockTimelineEvents.length,
  events: mockTimelineEvents
};

export const mockTimelineResponse: TimelineApiResponse = {
  success: true,
  data: mockTimelinePayload,
  request_id: '7b8c9d0e-1f2a-4b3c-9d4e-5f6a7b8c9d0e'
};

/**
 * Secondary case timeline payload for cross-case verification
 */
export const mockSecondaryTimelinePayload: TimelinePayload = {
  case_id: mockCasesList[1].case_id,
  time_bounds: {
    earliest: '2026-08-20T00:00:00Z',
    latest: '2026-08-30T23:59:59Z'
  },
  total_events: 2,
  events: [
    {
      event_id: '9e7c9f0a-1b2d-4c3e-6f4a-5b6c7d8e9f0a',
      event_type: 'TRANSACTION',
      channel: 'BANK_TRANSFER',
      timestamp: '2026-08-22T10:00:00Z',
      summary: 'Offshore shell company wire dispatch to logistics agent.',
      metadata: {
        amount: 2500000,
        currency: 'USD',
        location_label: 'BKC, Mumbai'
      }
    },
    {
      event_id: '0f8d0a1b-2c3e-4d4f-7a5b-6c7d8e9f0a1b',
      event_type: 'INCIDENT',
      channel: 'FIR_LOG',
      timestamp: '2026-08-29T15:30:00Z',
      summary: 'Customs bill of entry audit flag raised at JNPT port.',
      metadata: {
        location_label: 'JNPT Port, Navi Mumbai',
        has_incomplete_timestamp: false
      }
    }
  ]
};

/**
 * Deterministic helper to get timeline payload by case_id
 */
export function getTimelineForCase(caseId: string): TimelinePayload {
  if (caseId === mockCasesList[1].case_id) {
    return mockSecondaryTimelinePayload;
  }
  return mockTimelinePayload;
}
