import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import { Badge } from '../components/ui/Badge';
import {
  Clock,
  Calendar,
  Share2,
  FileText,
  Sliders,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';

type TimelinePreset = '12h' | '24h' | 'hawala' | '7d' | 'custom';

export const TimelineView: React.FC = () => {
  const { timelineEvents, inspectInGraph } = useCase();
  const [activePreset, setActivePreset] = useState<TimelinePreset>('hawala');
  const [sliderStart, setSliderStart] = useState<number>(35);
  const [sliderEnd, setSliderEnd] = useState<number>(95);

  const handlePresetChange = (preset: TimelinePreset) => {
    setActivePreset(preset);
    if (preset === '12h') {
      setSliderStart(75);
      setSliderEnd(100);
    } else if (preset === '24h') {
      setSliderStart(55);
      setSliderEnd(100);
    } else if (preset === 'hawala') {
      setSliderStart(35);
      setSliderEnd(95);
    } else if (preset === '7d') {
      setSliderStart(0);
      setSliderEnd(100);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Header & Duration Scrubber Panel */}
      <div
        style={{
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '1.5rem',
          boxShadow: 'var(--shadow-xs)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={20} color="var(--cnas-navy)" />
              <h1 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--cnas-navy)' }}>
                Chronological Timeline & Spatial Event Sequence
              </h1>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--cnas-text-secondary)', marginTop: '4px' }}>
              Correlate cellular tower CDR pings, cash liquidations, and physical observations across time.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {(['12h', '24h', 'hawala', '7d'] as TimelinePreset[]).map((preset) => (
              <button
                key={preset}
                onClick={() => handlePresetChange(preset)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '12px',
                  fontWeight: 600,
                  backgroundColor: activePreset === preset ? 'var(--cnas-navy)' : 'var(--cnas-surface-subtle)',
                  color: activePreset === preset ? '#ffffff' : 'var(--cnas-text-secondary)',
                  border: `1px solid ${activePreset === preset ? 'var(--cnas-navy)' : 'var(--cnas-border)'}`,
                  transition: 'all 0.15s ease',
                }}
              >
                {preset === 'hawala' ? 'Hawala Window (24-48h)' : preset.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Dual Handle Timeline Window Scrubber */}
        <div
          style={{
            padding: '1rem',
            backgroundColor: 'var(--cnas-surface-subtle)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--cnas-border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
            <span style={{ fontWeight: 600, color: 'var(--cnas-navy)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Sliders size={14} />
              <span>Observation Horizon:</span>
              <span style={{ fontFamily: 'var(--font-code)', color: 'var(--cnas-blue)' }}>
                T-48 hrs to T-0 (Latest Intercept)
              </span>
            </span>
            <span style={{ color: 'var(--cnas-text-muted)' }}>
              Events Filtered: <strong style={{ color: 'var(--cnas-navy)' }}>{timelineEvents.length}</strong> / 24 total
            </span>
          </div>

          {/* Interactive slider simulation track */}
          <div style={{ position: 'relative', height: '32px', display: 'flex', alignItems: 'center' }}>
            <div
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                height: '6px',
                backgroundColor: 'var(--cnas-border)',
                borderRadius: '3px',
              }}
            />
            {/* Active Range Highlight */}
            <div
              style={{
                position: 'absolute',
                left: `${sliderStart}%`,
                width: `${sliderEnd - sliderStart}%`,
                height: '8px',
                backgroundColor: 'var(--cnas-navy)',
                borderRadius: '4px',
                boxShadow: '0 0 8px rgba(0, 37, 72, 0.25)',
              }}
            />

            {/* Density Tick Marks */}
            <div style={{ position: 'absolute', left: 0, right: 0, height: '100%', pointerEvents: 'none', display: 'flex', alignItems: 'center' }}>
              {[10, 22, 38, 42, 58, 65, 72, 85, 92].map((pos, i) => (
                <span
                  key={i}
                  style={{
                    position: 'absolute',
                    left: `${pos}%`,
                    width: '3px',
                    height: pos > 40 ? '16px' : '10px',
                    backgroundColor: pos > 40 ? 'var(--cnas-risk)' : 'var(--cnas-border-strong)',
                    borderRadius: '2px',
                  }}
                />
              ))}
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '11px',
              fontFamily: 'var(--font-code)',
              color: 'var(--cnas-text-muted)',
              borderTop: '1px solid var(--cnas-border)',
              paddingTop: '6px',
              marginTop: '4px',
            }}
          >
            <span>18 May 00:00</span>
            <span>20 May 12:00</span>
            <span style={{ fontWeight: 700, color: 'var(--cnas-navy)' }}>22 May 08:00</span>
            <span>23 May 11:00</span>
            <span style={{ fontWeight: 700, color: 'var(--cnas-blue)' }}>24 May 18:30 IST (Latest)</span>
          </div>
        </div>
      </div>

      {/* 3. Synchronized Incident Records Stream */}
      <div
        style={{
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '1.5rem',
          boxShadow: 'var(--shadow-xs)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
          Synchronized Chronological Incident Stream
        </h2>

        <div style={{ position: 'relative', paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div
            style={{
              position: 'absolute',
              left: '6px',
              top: '6px',
              bottom: '8px',
              width: '2px',
              backgroundColor: 'var(--cnas-border)',
            }}
          />

          {timelineEvents.map((evt) => (
            <div
              key={evt.id}
              style={{
                position: 'relative',
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: '1rem',
                backgroundColor: 'var(--cnas-surface-subtle)',
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--cnas-border)',
              }}
            >
              {/* Dot */}
              <span
                style={{
                  position: 'absolute',
                  left: '-1.5rem',
                  top: '1rem',
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor:
                    evt.severity === 'CRITICAL'
                      ? 'var(--cnas-risk)'
                      : evt.severity === 'WARN'
                      ? 'var(--cnas-blue)'
                      : 'var(--cnas-navy)',
                  boxShadow: '0 0 0 4px #ffffff',
                }}
              />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxWidth: '640px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {evt.title}
                  </span>
                  <Badge variant={evt.severity === 'CRITICAL' ? 'risk' : 'neutral'} size="sm">
                    {evt.type}
                  </Badge>
                </div>

                <p style={{ fontSize: '12px', color: 'var(--cnas-text-secondary)', lineHeight: 1.45 }}>
                  {evt.description}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '4px', fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                  <span>Source: <strong style={{ color: 'var(--cnas-text-primary)' }}>{evt.sourceType}</strong></span>
                  {evt.linkedEntityName && (
                    <>
                      <span>•</span>
                      <span>Target: <strong style={{ color: 'var(--cnas-navy)' }}>{evt.linkedEntityName}</strong></span>
                    </>
                  )}
                </div>
              </div>

              {/* Right Side: Timestamp & Inspect in Graph action */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--font-code)', fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {evt.displayTime}
                  </div>
                </div>

                {evt.linkedEntityId && (
                  <button
                    onClick={() => inspectInGraph(evt.linkedEntityId!)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--cnas-navy)',
                      color: '#ffffff',
                      fontSize: '11px',
                      fontWeight: 600,
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    <Share2 size={12} />
                    <span>Inspect in Graph</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
