/**
 * SIH26189 — Interactive Timeline & Temporal Scrubber Contracts
 * Source: docs/contracts/01_SHARED_TYPES.md, 04_API_SPEC.md, 08_UI_DATA_CONTRACT.md
 * 
 * Rules:
 * 1. Strictly typed chronological event stream representations.
 * 2. Node & edge identities must use valid UUID-v4 format.
 * 3. Reuses shared ApiResponse envelope from types/shell.ts.
 * 4. Temporal incomplete-data policy: metadata.has_incomplete_timestamp is preserved.
 */

import { ApiResponse, UUID } from './shell';

/**
 * Canonical timeline event categories
 */
export type EventType =
  | 'COMMUNICATION'
  | 'TRANSACTION'
  | 'MOVEMENT'
  | 'INCIDENT'
  | 'OBSERVATION';

/**
 * Ingestion and investigative observation channels
 */
export type ChannelType =
  | 'CALL'
  | 'SMS'
  | 'WHATSAPP'
  | 'BANK_TRANSFER'
  | 'UPI'
  | 'FIR_LOG'
  | 'TOWER_PING';

export const ALL_EVENT_TYPES: readonly EventType[] = [
  'COMMUNICATION',
  'TRANSACTION',
  'MOVEMENT',
  'INCIDENT',
  'OBSERVATION'
] as const;

export const ALL_CHANNEL_TYPES: readonly ChannelType[] = [
  'CALL',
  'SMS',
  'WHATSAPP',
  'BANK_TRANSFER',
  'UPI',
  'FIR_LOG',
  'TOWER_PING'
] as const;

/**
 * Flexible yet typed metadata for diverse investigative event types
 */
export interface TimelineEventMetadata {
  amount?: number;
  currency?: string;
  duration_seconds?: number;
  location_label?: string;
  has_incomplete_timestamp?: boolean;
  [key: string]: unknown;
}

/**
 * Canonical timeline event structure
 */
export interface TimelineEvent {
  event_id: UUID;
  event_type: EventType;
  channel: ChannelType;
  timestamp: string; // ISO 8601 (e.g. 2026-08-16T10:15:00Z)
  source_entity_id?: UUID;
  target_entity_id?: UUID;
  source_label?: string;
  target_label?: string;
  summary: string;
  metadata: TimelineEventMetadata;
}

/**
 * Declared temporal boundary envelope for the active case
 */
export interface TimeBounds {
  earliest: string; // ISO 8601
  latest: string;   // ISO 8601
}

/**
 * Payload envelope for GET /api/v1/cases/{case_id}/events
 */
export interface TimelinePayload {
  case_id: UUID;
  time_bounds: TimeBounds;
  total_events: number;
  events: TimelineEvent[];
}

/**
 * Presentation filter state for TimelineScrubber
 */
export interface TimelineFilterState {
  startDate: string; // ISO timestamp or YYYY-MM-DD
  endDate: string;   // ISO timestamp or YYYY-MM-DD
  selectedChannels: ChannelType[];
  selectedTypes: EventType[];
}

export type TimelineApiResponse = ApiResponse<TimelinePayload>;
