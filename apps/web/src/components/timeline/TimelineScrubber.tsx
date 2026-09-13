import React from 'react';
import {
  TimeBounds,
  TimelineFilterState,
  ALL_CHANNEL_TYPES,
  ALL_EVENT_TYPES,
  ChannelType,
  EventType
} from '../../types/timeline';
import {
  toDateInputValue,
  fromDateInputValue,
  clampDateRange,
  CHANNEL_ICONS
} from './timelineUtils';

export interface TimelineScrubberProps {
  timeBounds: TimeBounds;
  filterState: TimelineFilterState;
  onFilterChange: (nextFilterState: TimelineFilterState) => void;
  onResetFilters: () => void;
  totalEventsCount: number;
  visibleEventsCount: number;
}

export const TimelineScrubber: React.FC<TimelineScrubberProps> = ({
  timeBounds,
  filterState,
  onFilterChange,
  onResetFilters,
  totalEventsCount,
  visibleEventsCount
}) => {
  const minDate = toDateInputValue(timeBounds.earliest);
  const maxDate = toDateInputValue(timeBounds.latest);
  const startDateValue = toDateInputValue(filterState.startDate);
  const endDateValue = toDateInputValue(filterState.endDate);

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawVal = e.target.value;
    if (!rawVal) return;
    const newStartIso = fromDateInputValue(rawVal, false);
    const clamped = clampDateRange(newStartIso, filterState.endDate, 'start');
    onFilterChange({
      ...filterState,
      startDate: clamped.startDate,
      endDate: clamped.endDate
    });
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawVal = e.target.value;
    if (!rawVal) return;
    const newEndIso = fromDateInputValue(rawVal, true);
    const clamped = clampDateRange(filterState.startDate, newEndIso, 'end');
    onFilterChange({
      ...filterState,
      startDate: clamped.startDate,
      endDate: clamped.endDate
    });
  };

  const handleToggleChannel = (channel: ChannelType) => {
    const isSelected = filterState.selectedChannels.includes(channel);
    let nextChannels: ChannelType[];
    if (isSelected) {
      nextChannels = filterState.selectedChannels.filter((c) => c !== channel);
    } else {
      nextChannels = [...filterState.selectedChannels, channel];
    }
    onFilterChange({
      ...filterState,
      selectedChannels: nextChannels
    });
  };

  const handleToggleType = (eventType: EventType) => {
    const isSelected = filterState.selectedTypes.includes(eventType);
    let nextTypes: EventType[];
    if (isSelected) {
      nextTypes = filterState.selectedTypes.filter((t) => t !== eventType);
    } else {
      nextTypes = [...filterState.selectedTypes, eventType];
    }
    onFilterChange({
      ...filterState,
      selectedTypes: nextTypes
    });
  };

  return (
    <div className="timeline-scrubber" role="region" aria-label="Timeline Temporal Scrubber">
      {/* Header and Filter Metrics */}
      <div className="timeline-scrubber-header">
        <div className="timeline-metrics">
          <span className="timeline-count-badge" aria-label={`Showing ${visibleEventsCount} of ${totalEventsCount} events`}>
            {visibleEventsCount} / {totalEventsCount} Events Visible
          </span>
          <span className="timeline-range-summary">
            Range: <strong>{startDateValue}</strong> to <strong>{endDateValue}</strong>
          </span>
        </div>
        <button
          type="button"
          className="btn btn-secondary timeline-reset-btn"
          onClick={onResetFilters}
          aria-label="Reset temporal and category filters"
        >
          Reset Filters
        </button>
      </div>

      {/* Date Range Controls */}
      <div className="timeline-controls-row">
        <div className="timeline-date-group">
          <label htmlFor="timeline-start-date" className="timeline-date-label">
            Start Date
          </label>
          <input
            id="timeline-start-date"
            type="date"
            className="timeline-date-input"
            aria-label="Timeline Start Date"
            value={startDateValue}
            min={minDate}
            max={maxDate}
            onChange={handleStartDateChange}
          />
        </div>

        <div className="timeline-date-group">
          <label htmlFor="timeline-end-date" className="timeline-date-label">
            End Date
          </label>
          <input
            id="timeline-end-date"
            type="date"
            className="timeline-date-input"
            aria-label="Timeline End Date"
            value={endDateValue}
            min={minDate}
            max={maxDate}
            onChange={handleEndDateChange}
          />
        </div>
      </div>

      {/* Channel Filters */}
      <div className="timeline-filter-group" role="group" aria-label="Channel Filters">
        <span className="timeline-filter-group-title">CHANNELS:</span>
        <div className="timeline-chips-list">
          {ALL_CHANNEL_TYPES.map((channel) => {
            const isSelected = filterState.selectedChannels.includes(channel);
            return (
              <button
                key={channel}
                type="button"
                className={`timeline-filter-chip ${isSelected ? 'timeline-filter-chip-active' : ''}`}
                aria-pressed={isSelected}
                aria-label={`Filter by channel ${channel}`}
                onClick={() => handleToggleChannel(channel)}
              >
                <span className="chip-icon" aria-hidden="true">
                  {CHANNEL_ICONS[channel]}
                </span>
                <span className="chip-label">
                  {isSelected ? '✓ ' : ''}{channel}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Event Type Filters */}
      <div className="timeline-filter-group" role="group" aria-label="Event Type Filters">
        <span className="timeline-filter-group-title">EVENT TYPES:</span>
        <div className="timeline-chips-list">
          {ALL_EVENT_TYPES.map((type) => {
            const isSelected = filterState.selectedTypes.includes(type);
            return (
              <button
                key={type}
                type="button"
                className={`timeline-filter-chip ${isSelected ? 'timeline-filter-chip-active' : ''}`}
                aria-pressed={isSelected}
                aria-label={`Filter by event type ${type}`}
                onClick={() => handleToggleType(type)}
              >
                <span className="chip-label">
                  {isSelected ? '✓ ' : ''}{type}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
