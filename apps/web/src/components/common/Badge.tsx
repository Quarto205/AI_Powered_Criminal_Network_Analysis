import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'person' | 'phone' | 'bank' | 'vehicle' | 'org' | 'location' | 'offense' | 'observed' | 'inferred' | 'high' | 'medium' | 'low';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', className = '' }) => {
  const getStyles = () => {
    switch (variant) {
      case 'person':
        return 'bg-indigo-950 text-indigo-300 border border-indigo-700/50';
      case 'phone':
        return 'bg-cyan-950 text-cyan-300 border border-cyan-700/50';
      case 'bank':
        return 'bg-emerald-950 text-emerald-300 border border-emerald-700/50';
      case 'vehicle':
        return 'bg-amber-950 text-amber-300 border border-amber-700/50';
      case 'org':
        return 'bg-purple-950 text-purple-300 border border-purple-700/50';
      case 'location':
        return 'bg-rose-950 text-rose-300 border border-rose-700/50';
      case 'offense':
        return 'bg-red-950 text-red-300 border border-red-700/50';
      case 'observed':
        return 'bg-blue-950 text-blue-300 border border-blue-600/60 font-semibold';
      case 'inferred':
        return 'bg-pink-950 text-pink-300 border border-dashed border-pink-500 font-semibold';
      case 'high':
        return 'bg-red-950 text-red-300 border border-red-800';
      case 'medium':
        return 'bg-amber-950 text-amber-300 border border-amber-800';
      case 'low':
        return 'bg-slate-800 text-slate-300 border border-slate-700';
      default:
        return 'bg-slate-800 text-slate-200 border border-slate-700';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono tracking-wide ${getStyles()} ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '11px',
        letterSpacing: '0.03em',
      }}
    >
      {children}
    </span>
  );
};
