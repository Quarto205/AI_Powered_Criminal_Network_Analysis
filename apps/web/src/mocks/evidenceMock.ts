/**
 * SIH26189 — Deterministic Evidence & Provenance Mock Fixtures
 * Strictly adheres to 01_SHARED_TYPES.md, 02_DATABASE_SCHEMA.md, 04_API_SPEC.md,
 * 05_AI_CONTRACTS.md, and contracts.ts.
 *
 * NOTE: For frontend development and testing only.
 * Demonstrates:
 * - Source-backed evidence with character-level provenance spans
 * - Drill-down data for EvidencePanel and EntityDrawer
 * - Ambiguous entity-resolution candidates for EntityReviewQueue
 */

import {
  EntityDetailResponse,
  RelationshipDetailResponse,
  EntityReviewItem,
  EntityReviewQueueResponse,
  DocumentListItem,
  EntityTypes,
  RelationshipTypes,
  RelationshipStates,
  ReviewStates,
  ProvenanceSpan,
} from '../types/contracts';
import { MOCK_CASE_ID } from './caseMock';

export const MOCK_PROVENANCE_FIR: ProvenanceSpan = {
  chunk_id: 'chk-001-fir-p2',
  document_id: 'doc-001-fir-42-2024',
  file_name: 'FIR_42_2026_Special_Cell.pdf',
  version_hash: 'sha256-a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0',
  page_number: 2,
  character_start: 340,
  character_end: 495,
  source_ref: 'FIR_42_2026_Special_Cell.pdf:p2:340-495',
  support_type: 'SUPPORTS',
  snippet:
    '...intercepted communications indicated Tariq Khan coordinating transit vehicles and instructing cash drops near Jamia Nagar transit points...',
};

export const MOCK_PROVENANCE_CDR: ProvenanceSpan = {
  chunk_id: 'chk-002-cdr-row819',
  document_id: 'doc-002-cdr-dump-feb',
  file_name: 'CDR_Dump_Feb2026_Intercepts.csv',
  version_hash: 'sha256-b2c3d4e5f6a7890123456789abcdef0123456789abcdef0123456789abcdef1',
  page_number: 1,
  character_start: 8190,
  character_end: 8320,
  source_ref: 'CDR_Dump_Feb2026_Intercepts.csv:row819',
  support_type: 'SUPPORTS',
  snippet:
    '2026-02-12 22:18:14,98110XXXXX,98731XXXXX,CALL_OUT,412s,CELL_TOWER_JAMIA_N_41',
};

export const MOCK_PROVENANCE_BANK: ProvenanceSpan = {
  chunk_id: 'chk-003-bank-p5',
  document_id: 'doc-003-bank-stmt-hdfc',
  file_name: 'HDFC_Statement_Account_4819.pdf',
  version_hash: 'sha256-c3d4e5f6a7b890123456789abcdef0123456789abcdef0123456789abcdef2',
  page_number: 5,
  character_start: 1240,
  character_end: 1390,
  source_ref: 'HDFC_Statement_Account_4819.pdf:p5:1240-1390',
  support_type: 'SUPPORTS',
  snippet:
    '13-FEB-2026 NEFT/RTGS CR-091823901 TO ICICI AC 9102 RAJESH GUPTA AMT: 4,50,000.00 REF: TRF-CONSULTANCY',
};

export const MOCK_ENTITY_DETAIL_TARIQ: EntityDetailResponse = {
  entity_id: 'node-person-1',
  case_id: MOCK_CASE_ID,
  canonical_name: 'Tariq Khan',
  entity_type: EntityTypes.PERSON,
  status: 'UNDER_SURVEILLANCE',
  aliases: [
    {
      alias_id: 'alias-001',
      alias_text: 'Bhaijaan',
      source_ref: 'FIR_42_2026_Special_Cell.pdf:p1',
    },
    {
      alias_id: 'alias-002',
      alias_text: 'TK North',
      source_ref: 'Informant_Debrief_Note_03.pdf:p1',
    },
  ],
  identifiers: [
    {
      identifier_id: 'ident-001',
      type: 'PHONE_NUMBER',
      masked_value: '+91 98110 •••••',
      value_policy: 'MASKED_PII',
    },
    {
      identifier_id: 'ident-002',
      type: 'VEHICLE_PLATE',
      masked_value: 'DL 01 AB ••••',
      value_policy: 'NORMALIZED_HASH',
    },
  ],
  risk_score: {
    score_id: 'score-001-tariq',
    score_type: 'INVESTIGATIVE_PRIORITY',
    value: 0.89,
    features_summary: {
      degree: 4,
      betweenness: 0.62,
      pagerank: 0.084,
      community_id: 1,
      temporal_recency: 0.95,
      alert_count: 2,
      reasoning:
        'High degree and betweenness linking communication cluster to banking accounts with recent multi-signal activity.',
    },
  },
  provenance_spans: [MOCK_PROVENANCE_FIR, MOCK_PROVENANCE_CDR],
  created_at: '2026-02-15T10:00:00Z',
};

export const MOCK_ENTITY_DETAIL_VIKRAM: EntityDetailResponse = {
  entity_id: 'node-person-2',
  case_id: MOCK_CASE_ID,
  canonical_name: 'Vikram Sharma',
  entity_type: EntityTypes.PERSON,
  status: 'IDENTIFIED',
  aliases: [
    {
      alias_id: 'alias-003',
      alias_text: 'Vicky Delhi',
      source_ref: 'Interrogation_Excerpt_Feb.pdf:p3',
    },
  ],
  identifiers: [
    {
      identifier_id: 'ident-003',
      type: 'PHONE_NUMBER',
      masked_value: '+91 98731 •••••',
      value_policy: 'MASKED_PII',
    },
  ],
  risk_score: {
    score_id: 'score-002-vikram',
    score_type: 'INVESTIGATIVE_PRIORITY',
    value: 0.68,
    features_summary: {
      degree: 3,
      betweenness: 0.35,
      pagerank: 0.045,
      community_id: 1,
      temporal_recency: 0.88,
      alert_count: 1,
      reasoning:
        'Acts as secondary communication bridge with verified burner phone associations.',
    },
  },
  provenance_spans: [MOCK_PROVENANCE_CDR],
  created_at: '2026-02-15T10:30:00Z',
};

export const MOCK_RELATIONSHIP_DETAIL_FACTUAL: RelationshipDetailResponse = {
  relationship_id: 'rel-0003-fact-comm-phone1-phone2',
  case_id: MOCK_CASE_ID,
  source_entity: {
    entity_id: 'node-phone-1',
    canonical_name: '+91 98110 XXXXX',
    entity_type: EntityTypes.PHONE,
  },
  target_entity: {
    entity_id: 'node-phone-2',
    canonical_name: '+91 98731 XXXXX',
    entity_type: EntityTypes.PHONE,
  },
  type: RelationshipTypes.COMMUNICATED_WITH,
  status: RelationshipStates.CORROBORATED,
  confidence_score: 0.92,
  is_predicted: false,
  style_line: 'solid',
  evidence_citations: [
    {
      evidence_id: 'ev-004',
      source_ref: 'CDR_Dump_Feb2026_Intercepts.csv:row819',
      support_type: 'SUPPORTS',
      snippet: 'Outgoing call duration 412s on 2026-02-12 22:18:14 UTC',
      document_id: 'doc-002-cdr-dump-feb',
      file_name: 'CDR_Dump_Feb2026_Intercepts.csv',
      page_number: 1,
    },
    {
      evidence_id: 'ev-005',
      source_ref: 'CDR_Dump_Feb2026_Intercepts.csv:row942',
      support_type: 'SUPPORTS',
      snippet: 'Incoming SMS exchange on 2026-02-13 08:10:05 UTC',
      document_id: 'doc-002-cdr-dump-feb',
      file_name: 'CDR_Dump_Feb2026_Intercepts.csv',
      page_number: 1,
    },
  ],
  factual_evidence: {
    relationship_id: 'rel-0003-fact-comm-phone1-phone2',
    status: 'CORROBORATED',
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
  created_at: '2026-02-15T11:00:00Z',
};

export const MOCK_RELATIONSHIP_DETAIL_PREDICTED: RelationshipDetailResponse = {
  relationship_id: 'pred-001-gat-tariq-rajesh',
  case_id: MOCK_CASE_ID,
  source_entity: {
    entity_id: 'node-person-1',
    canonical_name: 'Tariq Khan',
    entity_type: EntityTypes.PERSON,
  },
  target_entity: {
    entity_id: 'node-person-3',
    canonical_name: 'Rajesh Gupta',
    entity_type: EntityTypes.PERSON,
  },
  type: RelationshipTypes.KNOWS,
  status: RelationshipStates.INFERRED,
  confidence_score: 0.84,
  is_predicted: true,
  style_line: 'dashed',
  evidence_citations: [],
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
  created_at: '2026-02-15T12:00:00Z',
};

/**
 * Section 13: Entity Review Queue Mock Data
 * Realistic ambiguous entity resolution candidates routed for supervisor review.
 */
export const MOCK_ENTITY_REVIEW_ITEMS: EntityReviewItem[] = [
  {
    review_id: 'rev-001-vikram-s',
    case_id: MOCK_CASE_ID,
    target_type: 'ENTITY_RESOLUTION',
    source_mention: {
      temp_id: 'mention-tmp-819',
      entity_type: EntityTypes.PERSON,
      extracted_text: 'Vikram S.',
      character_start: 1042,
      character_end: 1051,
      document_id: 'doc-001-fir-42-2024',
      chunk_id: 'chk-001-fir-p3',
      file_name: 'FIR_42_2026_Special_Cell.pdf',
    },
    candidate_entity: {
      canonical_entity_id: 'node-person-2',
      canonical_name: 'Vikram Sharma',
      entity_type: EntityTypes.PERSON,
      existing_identifiers: ['+91 98731 •••••'],
      existing_aliases: ['Vicky Delhi'],
    },
    match_metadata: {
      similarity_score: 0.78,
      match_algorithm: 'JARO_WINKLER',
      match_reasons: [
        'Partial surname match (S. -> Sharma)',
        'Mentioned in context with co-suspect phone +91 98731 XXXXX',
      ],
      threshold_applied: 0.85,
    },
    review_status: ReviewStates.NEW,
    provenance: {
      chunk_id: 'chk-001-fir-p3',
      document_id: 'doc-001-fir-42-2024',
      file_name: 'FIR_42_2026_Special_Cell.pdf',
      page_number: 3,
      character_start: 1042,
      character_end: 1051,
      source_ref: 'FIR_42_2026_Special_Cell.pdf:p3:1042-1051',
      support_type: 'SUPPORTS',
      snippet: '...witness stated that Vikram S. was accompanied by two associates carrying parcel bags...',
    },
    created_at: '2026-02-15T12:30:00Z',
  },
  {
    review_id: 'rev-002-t-khan',
    case_id: MOCK_CASE_ID,
    target_type: 'ENTITY_RESOLUTION',
    source_mention: {
      temp_id: 'mention-tmp-820',
      entity_type: EntityTypes.PERSON,
      extracted_text: 'T. Khan',
      character_start: 512,
      character_end: 519,
      document_id: 'doc-004-diary-notes',
      chunk_id: 'chk-004-diary-p1',
      file_name: 'Seized_Diary_Excerpts.pdf',
    },
    candidate_entity: {
      canonical_entity_id: 'node-person-1',
      canonical_name: 'Tariq Khan',
      entity_type: EntityTypes.PERSON,
      existing_identifiers: ['+91 98110 •••••', 'DL 01 AB ••••'],
      existing_aliases: ['Bhaijaan', 'TK'],
    },
    match_metadata: {
      similarity_score: 0.82,
      match_algorithm: 'LEVENSHTEIN',
      match_reasons: [
        'Initial and surname alignment',
        'Co-located entry with Jamia Nagar cash delivery address',
      ],
      threshold_applied: 0.85,
    },
    review_status: ReviewStates.REVIEWED,
    decision: 'CONFIRM',
    reviewer_id: '33333333-4444-5555-6666-777777777777',
    reviewer_notes: 'Confirmed by ACP Singh based on diary address corroboration.',
    provenance: {
      chunk_id: 'chk-004-diary-p1',
      document_id: 'doc-004-diary-notes',
      file_name: 'Seized_Diary_Excerpts.pdf',
      page_number: 1,
      character_start: 512,
      character_end: 519,
      source_ref: 'Seized_Diary_Excerpts.pdf:p1:512-519',
      support_type: 'SUPPORTS',
      snippet: '...entry dated 11 Feb: handover package to T. Khan at Jamia tea stall...',
    },
    created_at: '2026-02-15T12:45:00Z',
  },
  {
    review_id: 'rev-003-rk-gupta',
    case_id: MOCK_CASE_ID,
    target_type: 'ENTITY_RESOLUTION',
    source_mention: {
      temp_id: 'mention-tmp-821',
      entity_type: EntityTypes.PERSON,
      extracted_text: 'R. K. Gupta',
      character_start: 890,
      character_end: 901,
      document_id: 'doc-003-bank-stmt-hdfc',
      chunk_id: 'chk-003-bank-p5',
      file_name: 'HDFC_Statement_Account_4819.pdf',
    },
    candidate_entity: {
      canonical_entity_id: 'node-person-3',
      canonical_name: 'Rajesh Gupta',
      entity_type: EntityTypes.PERSON,
      existing_identifiers: ['ICICI-••••-9102'],
      existing_aliases: [],
    },
    match_metadata: {
      similarity_score: 0.71,
      match_algorithm: 'COMPOSITE',
      match_reasons: [
        'Matching surname Gupta with shared middle initial',
        'Direct beneficiary on NEFT transaction record',
      ],
      threshold_applied: 0.85,
    },
    review_status: ReviewStates.NEW,
    provenance: {
      chunk_id: 'chk-003-bank-p5',
      document_id: 'doc-003-bank-stmt-hdfc',
      file_name: 'HDFC_Statement_Account_4819.pdf',
      page_number: 5,
      character_start: 890,
      character_end: 901,
      source_ref: 'HDFC_Statement_Account_4819.pdf:p5:890-901',
      support_type: 'SUPPORTS',
      snippet: '...beneficiary name listed as R. K. Gupta in transaction ledger memo...',
    },
    created_at: '2026-02-15T13:00:00Z',
  },
];

export const MOCK_ENTITY_REVIEW_QUEUE: EntityReviewQueueResponse = {
  reviews: MOCK_ENTITY_REVIEW_ITEMS,
  total: MOCK_ENTITY_REVIEW_ITEMS.length,
  pending_count: MOCK_ENTITY_REVIEW_ITEMS.filter((r) => r.review_status === ReviewStates.NEW).length,
};

export const MOCK_DOCUMENTS: DocumentListItem[] = [
  {
    document_id: 'doc-001-fir-42-2024',
    case_id: MOCK_CASE_ID,
    file_type: 'application/pdf',
    file_hash: 'sha256-a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0',
    status: 'ACCEPTED',
    created_at: '2026-02-15T09:40:00Z',
  },
  {
    document_id: 'doc-002-cdr-dump-feb',
    case_id: MOCK_CASE_ID,
    file_type: 'text/csv',
    file_hash: 'sha256-b2c3d4e5f6a7890123456789abcdef0123456789abcdef0123456789abcdef1',
    status: 'ACCEPTED',
    created_at: '2026-02-15T09:45:00Z',
  },
  {
    document_id: 'doc-003-bank-stmt-hdfc',
    case_id: MOCK_CASE_ID,
    file_type: 'application/pdf',
    file_hash: 'sha256-c3d4e5f6a7b890123456789abcdef0123456789abcdef0123456789abcdef2',
    status: 'ACCEPTED',
    created_at: '2026-02-15T09:50:00Z',
  },
  {
    document_id: 'doc-004-diary-notes',
    case_id: MOCK_CASE_ID,
    file_type: 'application/pdf',
    file_hash: 'sha256-d4e5f6a7b8c90123456789abcdef0123456789abcdef0123456789abcdef3',
    status: 'ACCEPTED',
    created_at: '2026-02-15T09:55:00Z',
  },
];
