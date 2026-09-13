import React, { useMemo } from 'react';
import {
  TimelineEvent,
  TimelineFilterState,
  TimeBounds
} from '../../types/timeline';
import { TimelineScrubber } from './TimelineScrubber';
import { filterTimelineEvents, CHANNEL_ICONS } from './timelineUtils';

export interface TimelineViewProps {
  events: TimelineEvent[];
  timeBounds: TimeBounds;
  filterState: TimelineFilterState;
  onFilterChange: (nextFilterState: TimelineFilterState) => void;
  onResetFilters: () => void;
  onSelectEvent?: (event: TimelineEvent) => void;
  selectedEventId?: string | null;
}

export const TimelineView: React.FC<TimelineViewProps> = ({
  events,
  timeBounds,
  filterState,
  onFilterChange,
  onResetFilters,
  onSelectEvent,
  selectedEventId
}) => {
  const visibleEvents = useMemo(() => {
    return filterTimelineEvents(events, filterState);
  }, [events, filterState]);

  return (
    <div className="timeline-view-container" aria-label="Interactive Chronological Timeline">
      <TimelineScrubber
        timeBounds={timeBounds}
        filterState={filterState}
        onFilterChange={onFilterChange}
        onResetFilters={onResetFilters}
        totalEventsCount={events.length}
        visibleEventsCount={visibleEvents.length}
      />

      <section
        className="timeline-stream-container"
        aria-label="Chronological Event Stream"
        tabIndex={0}
      >
        {events.length === 0 ? (
          <div className="timeline-empty-state" role="status">
            <p className="empty-text">No timeline events recorded for this case.</p>
          </div>
        ) : visibleEvents.length === 0 ? (
          <div className="timeline-empty-state" role="status">
            <p className="empty-text">
              No events found matching the selected temporal range or category filters.
            </p>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onResetFilters}
              style={{ marginTop: '12px' }}
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="timeline-event-list" role="feed" aria-label="Event sequence">
            {visibleEvents.map((event) => {
              const isSelected = selectedEventId === event.event_id;
              const isIncomplete = Boolean(event.metadata?.has_incomplete_timestamp);

              return (
                <article
                  key={event.event_id}
                  className={`timeline-event-card ${isSelected ? 'timeline-event-card-selected' : ''}`}
                  aria-label={`Event: ${event.summary}`}
                >
                  <div className="event-card-header">
                    <div className="event-badges-row">
                      <span className="event-channel-badge">
                        <span aria-hidden="true">{CHANNEL_ICONS[event.channel]}</span> {event.channel}
                      </span>
                      <span className="event-type-badge">
                        {event.event_type}
                      </span>
                      {isIncomplete && (
                        <span
                          className="event-incomplete-badge"
                          role="status"
                          aria-label="Insufficient temporal data"
                        >
                          [INSUFFICIENT TEMPORAL DATA]
                        </span>
                      )}
                    </div>
                    <time className="event-timestamp" dateTime={event.timestamp}>
                      {event.timestamp}
                    </time>
                  </div>

                  <p className="event-summary">{event.summary}</p>

                  <div className="event-card-footer">
                    <div className="event-participants">
                      {event.source_label && (
                        <span className="participant-tag">
                          <strong>Source:</strong> {event.source_label}
                        </span>
                      )}
                      {event.target_label && (
                        <span className="participant-tag">
                          <strong>Target:</strong> {event.target_label}
                        </span>
                      )}
                      {event.metadata?.amount !== undefined && (
                        <span className="metadata-tag">
                          <strong>Amount:</strong> {event.metadata.currency || 'INR'} {event.metadata.amount.toLocaleString()}
                        </span>
                      )}
                      {event.metadata?.duration_seconds !== undefined && (
                        <span className="metadata-tag">
                          <strong>Duration:</strong> {event.metadata.duration_seconds}s
                        </span>
                      )}
                      {event.metadata?.location_label && (
                        <span className="metadata-tag">
                          <strong>Location:</strong> {event.metadata.location_label}
                        </span>
                      )}
                    </div>

                    <button
                      type="button"
                      className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'} event-select-btn`}
                      onClick={() => onSelectEvent?.(event)}
                      aria-pressed={isSelected}
                      aria-label={`Select event and inspect associated entities: ${event.summary}`}
                    >
                      {isSelected ? 'Selected' : 'Inspect in Graph'}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};
