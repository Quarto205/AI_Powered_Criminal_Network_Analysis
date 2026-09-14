/**
 * Deterministic Synthetic Evidence & Provenance Fixtures
 * Strictly adheres to 01_SHARED_TYPES.md, 04_API_SPEC.md, and 08_UI_DATA_CONTRACT.md.
 */

import { EntityDetailResponse } from '../contracts/entities';
import { RelationshipDetailResponse, ProvenanceSpan } from '../contracts/evidence';
import { DEMO_CASE_ID } from './demoCase';

export const DEMO_ENTITIES_DETAIL: Record<string, EntityDetailResponse> = {
  'ent-person-001': {
    entity_id: 'ent-person-001',
    case_id: DEMO_CASE_ID,
    canonical_name: 'Rajesh Sharma',
    entity_type: 'PERSON',
    status: 'ACTIVE',
    aliases: [
      { alias_id: 'al-01', alias_text: 'Raju Seth', source_ref: 'FIR-104-para-4' },
      { alias_id: 'al-02', alias_text: 'Sharma Ji Hawala', source_ref: 'CDR-Note-Delhi' },
    ],
    identifiers: [
      { identifier_id: 'id-01', type: 'PHONE_NUMBER', masked_value: '+91 9811XXXX54', value_policy: 'MASK_MIDDLE_4' },
      { identifier_id: 'id-02', type: 'VEHICLE_PLATE', masked_value: 'DL 01 XX 4412', value_policy: 'MASK_SERIES' },
    ],
    risk_score: {
      score_id: 'sc-01',
      score_type: 'PRIORITY_RANKING',
      value: 0.89,
      features_summary: {
        degree_centrality: 0.75,
        betweenness_centrality: 0.88,
        pagerank: 0.82,
        community_id: 1,
        reasoning: 'High betweenness broker node bridging financial mule accounts and ground delivery vehicles.',
      },
    },
    provenance_spans: [
      {
        chunk_id: 'chk-01',
        document_id: 'doc-fir-01',
        file_name: 'FIR_104_2026_SpecialCell.pdf',
        page_number: 2,
        character_start: 340,
        character_end: 462,
        source_ref: 'FIR_104_2026_SpecialCell.pdf:p2#340-462',
        support_type: 'FIR_PARAGRAPH',
        snippet: '...stated that Rajesh Sharma alias Raju Seth operates hawala transactions from a shop premises in Chandni Chowk...',
      },
      {
        chunk_id: 'chk-02',
        document_id: 'doc-cdr-01',
        file_name: 'CDR_Export_9811XXXX54_Aug2026.csv',
        page_number: 1,
        character_start: 12,
        character_end: 98,
        source_ref: 'CDR_Export_9811XXXX54_Aug2026.csv:row#42',
        support_type: 'CDR_ROW',
        snippet: 'MSISDN +91 9811XXXX54 outgoing 32 calls to +91 9872XXXX19 between 2026-08-01 and 2026-08-10.',
      },
    ],
    created_at: '2026-08-14T10:00:00Z',
  },

  'ent-person-002': {
    entity_id: 'ent-person-002',
    case_id: DEMO_CASE_ID,
    canonical_name: 'Amitabh Sen',
    entity_type: 'PERSON',
    status: 'ACTIVE',
    aliases: [
      { alias_id: 'al-03', alias_text: 'Dada Sen', source_ref: 'MCA-Directors-Report' },
    ],
    identifiers: [
      { identifier_id: 'id-03', type: 'PHONE_NUMBER', masked_value: '+91 9872XXXX19', value_policy: 'MASK_MIDDLE_4' },
      { identifier_id: 'id-04', type: 'BANK_ACCOUNT', masked_value: 'HDFC-XXXX8921', value_policy: 'MASK_MIDDLE_4' },
    ],
    risk_score: {
      score_id: 'sc-02',
      score_type: 'PRIORITY_RANKING',
      value: 0.76,
      features_summary: {
        degree_centrality: 0.60,
        betweenness_centrality: 0.72,
        pagerank: 0.69,
        community_id: 1,
        reasoning: 'Director of Zenith Logistics shell entity and controller of apex mule account.',
      },
    },
    provenance_spans: [
      {
        chunk_id: 'chk-03',
        document_id: 'doc-mca-01',
        file_name: 'MCA_Filing_Zenith_Logistics.pdf',
        page_number: 4,
        character_start: 110,
        character_end: 245,
        source_ref: 'MCA_Filing_Zenith_Logistics.pdf:p4#110-245',
        support_type: 'OFFICIAL_REGISTRY',
        snippet: '...Managing Director designated: Amitabh Sen, DIN 09841283, registered address Karol Bagh, New Delhi...',
      },
    ],
    created_at: '2026-08-14T10:05:00Z',
  },

  'ent-person-003': {
    entity_id: 'ent-person-003',
    case_id: DEMO_CASE_ID,
    canonical_name: 'Vikram Verma',
    entity_type: 'PERSON',
    status: 'ACTIVE',
    aliases: [],
    identifiers: [
      { identifier_id: 'id-05', type: 'BANK_ACCOUNT', masked_value: 'SBI-XXXX1102', value_policy: 'MASK_MIDDLE_4' },
    ],
    risk_score: {
      score_id: 'sc-03',
      score_type: 'PRIORITY_RANKING',
      value: 0.62,
      features_summary: {
        degree_centrality: 0.45,
        betweenness_centrality: 0.51,
        pagerank: 0.48,
        community_id: 2,
        reasoning: 'Downstream distribution cash-out account holder with frequent ATM withdrawals.',
      },
    },
    provenance_spans: [
      {
        chunk_id: 'chk-04',
        document_id: 'doc-bank-01',
        file_name: 'Bank_Statement_SBI_Aug2026.csv',
        page_number: 1,
        character_start: 50,
        character_end: 180,
        source_ref: 'Bank_Statement_SBI_Aug2026.csv:row#18',
        support_type: 'BANK_RECORD',
        snippet: 'A/C 3847291102 IFSC SBIN0001234 in name of Vikram Verma, multiple UPI inflows followed by immediate cash debits.',
      },
    ],
    created_at: '2026-08-14T10:10:00Z',
  },
};

export const DEMO_RELATIONSHIPS_DETAIL: Record<string, RelationshipDetailResponse> = {
  'rel-002': {
    relationship_id: 'rel-002',
    case_id: DEMO_CASE_ID,
    source_entity: {
      entity_id: 'ent-phone-001',
      canonical_name: '+91 9811XXXX54',
      entity_type: 'PHONE',
    },
    target_entity: {
      entity_id: 'ent-phone-002',
      canonical_name: '+91 9872XXXX19',
      entity_type: 'PHONE',
    },
    type: 'COMMUNICATED_WITH',
    status: 'CORROBORATED',
    confidence_score: 1.0,
    is_predicted: false,
    evidence_citations: [
      {
        evidence_id: 'ev-01',
        source_ref: 'CDR_Export_9811XXXX54_Aug2026.csv',
        support_type: 'CDR_ROW',
      },
      {
        evidence_id: 'ev-02',
        source_ref: 'Cell_Tower_Dump_ChandniChowk.csv',
        support_type: 'TOWER_DUMP',
      },
    ],
    created_at: '2026-08-14T11:00:00Z',
  },

  'pred-001': {
    relationship_id: 'pred-001',
    case_id: DEMO_CASE_ID,
    source_entity: {
      entity_id: 'ent-person-001',
      canonical_name: 'Rajesh Sharma',
      entity_type: 'PERSON',
    },
    target_entity: {
      entity_id: 'ent-person-003',
      canonical_name: 'Vikram Verma',
      entity_type: 'PERSON',
    },
    type: 'CONTACTED',
    status: 'INFERRED',
    confidence_score: 0.82,
    is_predicted: true,
    evidence_citations: [
      {
        evidence_id: 'ev-pred-01',
        source_ref: 'GATv2_Link_Prediction_Run_8819',
        support_type: 'MODEL_PREDICTION',
      },
    ],
    created_at: '2026-08-14T12:00:00Z',
  },
};

export const DEMO_EVIDENCE_SPANS: Record<string, ProvenanceSpan> = {
  'ev-01': {
    chunk_id: 'chk-02',
    document_id: 'doc-cdr-01',
    file_name: 'CDR_Export_9811XXXX54_Aug2026.csv',
    version_hash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    page_number: 1,
    character_start: 12,
    character_end: 98,
    source_ref: 'CDR_Export_9811XXXX54_Aug2026.csv:row#42',
    support_type: 'CDR_ROW',
    snippet: 'Record #42: MSISDN +91 9811XXXX54 -> +91 9872XXXX19, Duration 342s, Timestamp 2026-08-04 18:42:10 IST, BTS-DEL-0491.',
  },
  'ev-pred-01': {
    chunk_id: null,
    document_id: null,
    file_name: 'GATv2 Graph Neural Network Model Run #8819',
    version_hash: 'sha256:model-gatv2-chkpt-20260814',
    page_number: null,
    character_start: null,
    character_end: null,
    source_ref: 'Agent 3 GATv2 Inference Engine',
    support_type: 'PREDICTED_LINK',
    snippet: 'Latent link candidate generated from high 2-hop topological proximity, coincident financial routing to ICICI-XXXX4410, and collocated BTS towers.',
  },
};
