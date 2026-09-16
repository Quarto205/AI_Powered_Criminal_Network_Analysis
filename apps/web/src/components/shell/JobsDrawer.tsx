import React from 'react';
import { MOCK_BACKGROUND_JOBS } from '../../mocks/data';
import { X, CheckCircle2, Loader2, Clock } from 'lucide-react';

interface JobsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const JobsDrawer: React.FC<JobsDrawerProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(11, 28, 48, 0.3)',
        backdropFilter: 'blur(2px)',
        zIndex: 90,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '380px',
          height: '100%',
          backgroundColor: 'var(--cnas-surface)',
          borderLeft: '1px solid var(--cnas-border)',
          boxShadow: 'var(--shadow-drawer)',
          display: 'flex',
          flexDirection: 'column',
          padding: '1.25rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
              Ingestion & Engine Jobs
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
              Real-time pipeline verification status
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '4px',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--cnas-text-muted)',
            }}
          >
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', flex: 1 }}>
          {MOCK_BACKGROUND_JOBS.map((job) => (
            <div
              key={job.id}
              style={{
                padding: '0.85rem',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'var(--cnas-surface-subtle)',
                border: '1px solid var(--cnas-border)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.45rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-text-primary)' }}>
                  {job.title}
                </span>
                {job.status === 'COMPLETED' ? (
                  <CheckCircle2 size={16} color="var(--cnas-verified)" />
                ) : (
                  <Loader2 size={16} color="var(--cnas-blue)" className="pulse-live" />
                )}
              </div>

              {/* Progress bar */}
              <div
                style={{
                  width: '100%',
                  height: '4px',
                  backgroundColor: 'var(--cnas-border)',
                  borderRadius: 'var(--radius-full)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${job.progress}%`,
                    height: '100%',
                    backgroundColor: job.status === 'COMPLETED' ? 'var(--cnas-verified)' : 'var(--cnas-blue)',
                    transition: 'width 0.3s ease',
                  }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '10px', color: 'var(--cnas-text-muted)' }}>
                <span>{job.progress}% Attested</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                  <Clock size={10} />
                  {job.startedAgo}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
