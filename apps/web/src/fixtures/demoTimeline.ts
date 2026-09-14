/**
 * Deterministic Synthetic Timeline Fixture
 * Strictly adheres to 02_DATABASE_SCHEMA.md (events table) and 08_UI_DATA_CONTRACT.md.
 */

import { TimelineEventItem } from '../contracts/audit';
import { DEMO_CASE_ID } from './demoCase';

export const DEMO_TIMELINE: TimelineEventItem[] = [
  {
    event_id: 'ev-time-001',
    case_id: DEMO_CASE_ID,
    event_type: 'COMMUNICATION',
    timestamp: '2026-08-04T18:42:10Z',
    description: '342s voice call between +91 9811XXXX54 and +91 9872XXXX19 collocated via North Delhi tower',
    entities_involved: [
      { entity_id: 'ent-phone-001', canonical_name: '+91 9811XXXX54', role: 'CALLER' },
      { entity_id: 'ent-phone-002', canonical_name: '+91 9872XXXX19', role: 'CALLEE' },
    ],
    source_ref: 'CDR_Export_9811XXXX54_Aug2026.csv:row#42',
  },
  {
    event_id: 'ev-time-002',
    case_id: DEMO_CASE_ID,
    event_type: 'TRANSACTION',
    timestamp: '2026-08-04T19:15:00Z',
    description: 'RTGS transfer of ₹ 14,50,000 from HDFC-XXXX8921 to ICICI-XXXX4410',
    entities_involved: [
      { entity_id: 'ent-bank-001', canonical_name: 'HDFC-XXXX8921', role: 'SENDER' },
      { entity_id: 'ent-bank-002', canonical_name: 'ICICI-XXXX4410', role: 'RECEIVER' },
    ],
    source_ref: 'Bank_Statement_HDFC_Aug2026.csv:row#102',
  },
  {
    event_id: 'ev-time-003',
    case_id: DEMO_CASE_ID,
    event_type: 'TRANSACTION',
    timestamp: '2026-08-04T20:30:00Z',
    description: 'Immediate split disbursement: ₹ 4,90,000 from ICICI-XXXX4410 to SBI-XXXX1102',
    entities_involved: [
      { entity_id: 'ent-bank-002', canonical_name: 'ICICI-XXXX4410', role: 'SENDER' },
      { entity_id: 'ent-bank-003', canonical_name: 'SBI-XXXX1102', role: 'RECEIVER' },
    ],
    source_ref: 'Bank_Statement_ICICI_Aug2026.csv:row#58',
  },
  {
    event_id: 'ev-time-004',
    case_id: DEMO_CASE_ID,
    event_type: 'MOVEMENT',
    timestamp: '2026-08-05T09:10:00Z',
    description: 'ANPR camera detection of DL 01 XX 4412 at Karol Bagh junction towards Chandni Chowk',
    entities_involved: [
      { entity_id: 'ent-veh-001', canonical_name: 'DL 01 XX 4412', role: 'VEHICLE' },
      { entity_id: 'ent-loc-002', canonical_name: 'Karol Bagh Safehouse', role: 'VICINITY' },
    ],
    source_ref: 'ANPR_Delhi_Police_Toll_Dump.csv:row#910',
  },
  {
    event_id: 'ev-time-005',
    case_id: DEMO_CASE_ID,
    event_type: 'DOCUMENT_OBSERVATION',
    timestamp: '2026-08-14T09:30:00Z',
    description: 'FIR 104/2026 registered at Special Cell PS citing organized Hawala nexus',
    entities_involved: [
      { entity_id: 'ent-person-001', canonical_name: 'Rajesh Sharma', role: 'NAMED_ACCUSED' },
      { entity_id: 'ent-off-001', canonical_name: 'FIR 104/2026 IPC 420/120B', role: 'OFFENSE' },
    ],
    source_ref: 'FIR_104_2026_SpecialCell.pdf',
  },
];
