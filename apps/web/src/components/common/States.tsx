import React from 'react';
import { AlertCircle, HelpCircle } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  icon = <HelpCircle size={40} color="#64748b" />,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
        background: 'rgba(15, 23, 42, 0.4)',
        borderRadius: '8px',
        border: '1px dashed #334155',
        margin: '16px',
      }}
    >
      <div style={{ marginBottom: '16px' }}>{icon}</div>
      <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#f1f5f9', marginBottom: '8px' }}>
        {title}
      </h3>
      <p style={{ fontSize: '13px', color: '#94a3b8', maxWidth: '440px', marginBottom: '16px' }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            padding: '6px 14px',
            fontSize: '12px',
            fontWeight: 500,
            color: '#ffffff',
            background: '#2563eb',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export const LoadingState: React.FC<{ message?: string }> = ({
  message = 'Loading investigative assets...',
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 24px',
        color: '#94a3b8',
      }}
    >
      <div
        style={{
          width: '32px',
          height: '32px',
          border: '3px solid #1e293b',
          borderTop: '3px solid #3b82f6',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          marginBottom: '12px',
        }}
      />
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)' }}>{message}</span>
    </div>
  );
};

export const AlertBox: React.FC<{
  type?: 'info' | 'warning' | 'error';
  title?: string;
  message: string;
}> = ({ type = 'info', title, message }) => {
  const styles = {
    info: { bg: '#082f49', border: '#0369a1', text: '#bae6fd' },
    warning: { bg: '#451a03', border: '#b45309', text: '#fde68a' },
    error: { bg: '#450a0a', border: '#b91c1c', text: '#fecaca' },
  }[type];

  return (
    <div
      style={{
        display: 'flex',
        gap: '10px',
        padding: '12px 16px',
        borderRadius: '6px',
        backgroundColor: styles.bg,
        border: `1px solid ${styles.border}`,
        color: styles.text,
        fontSize: '13px',
        margin: '8px 0',
      }}
    >
      <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
      <div>
        {title && <div style={{ fontWeight: 600, marginBottom: '2px' }}>{title}</div>}
        <div>{message}</div>
      </div>
    </div>
  );
};
