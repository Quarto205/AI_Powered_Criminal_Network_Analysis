/**
 * Interactive Timeline Tab Component
 * Strictly adheres to 02_DATABASE_SCHEMA.md (events table) and 08_UI_DATA_CONTRACT.md.
 */

import React, { useEffect, useState } from 'react';
import { Clock, PhoneCall, DollarSign, Navigation, FileCheck, Filter } from 'lucide-react';
import { TimelineEventItem } from '../../contracts/audit';
import { Badge } from '../common/Badge';
import { apiClient } from '../../api';
import { useCase } from '../../context/CaseContext';
import { useSelection } from '../../context/SelectionContext';

export const TimelineTab: React.FC = () => {
  const { activeCaseId } = useCase();
  const { selectNode } = useSelection();
  const [events, setEvents] = useState<TimelineEventItem[]>([]);
  const [filterType, setFilterType] = useState<string>('ALL');

  useEffect(() => {
    let isMounted = true;
    if (activeCaseId) {
      apiClient
        .getTimelineEvents(activeCaseId)
        .then((resp) => {
          if (isMounted) {
            setEvents(resp.data.events);
          }
        })
        .catch(() => {
          // Handled gracefully
        });
    }
    return () => {
      isMounted = false;
    };
  }, [activeCaseId]);

  const filteredEvents = events.filter((e) => {
    if (filterType === 'ALL') return true;
    return e.event_type === filterType;
  });

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'COMMUNICATION':
        return <PhoneCall size={16} color="#06b6d4" />;
      case 'TRANSACTION':
        return <DollarSign size={16} color="#10b981" />;
      case 'MOVEMENT':
        return <Navigation size={16} color="#f59e0b" />;
      case 'DOCUMENT_OBSERVATION':
        return <FileCheck size={16} color="#8b5cf6" />;
      default:
        return <Clock size={16} color="#94a3b8" />;
    }
  };

  return (
    <div style={{ padding: '24px', height: '100%', overflowY: 'auto', background: '#090d16' }}>
      {/* Header & Filter Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#f8fafc' }}>
            Case Event & Interaction Timeline
          </h2>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            Chronological reconstruction of communications, financial disbursements, and sightings.
          </p>
        </div>

        {/* Filter Buttons */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Filter size={14} color="#64748b" />
          {['ALL', 'COMMUNICATION', 'TRANSACTION', 'MOVEMENT', 'DOCUMENT_OBSERVATION'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              style={{
                padding: '4px 10px',
                borderRadius: '4px',
                border: filterType === t ? '1px solid #3b82f6' : '1px solid #334155',
                background: filterType === t ? '#1e293b' : 'transparent',
                color: filterType === t ? '#f8fafc' : '#94a3b8',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline Stream */}
      <div style={{ position: 'relative', paddingLeft: '28px' }}>
        {/* Timeline vertical bar */}
        <div
          style={{
            position: 'absolute',
            left: '11px',
            top: '8px',
            bottom: '8px',
            width: '2px',
            background: '#1e293b',
          }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {filteredEvents.map((evt) => (
            <div
              key={evt.event_id}
              style={{
                position: 'relative',
                background: '#0f172a',
                border: '1px solid #1e293b',
                borderRadius: '8px',
                padding: '16px 20px',
              }}
            >
              {/* Event bullet point */}
              <div
                style={{
                  position: 'absolute',
                  left: '-28px',
                  top: '16px',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: '#090d16',
                  border: '2px solid #3b82f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {getEventIcon(evt.event_type)}
              </div>

              {/* Event Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Badge variant="default">{evt.event_type}</Badge>
                  <span style={{ fontSize: '12px', color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                    {new Date(evt.timestamp).toLocaleString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })} IST
                  </span>
                </div>
                {evt.source_ref && (
                  <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                    Src: {evt.source_ref}
                  </span>
                )}
              </div>

              {/* Description */}
              <p style={{ fontSize: '13px', color: '#e2e8f0', marginBottom: '12px', lineHeight: '1.4' }}>
                {evt.description}
              </p>

              {/* Involved Entities */}
              {evt.entities_involved && evt.entities_involved.length > 0 && (
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>Involved:</span>
                  {evt.entities_involved.map((ent, idx) => (
                    <button
                      key={idx}
                      onClick={() =>
                        selectNode({
                          id: ent.entity_id,
                          label: ent.canonical_name,
                          entity_type: 'ENTITY',
                          case_id: activeCaseId ?? '',
                        })
                      }
                      style={{
                        padding: '2px 8px',
                        background: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '4px',
                        color: '#93c5fd',
                        fontSize: '11px',
                        cursor: 'pointer',
                      }}
                    >
                      {ent.canonical_name} ({ent.role})
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
