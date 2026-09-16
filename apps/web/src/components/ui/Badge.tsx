import React from 'react';

export interface BadgeProps {
  variant?: 'verified' | 'ai-inferred' | 'review' | 'risk' | 'neutral' | 'navy';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  icon?: React.ReactNode;
  pulse?: boolean;
  style?: React.CSSProperties;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  size = 'md',
  children,
  icon,
  pulse = false,
  style,
  className,
}) => {
  const baseStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.35rem',
    borderRadius: 'var(--radius-full)',
    fontWeight: 600,
    fontSize: size === 'sm' ? '10px' : '11px',
    lineHeight: '14px',
    padding: size === 'sm' ? '0.15rem 0.45rem' : '0.25rem 0.65rem',
    letterSpacing: '0.02em',
    whiteSpace: 'nowrap',
    transition: 'all var(--transition-fast)',
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    verified: {
      backgroundColor: 'var(--cnas-verified-bg)',
      color: 'var(--cnas-verified)',
      border: '1px solid var(--cnas-verified-border)',
    },
    'ai-inferred': {
      backgroundColor: 'var(--cnas-ai-subtle)',
      color: 'var(--cnas-ai-text)',
      border: '1px dashed var(--cnas-ai-border)',
    },
    review: {
      backgroundColor: 'var(--cnas-review-bg)',
      color: 'var(--cnas-review)',
      border: '1px solid var(--cnas-review-border)',
    },
    risk: {
      backgroundColor: 'var(--cnas-risk-bg)',
      color: 'var(--cnas-risk)',
      border: '1px solid var(--cnas-risk-border)',
    },
    navy: {
      backgroundColor: 'var(--cnas-surface-container)',
      color: 'var(--cnas-navy)',
      border: '1px solid var(--cnas-border)',
    },
    neutral: {
      backgroundColor: 'var(--cnas-surface-subtle)',
      color: 'var(--cnas-text-secondary)',
      border: '1px solid var(--cnas-border)',
    },
  };

  return (
    <span style={{ ...baseStyles, ...variantStyles[variant], ...style }} className={className}>
      {pulse && (
        <span
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: 'currentColor',
            display: 'inline-block',
          }}
          className="pulse-live"
        />
      )}
      {icon}
      {children}
    </span>
  );
};
