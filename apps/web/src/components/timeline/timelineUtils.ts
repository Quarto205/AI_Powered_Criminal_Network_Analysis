/**
 * SIH26189 — Timeline Pure Utilities & Filtering Pipeline
 * Source: docs/contracts/08_UI_DATA_CONTRACT.md
 * 
 * Rules:
 * 1. Zero side effects: never mutate the source event array or source timestamps.
 * 2. Strict UTC/ISO date normalization for HTML date inputs to avoid timezone shifts.
 * 3. Temporal incomplete-data policy: events flagged with has_incomplete_timestamp
 *    are never silently dropped or fabricated.
 * 4. Empty selection in channel or type filters matches all items.
 */

import {
  TimelineEvent,
  TimelineFilterState,
  ChannelType,
  EventType,
  TimeBounds
} from '../../types/timeline';

/**
 * Safely converts an ISO timestamp to HTML date input format (YYYY-MM-DD)
 */
export function toDateInputValue(isoString: string): string {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return '';
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Safely converts an HTML date input format (YYYY-MM-DD) to ISO timestamp
 */
export function fromDateInputValue(dateString: string, isEndOfDay = false): string {
  if (!dateString) return '';
  if (isEndOfDay) {
    return `${dateString}T23:59:59.999Z`;
  }
  return `${dateString}T00:00:00.000Z`;
}

/**
 * Enforces start <= end boundary constraint without losing valid state
 */
export function clampDateRange(
  newStartDate: string,
  newEndDate: string,
  changedField: 'start' | 'end'
): { startDate: string; endDate: string } {
  const startTime = new Date(newStartDate).getTime();
  const endTime = new Date(newEndDate).getTime();

  if (isNaN(startTime) || isNaN(endTime)) {
    return { startDate: newStartDate, endDate: newEndDate };
  }

  if (startTime > endTime) {
    if (changedField === 'start') {
      // Pushed start beyond end -> move end to match start
      return { startDate: newStartDate, endDate: newStartDate };
    } else {
      // Pushed end before start -> move start to match end
      return { startDate: newEndDate, endDate: newEndDate };
    }
  }

  return { startDate: newStartDate, endDate: newEndDate };
}

/**
 * Determines if an event falls inside the active date window.
 * Invariant: Events with metadata.has_incomplete_timestamp === true are ALWAYS
 * preserved so that incomplete investigation data is flagged, not dropped.
 */
export function isEventWithinRange(
  event: TimelineEvent,
  startDateIso: string,
  endDateIso: string
): boolean {
  if (event.metadata?.has_incomplete_timestamp === true) {
    return true;
  }

  const eventTime = new Date(event.timestamp).getTime();
  const startTime = new Date(startDateIso).getTime();
  const endTime = new Date(endDateIso).getTime();

  if (isNaN(eventTime)) return true; // keep resilient
  if (!isNaN(startTime) && eventTime < startTime) return false;
  if (!isNaN(endTime) && eventTime > endTime) return false;

  return true;
}

/**
 * Channel filter check (empty selection => match all)
 */
export function eventMatchesChannelFilter(
  event: TimelineEvent,
  selectedChannels: ChannelType[]
): boolean {
  if (!selectedChannels || selectedChannels.length === 0) {
    return true;
  }
  return selectedChannels.includes(event.channel);
}

/**
 * Event type filter check (empty selection => match all)
 */
export function eventMatchesTypeFilter(
  event: TimelineEvent,
  selectedTypes: EventType[]
): boolean {
  if (!selectedTypes || selectedTypes.length === 0) {
    return true;
  }
  return selectedTypes.includes(event.event_type);
}

/**
 * Pure chronological sorting (ascending: oldest to newest).
 * Never mutates source array.
 */
export function sortTimelineEvents(events: readonly TimelineEvent[]): TimelineEvent[] {
  return [...events].sort((a, b) => {
    const timeA = new Date(a.timestamp).getTime();
    const timeB = new Date(b.timestamp).getTime();
    if (isNaN(timeA)) return 1;
    if (isNaN(timeB)) return -1;
    return timeA - timeB;
  });
}

/**
 * Master pure filter pipeline for timeline events
 */
export function filterTimelineEvents(
  events: readonly TimelineEvent[],
  filterState: TimelineFilterState
): TimelineEvent[] {
  if (!events) return [];

  const filtered = events.filter((event) => {
    // 1. Channel Filter
    if (!eventMatchesChannelFilter(event, filterState.selectedChannels)) {
      return false;
    }

    // 2. Event Type Filter
    if (!eventMatchesTypeFilter(event, filterState.selectedTypes)) {
      return false;
    }

    // 3. Date Range Filter
    if (!isEventWithinRange(event, filterState.startDate, filterState.endDate)) {
      return false;
    }

    return true;
  });

  return sortTimelineEvents(filtered);
}

/**
 * Channel iconography and text glyph mapping
 */
export const CHANNEL_ICONS: Record<ChannelType, string> = {
  CALL: '📞',
  SMS: '💬',
  WHATSAPP: '📱',
  BANK_TRANSFER: '🏦',
  UPI: '⇄',
  FIR_LOG: '📋',
  TOWER_PING: '📡'
};

/**
 * Default initial filter state derived from TimeBounds
 */
export function createDefaultFilterState(timeBounds: TimeBounds): TimelineFilterState {
  return {
    startDate: timeBounds.earliest,
    endDate: timeBounds.latest,
    selectedChannels: [],
    selectedTypes: []
  };
}

/**
 * Pure derived graph synchronization:
 * Composes timeline visibility constraints with existing graph data.
 * - Edges associated with timeline events are hidden if all associated events are filtered out.
 * - Edges with no timeline association remain unaffected.
 * - Strict edge endpoint integrity is preserved.
 * - Never mutates source graph data.
 */
export function applyTimelineToGraph(
  graphData: { nodes: any[]; edges: any[] },
  allEvents: readonly TimelineEvent[],
  visibleEvents: readonly TimelineEvent[]
): { nodes: any[]; edges: any[] } {
  if (!graphData || !graphData.edges) {
    return graphData;
  }

  // Set of entity pairs that have at least one timeline event
  const allEventPairs = new Set<string>();
  for (const ev of allEvents) {
    if (ev.source_entity_id && ev.target_entity_id) {
      allEventPairs.add(`${ev.source_entity_id}|${ev.target_entity_id}`);
      allEventPairs.add(`${ev.target_entity_id}|${ev.source_entity_id}`);
    }
  }

  // Set of entity pairs that are currently visible under active timeline filters
  const visibleEventPairs = new Set<string>();
  for (const ev of visibleEvents) {
    if (ev.source_entity_id && ev.target_entity_id) {
      visibleEventPairs.add(`${ev.source_entity_id}|${ev.target_entity_id}`);
      visibleEventPairs.add(`${ev.target_entity_id}|${ev.source_entity_id}`);
    }
  }

  const filteredEdges = graphData.edges.filter((edge) => {
    if (!edge.data) return false;
    const pairKey = `${edge.data.source}|${edge.data.target}`;
    const reversePairKey = `${edge.data.target}|${edge.data.source}`;
    const isAssociated = allEventPairs.has(pairKey) || allEventPairs.has(reversePairKey);

    if (isAssociated) {
      return visibleEventPairs.has(pairKey) || visibleEventPairs.has(reversePairKey);
    }
    return true;
  });

  const validNodeIds = new Set(graphData.nodes.map((n) => n.data?.id));
  const safeEdges = filteredEdges.filter(
    (e) => validNodeIds.has(e.data?.source) && validNodeIds.has(e.data?.target)
  );

  return {
    nodes: graphData.nodes,
    edges: safeEdges
  };
}

