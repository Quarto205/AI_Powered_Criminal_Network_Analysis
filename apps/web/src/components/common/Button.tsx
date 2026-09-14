import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  icon,
  className = '',
  disabled,
  style,
  ...props
}) => {
  const baseStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    fontFamily: 'var(--font-sans)',
    fontWeight: 500,
    borderRadius: '6px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    transition: 'all 0.15s ease-in-out',
    border: '1px solid transparent',
    outline: 'none',
    ...style,
  };

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { padding: '4px 10px', fontSize: '12px', height: '28px' },
    md: { padding: '6px 14px', fontSize: '13px', height: '34px' },
    lg: { padding: '8px 18px', fontSize: '14px', height: '40px' },
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: '#2563eb',
      color: '#ffffff',
      borderColor: '#3b82f6',
    },
    secondary: {
      backgroundColor: '#1e293b',
      color: '#f1f5f9',
      borderColor: '#334155',
    },
    danger: {
      backgroundColor: '#991b1b',
      color: '#fef2f2',
      borderColor: '#dc2626',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: '#94a3b8',
      borderColor: 'transparent',
    },
    outline: {
      backgroundColor: 'transparent',
      color: '#f1f5f9',
      borderColor: '#475569',
    },
  };

  return (
    <button
      style={{
        ...baseStyles,
        ...sizeStyles[size],
        ...variantStyles[variant],
      }}
      disabled={disabled}
      className={`focus-ring ${className}`}
      {...props}
    >
      {icon && <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>}
      {children}
    </button>
  );
};
