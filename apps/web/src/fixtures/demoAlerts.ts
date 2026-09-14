/**
 * Deterministic Synthetic Alerts & Priority Scores Fixtures
 * Strictly adheres to 05_AI_CONTRACTS.md and main/backend/schemas/evidence_analysis.py.
 * Non-accusatory language: Pattern Alert, Priority Ranking, Investigative Lead.
 */

import { CaseAlertsResponse } from '../types/contracts';
import { CaseScoresResponse } from '../contracts/analysis';
import { DEMO_CASE_ID } from './demoCase';

export const DEMO_ALERTS: CaseAlertsResponse = {
  case_id: DEMO_CASE_ID,
  total: 5,
  alerts: [
    {
      alert_id: 'alt-001',
      case_id: DEMO_CASE_ID,
      alert_type: 'CIRCULAR_TRANSACTION_CYCLE',
      severity: 'HIGH',
      rule_id: 'RULE-FIN-MOTIF-01',
      status: 'NEW',
      description: 'Potential closed funds cycle detected: HDFC-XXXX8921 -> ICICI-XXXX4410 -> SBI-XXXX1102 within a 72-hour window.',
      contributing_entities: [
        { entity_id: 'node-bank-1', canonical_name: 'HDFC-XXXX8921', role: 'ORIGIN' },
        { entity_id: 'node-bank-2', canonical_name: 'ICICI-XXXX4410', role: 'INTERMEDIARY' },
        { entity_id: 'node-bank-3', canonical_name: 'SBI-XXXX1102', role: 'CASH_OUT' },
      ],
      created_at: '2026-02-14T18:30:00Z',
      evidence_context: {
        cycle_pattern: 'A -> B -> C -> A',
        window_hours: 72,
        has_temporal_data: true,
      },
    },
    {
      alert_id: 'alt-002',
      case_id: DEMO_CASE_ID,
      alert_type: 'COMMUNICATION_BURST',
      severity: 'HIGH',
      rule_id: 'RULE-CDR-BURST-04',
      status: 'NEW',
      description: 'Anomalous call frequency surge between +91 9811XXXX54 and +91 9872XXXX19 immediately preceding fund disbursement.',
      contributing_entities: [
        { entity_id: 'node-phone-1', canonical_name: '+91 98110 XXXXX', role: 'CALLER' },
        { entity_id: 'node-phone-2', canonical_name: '+91 98731 XXXXX', role: 'CALLEE' },
      ],
      created_at: '2026-02-12T22:20:00Z',
      evidence_context: {
        burst_duration_minutes: 15,
        call_count: 8,
        has_temporal_data: true,
      },
    },
    {
      alert_id: 'alt-003',
      case_id: DEMO_CASE_ID,
      alert_type: 'HIGH_BETWEENNESS_BRIDGE',
      severity: 'MEDIUM',
      rule_id: 'RULE-SNA-BRIDGE-02',
      status: 'REVIEWED',
      description: 'Rajesh Sharma exhibits top-percentile betweenness centrality (0.88), bridging logistical and financial communities.',
      contributing_entities: [
        { entity_id: 'node-person-3', canonical_name: 'Rajesh Gupta', role: 'BRIDGE_NODE' },
      ],
      created_at: '2026-02-13T12:00:00Z',
      evidence_context: {
        betweenness_score: 0.88,
        has_temporal_data: true,
      },
    },
    {
      alert_id: 'alt-004',
      case_id: DEMO_CASE_ID,
      alert_type: 'RAPID_FAN_OUT',
      severity: 'HIGH',
      rule_id: 'RULE-FIN-FANOUT-03',
      status: 'NEW',
      description: 'Rapid fan-out disbursement: HDFC-XXXX8921 transferred funds to 5 recipient accounts within 10 minutes.',
      contributing_entities: [
        { entity_id: 'node-bank-1', canonical_name: 'HDFC-XXXX8921', role: 'SOURCE_DISBURSER' },
        { entity_id: 'node-bank-2', canonical_name: 'ICICI-XXXX4410', role: 'RECIPIENT_1' },
      ],
      created_at: '2026-02-14T09:15:00Z',
      evidence_context: {
        fan_out_count: 5,
        window_minutes: 10,
        has_temporal_data: true,
      },
    },
    {
      alert_id: 'alt-005',
      case_id: DEMO_CASE_ID,
      alert_type: 'TRANSACTION_CYCLE_UNVERIFIED',
      severity: 'LOW',
      rule_id: 'RULE-FIN-MOTIF-09',
      status: 'NEW',
      description: 'Suspected recurring transfer cluster flagged with incomplete timestamps across manual ledger entries.',
      contributing_entities: [
        { entity_id: 'node-bank-2', canonical_name: 'ICICI-XXXX4410', role: 'ACCUSED_LEDGER' },
      ],
      created_at: undefined,
      evidence_context: {
        has_temporal_data: false,
        temporal_data_incomplete: true,
      },
    },
  ],
};

export const DEMO_SCORES: CaseScoresResponse = {
  case_id: DEMO_CASE_ID,
  total: 3,
  scores: [
    {
      score_id: 'scr-001',
      entity_id: 'ent-person-001',
      canonical_name: 'Rajesh Sharma',
      entity_type: 'PERSON',
      score_type: 'INVESTIGATIVE_PRIORITY',
      value: 0.89,
      features_summary: {
        betweenness: 0.88,
        degree: 0.75,
        pagerank: 0.82,
        community_id: 1,
        reasoning: 'Primary topological bridge linking communication cell to ground transportation vehicles.',
      },
    },
    {
      score_id: 'scr-002',
      entity_id: 'ent-bank-001',
      canonical_name: 'HDFC-XXXX8921',
      entity_type: 'BANK_ACCOUNT',
      score_type: 'INVESTIGATIVE_PRIORITY',
      value: 0.84,
      features_summary: {
        betweenness: 0.65,
        degree: 0.70,
        pagerank: 0.78,
        community_id: 1,
        reasoning: 'Apex account receiving high-velocity aggregations with subsequent fan-out distribution.',
      },
    },
    {
      score_id: 'scr-003',
      entity_id: 'ent-person-002',
      canonical_name: 'Amitabh Sen',
      entity_type: 'PERSON',
      score_type: 'INVESTIGATIVE_PRIORITY',
      value: 0.76,
      features_summary: {
        betweenness: 0.72,
        degree: 0.60,
        pagerank: 0.69,
        community_id: 1,
        reasoning: 'Corporate officer with registered corporate vehicle affiliations and burner SIM usage.',
      },
    },
  ],
};
