/**
 * Canonical Analysis, Priority Scores & Pattern Alerts Schemas for SIH26189.
 * Strictly adheres to 05_AI_CONTRACTS.md, 04_API_SPEC.md,
 * and main/backend/schemas/evidence_analysis.py.
 * Non-accusatory terminology: Priority Ranking, Investigative Lead, Pattern Alert.
 */

import { UUID } from './common';

export const AnalysisPipelines = {
  SNA: 'SNA',
  PATTERN_MOTIFS: 'PATTERN_MOTIFS',
  GAT_LINK_PREDICTION: 'GAT_LINK_PREDICTION',
} as const;

export type AnalysisPipeline = (typeof AnalysisPipelines)[keyof typeof AnalysisPipelines];

export interface AnalysisParameters {
  time_window_days?: number;
  min_confidence_threshold?: number;
}

export interface AnalysisTriggerRequest {
  pipelines: string[];
  parameters?: AnalysisParameters;
}

export interface AnalysisTriggerResponse {
  run_id: UUID;
  case_id: UUID;
  status: string;
  pipelines: string[];
  triggered_at: string;
}

export interface AnalysisRunDetailResponse {
  run_id: UUID;
  case_id?: UUID | null;
  model_name: string;
  version: string;
  task_type: string;
  status: string;
  input_snapshot_checksum: string;
  created_at: string;
}

export interface ScoreItem {
  score_id: UUID;
  entity_id: UUID;
  canonical_name: string;
  entity_type: string;
  score_type: string;
  value: number;
  features_summary?: {
    degree?: number;
    betweenness?: number;
    pagerank?: number;
    community_id?: number;
    reasoning?: string;
    [key: string]: unknown;
  } | null;
}

export interface CaseScoresResponse {
  case_id: UUID;
  scores: ScoreItem[];
  total: number;
}

export interface AlertItem {
  alert_id: UUID;
  case_id: UUID;
  alert_type: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  rule_id: string;
  status: 'NEW' | 'REVIEWED' | string;
  contributing_entities: Array<{
    entity_id: UUID;
    canonical_name: string;
    role?: string;
  }> | Record<string, unknown>;
  description?: string;
}

export interface CaseAlertsResponse {
  case_id: UUID;
  alerts: AlertItem[];
  total: number;
}
