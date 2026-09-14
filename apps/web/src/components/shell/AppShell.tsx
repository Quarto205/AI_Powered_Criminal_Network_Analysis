import React from 'react';
import { SystemRole, SystemHealthStatus, AppDomain } from '../../types/shell';
import { AppShellHeader } from './AppShellHeader';
import { AppShellSidebar } from './AppShellSidebar';

export interface AppShellProps {
  currentRole: SystemRole;
  healthStatus: SystemHealthStatus;
  activeDomain: AppDomain;
  onRoleChange?: (role: SystemRole) => void;
  onHealthStatusChange?: (status: SystemHealthStatus) => void;
  onSelectDomain: (domain: AppDomain) => void;
  onOpenGlobalSearch?: () => void;
  children: React.ReactNode;
}

/**
 * Persistent outer application frame (08_UI_DATA_CONTRACT.md Section 8.1).
 * 
 * Invariants:
 * - Remains persistently mounted across case-level tab switching.
 * - Preserves global state (navigation domain, system role, health status).
 * - Client-side state transitions without full document reloads.
 * - Universal '/' shortcut triggers global search when outside editable fields.
 */
export const AppShell: React.FC<AppShellProps> = ({
  currentRole,
  healthStatus,
  activeDomain,
  onRoleChange,
  onHealthStatusChange,
  onSelectDomain,
  onOpenGlobalSearch,
  children
}) => {
  // Universal '/' keyboard shortcut listener (Section 21, 51, 52)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/') {
        const target = e.target as HTMLElement | null;
        const tagName = target?.tagName?.toLowerCase();
        const isEditable =
          tagName === 'input' ||
          tagName === 'textarea' ||
          tagName === 'select' ||
          Boolean(target?.isContentEditable);

        if (!isEditable && onOpenGlobalSearch) {
          e.preventDefault();
          onOpenGlobalSearch();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onOpenGlobalSearch]);

  return (
    <div data-testid="app-shell" className="app-shell-layout">
      {/* 21. Master Header */}
      <AppShellHeader
        currentRole={currentRole}
        healthStatus={healthStatus}
        onRoleChange={onRoleChange}
        onHealthStatusChange={onHealthStatusChange}
        onOpenGlobalSearch={onOpenGlobalSearch}
      />

      <div className="app-shell-body">
        {/* 20. Master Navigation Sidebar */}
        <AppShellSidebar
          activeDomain={activeDomain}
          onSelectDomain={onSelectDomain}
          onOpenGlobalSearch={onOpenGlobalSearch}
          currentRole={currentRole}
          onRoleChange={(r) => onRoleChange?.(r as SystemRole)}
        />

        {/* 18. Persistent Main Viewport */}
        <main className="app-shell-main" role="main">
          {children}
        </main>
      </div>
    </div>
  );
};
