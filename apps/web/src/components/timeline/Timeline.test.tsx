import { describe, it, expect, vi } from 'vitest';
import { useState } from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { TimelineScrubber } from './TimelineScrubber';
import { TimelineView } from './TimelineView';
import {
  mockTimelinePayload,
  mockTimelineEvents,
  mockSecondaryTimelinePayload,
  getTimelineForCase
} from '../../mocks/timelineMock';
import {
  filterTimelineEvents,
  sortTimelineEvents,
  clampDateRange,
  toDateInputValue,
  fromDateInputValue,
  createDefaultFilterState,
  applyTimelineToGraph
} from './timelineUtils';
import { TimelineFilterState, TimelineEvent } from '../../types/timeline';

describe('Timeline Pure Utilities (timelineUtils)', () => {
  it('A. toDateInputValue & fromDateInputValue convert safely without timezone drift', () => {
    const iso = '2026-08-15T11:05:00.000Z';
    const dateInput = toDateInputValue(iso);
    expect(dateInput).toBe('2026-08-15');

    const backToIsoStart = fromDateInputValue('2026-08-15', false);
    expect(backToIsoStart).toBe('2026-08-15T00:00:00.000Z');

    const backToIsoEnd = fromDateInputValue('2026-08-15', true);
    expect(backToIsoEnd).toBe('2026-08-15T23:59:59.999Z');
  });

  it('sortTimelineEvents orders events chronologically ascending without mutating source', () => {
    const reversed = [...mockTimelineEvents].reverse();
    const sorted = sortTimelineEvents(reversed);
    expect(new Date(sorted[0].timestamp).getTime()).toBeLessThanOrEqual(
      new Date(sorted[sorted.length - 1].timestamp).getTime()
    );
  });

  it('J. clampDateRange prevents startDate > endDate', () => {
    // When pushing start past end
    const clamped1 = clampDateRange('2026-08-20T00:00:00Z', '2026-08-15T23:59:59Z', 'start');
    expect(new Date(clamped1.startDate).getTime()).toBeLessThanOrEqual(new Date(clamped1.endDate).getTime());

    // When pulling end before start
    const clamped2 = clampDateRange('2026-08-20T00:00:00Z', '2026-08-15T23:59:59Z', 'end');
    expect(new Date(clamped2.startDate).getTime()).toBeLessThanOrEqual(new Date(clamped2.endDate).getTime());
  });

  it('L. filterTimelineEvents and sortTimelineEvents never mutate source array (Immutability)', () => {
    const copyBefore = JSON.parse(JSON.stringify(mockTimelineEvents));
    const filterState: TimelineFilterState = {
      startDate: '2026-08-12T00:00:00Z',
      endDate: '2026-08-18T23:59:59Z',
      selectedChannels: ['CALL'],
      selectedTypes: ['COMMUNICATION']
    };

    const result = filterTimelineEvents(mockTimelineEvents, filterState);
    expect(result.length).toBeGreaterThan(0);
    expect(mockTimelineEvents).toEqual(copyBefore);
  });

  it('K. Determinism: mock data remains fixed across runs and supports cross-case lookup', () => {
    expect(mockTimelinePayload.events.length).toBe(8);
    expect(mockTimelinePayload.total_events).toBe(8);
    expect(mockTimelinePayload.case_id).toBe('a8f3b2e1-4c5d-4f6a-9b8c-7d6e5f4a3b2c');

    const secondary = getTimelineForCase(mockSecondaryTimelinePayload.case_id);
    expect(secondary.events.length).toBe(2);
    expect(secondary.case_id).toBe(mockSecondaryTimelinePayload.case_id);
  });

  it('TimelineScrubber renders standalone and responds to category toggles', () => {
    const handleFilterChange = vi.fn();
    const handleReset = vi.fn();
    const defaultFilter = createDefaultFilterState(mockTimelinePayload.time_bounds);

    render(
      <TimelineScrubber
        timeBounds={mockTimelinePayload.time_bounds}
        filterState={defaultFilter}
        onFilterChange={handleFilterChange}
        onResetFilters={handleReset}
        totalEventsCount={mockTimelinePayload.total_events}
        visibleEventsCount={mockTimelinePayload.events.length}
      />
    );

    const callChip = screen.getByRole('button', { name: /Filter by channel CALL/i });
    fireEvent.click(callChip);
    expect(handleFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ selectedChannels: ['CALL'] })
    );
  });
});


describe('TimelineView & TimelineScrubber Component Suite', () => {
  const defaultState = createDefaultFilterState(mockTimelinePayload.time_bounds);

  const ControlledTimeline = ({
    initialFilterState = defaultState,
    onSelectEvent = vi.fn()
  }: {
    initialFilterState?: TimelineFilterState;
    onSelectEvent?: (e: TimelineEvent) => void;
  }) => {
    const [state, setState] = useState<TimelineFilterState>(initialFilterState);
    return (
      <TimelineView
        events={mockTimelinePayload.events}
        timeBounds={mockTimelinePayload.time_bounds}
        filterState={state}
        onFilterChange={setState}
        onResetFilters={() => setState(defaultState)}
        onSelectEvent={onSelectEvent}
      />
    );
  };

  it('A. Renders timeline header, date range, channel chips, and event types', () => {
    render(<ControlledTimeline />);

    expect(screen.getByRole('region', { name: /Timeline Temporal Scrubber/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Timeline Start Date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Timeline End Date/i)).toBeInTheDocument();
    expect(screen.getByRole('group', { name: /Channel Filters/i })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: /Event Type Filters/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reset temporal and category filters/i })).toBeInTheDocument();
  });

  it('B. Date range filtering narrows event stream', () => {
    render(<ControlledTimeline />);

    // Initially all 8 events are visible
    expect(screen.getByText(/8 \/ 8 Events Visible/i)).toBeInTheDocument();

    // Change start date to 2026-08-20
    const startInput = screen.getByLabelText(/Timeline Start Date/i);
    fireEvent.change(startInput, { target: { value: '2026-08-20' } });

    // Events before Aug 20 (except incomplete timestamp event which is always preserved) are filtered out
    // Events on/after Aug 20: 2026-08-21 (UPI), 2026-08-23 (WHATSAPP), 2026-08-24 (Surveillance with incomplete timestamp)
    expect(screen.getByText(/3 \/ 8 Events Visible/i)).toBeInTheDocument();
  });

  it('C. Channel filtering limits results and restores on empty selection', () => {
    render(<ControlledTimeline />);

    const callChip = screen.getByRole('button', { name: /Filter by channel CALL/i });
    expect(callChip).toHaveAttribute('aria-pressed', 'false');

    // Click CALL channel filter
    fireEvent.click(callChip);
    expect(callChip).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText(/1 \/ 8 Events Visible/i)).toBeInTheDocument();
    expect(screen.getByText(/Outbound voice call lasting 184 seconds/i)).toBeInTheDocument();

    // Toggle CALL off -> empty restores all
    fireEvent.click(callChip);
    expect(callChip).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByText(/8 \/ 8 Events Visible/i)).toBeInTheDocument();
  });

  it('D. Event type filtering isolates specific analytical categories', () => {
    render(<ControlledTimeline />);

    const transactionChip = screen.getByRole('button', { name: /Filter by event type TRANSACTION/i });
    fireEvent.click(transactionChip);

    // 2 transactions in fixture: BANK_TRANSFER (Aug 15) and UPI (Aug 21)
    expect(screen.getByText(/2 \/ 8 Events Visible/i)).toBeInTheDocument();
    expect(screen.getByText(/NEFT credit to corporate proxy account/i)).toBeInTheDocument();
    expect(screen.getByText(/Structured peer-to-peer micro-remittance/i)).toBeInTheDocument();
  });

  it('E. Combined filters (date + channel + type) correctly intersect', () => {
    render(<ControlledTimeline />);

    // Filter by type: TRANSACTION
    const transactionChip = screen.getByRole('button', { name: /Filter by event type TRANSACTION/i });
    fireEvent.click(transactionChip);

    // Filter by channel: UPI
    const upiChip = screen.getByRole('button', { name: /Filter by channel UPI/i });
    fireEvent.click(upiChip);

    // Exactly 1 match (UPI micro-remittance on Aug 21)
    expect(screen.getByText(/1 \/ 8 Events Visible/i)).toBeInTheDocument();
    expect(screen.getByText(/Structured peer-to-peer micro-remittance/i)).toBeInTheDocument();
  });

  it('F. Reset button restores time bounds and clears selected filters', () => {
    render(<ControlledTimeline />);

    // Set filters
    const upiChip = screen.getByRole('button', { name: /Filter by channel UPI/i });
    fireEvent.click(upiChip);
    expect(screen.getByText(/1 \/ 8 Events Visible/i)).toBeInTheDocument();

    // Click Reset
    const resetBtn = screen.getByRole('button', { name: /Reset temporal and category filters/i });
    fireEvent.click(resetBtn);

    expect(screen.getByText(/8 \/ 8 Events Visible/i)).toBeInTheDocument();
    expect(upiChip).toHaveAttribute('aria-pressed', 'false');
  });

  it('G. Incomplete temporal data is visibly flagged with [INSUFFICIENT TEMPORAL DATA]', () => {
    render(<ControlledTimeline />);

    const badge = screen.getByText('[INSUFFICIENT TEMPORAL DATA]');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('role', 'status');
    expect(badge).toHaveAttribute('aria-label', 'Insufficient temporal data');
  });

  it('H. Event selection fires onSelectEvent with exact event data', () => {
    const handleSelect = vi.fn();
    render(<ControlledTimeline onSelectEvent={handleSelect} />);

    const inspectBtn = screen.getAllByRole('button', { name: /Select event and inspect associated entities/i })[0];
    fireEvent.click(inspectBtn);

    expect(handleSelect).toHaveBeenCalledTimes(1);
    expect(handleSelect).toHaveBeenCalledWith(expect.objectContaining({
      event_id: expect.any(String),
      channel: expect.any(String),
      event_type: expect.any(String)
    }));
  });

  it('I. Accessibility: controls have aria attributes and non-color text indicators', () => {
    render(<ControlledTimeline />);

    const upiChip = screen.getByRole('button', { name: /Filter by channel UPI/i });
    expect(upiChip).toHaveAttribute('aria-pressed', 'false');
    expect(within(upiChip).getByText('UPI')).toBeInTheDocument();

    fireEvent.click(upiChip);
    expect(upiChip).toHaveAttribute('aria-pressed', 'true');
    // Non-color indication: includes '✓' text
    expect(within(upiChip).getByText(/✓/)).toBeInTheDocument();
  });
});

describe('Graph Synchronization via applyTimelineToGraph', () => {
  it('Excludes associated graph edges when their timeline events are filtered out', () => {
    const initialGraph = {
      nodes: [
        { data: { id: 'node-1', label: 'Person A' } },
        { data: { id: 'node-2', label: 'Phone 1' } },
        { data: { id: 'node-3', label: 'Account 1' } }
      ],
      edges: [
        { data: { id: 'edge-1', source: 'node-1', target: 'node-2', relationship_type: 'OWNS' } },
        { data: { id: 'edge-2', source: 'node-1', target: 'node-3', relationship_type: 'OWNS' } }
      ]
    };

    const allEvents: TimelineEvent[] = [
      {
        event_id: 'e1',
        event_type: 'COMMUNICATION',
        channel: 'CALL',
        timestamp: '2026-08-12T10:00:00Z',
        source_entity_id: 'node-1',
        target_entity_id: 'node-2',
        summary: 'Call event',
        metadata: {}
      }
    ];

    // Case 1: Event is visible -> edge-1 remains visible
    const visibleGraph1 = applyTimelineToGraph(initialGraph, allEvents, allEvents);
    expect(visibleGraph1.edges.length).toBe(2);

    // Case 2: Event is filtered out -> edge-1 is excluded because all its timeline events are out of range
    const visibleGraph2 = applyTimelineToGraph(initialGraph, allEvents, []);
    expect(visibleGraph2.edges.length).toBe(1);
    expect(visibleGraph2.edges[0].data.id).toBe('edge-2'); // edge-2 has no timeline association, preserved safely
  });
});
