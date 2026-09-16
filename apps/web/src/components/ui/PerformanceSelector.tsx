import React from 'react';
import { usePerformance } from '../../context/PerformanceContext';
import { Sparkles, Gauge, EyeOff } from 'lucide-react';

export const PerformanceSelector: React.FC = () => {
  const { mode, setMode } = usePerformance();

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        background: 'var(--cnas-surface-subtle)',
        border: '1px solid var(--cnas-border)',
        borderRadius: 'var(--radius-lg)',
        padding: '2px',
        gap: '2px',
      }}
      title="Display & Animation Performance Policy"
    >
      <button
        onClick={() => setMode('full')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 8px',
          borderRadius: 'var(--radius-md)',
          fontSize: '11px',
          fontWeight: 600,
          color: mode === 'full' ? 'var(--cnas-blue)' : 'var(--cnas-text-muted)',
          background: mode === 'full' ? 'var(--cnas-surface)' : 'transparent',
          boxShadow: mode === 'full' ? 'var(--shadow-xs)' : 'none',
        }}
      >
        <Sparkles size={12} />
        <span>Full 3D</span>
      </button>

      <button
        onClick={() => setMode('balanced')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 8px',
          borderRadius: 'var(--radius-md)',
          fontSize: '11px',
          fontWeight: 600,
          color: mode === 'balanced' ? 'var(--cnas-navy)' : 'var(--cnas-text-muted)',
          background: mode === 'balanced' ? 'var(--cnas-surface)' : 'transparent',
          boxShadow: mode === 'balanced' ? 'var(--shadow-xs)' : 'none',
        }}
      >
        <Gauge size={12} />
        <span>Balanced</span>
      </button>

      <button
        onClick={() => setMode('reduced')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 8px',
          borderRadius: 'var(--radius-md)',
          fontSize: '11px',
          fontWeight: 600,
          color: mode === 'reduced' ? 'var(--cnas-navy)' : 'var(--cnas-text-muted)',
          background: mode === 'reduced' ? 'var(--cnas-surface)' : 'transparent',
          boxShadow: mode === 'reduced' ? 'var(--shadow-xs)' : 'none',
        }}
      >
        <EyeOff size={12} />
        <span>Reduced</span>
      </button>
    </div>
  );
};
