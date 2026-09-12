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
  children: React.ReactNode;
}

/**
 * Persistent outer application frame (08_UI_DATA_CONTRACT.md Section 8.1).
 * 
 * Invariants:
 * - Remains persistently mounted across case-level tab switching.
 * - Preserves global state (navigation domain, system role, health status).
 * - Client-side state transitions without full document reloads.
 */
export const AppShell: React.FC<AppShellProps> = ({
  currentRole,
  healthStatus,
  activeDomain,
  onRoleChange,
  onHealthStatusChange,
  onSelectDomain,
  children
}) => {
  return (
    <div className="app-shell-layout">
      {/* 21. Master Header */}
      <AppShellHeader
        currentRole={currentRole}
        healthStatus={healthStatus}
        onRoleChange={onRoleChange}
        onHealthStatusChange={onHealthStatusChange}
      />

      <div className="app-shell-body">
        {/* 20. Master Navigation Sidebar */}
        <AppShellSidebar
          activeDomain={activeDomain}
          onSelectDomain={onSelectDomain}
        />

        {/* 18. Persistent Main Viewport */}
        <main className="app-shell-main" role="main">
          {children}
        </main>
      </div>
    </div>
  );
};
