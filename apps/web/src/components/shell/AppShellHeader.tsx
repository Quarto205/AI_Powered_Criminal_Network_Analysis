import React from 'react';
import { SystemRole, SystemHealthStatus } from '../../types/shell';

export interface AppShellHeaderProps {
  currentRole: SystemRole;
  healthStatus: SystemHealthStatus;
  onRoleChange?: (role: SystemRole) => void;
  onHealthStatusChange?: (status: SystemHealthStatus) => void;
  onOpenGlobalSearch?: () => void;
}

export const AppShellHeader: React.FC<AppShellHeaderProps> = ({
  currentRole,
  healthStatus,
  onRoleChange,
  onHealthStatusChange,
  onOpenGlobalSearch
}) => {
  return (
    <header className="app-header" aria-label="Master Application Header">
      <div className="app-header-brand">
        <div className="app-logo-mark">
          SIH26189
        </div>
        <div className="app-brand-text">
          <span className="app-title">SIH26189 — CNAS</span>
          <span className="app-subtitle">AI-Powered Criminal Network Analysis System</span>
        </div>
      </div>

      <div className="app-header-controls">
        {/* Global Search Trigger Button (Section 48, 49) */}
        {onOpenGlobalSearch && (
          <button
            type="button"
            className="header-search-btn"
            onClick={onOpenGlobalSearch}
            aria-label="Search authorized cases and entities"
          >
            <span className="search-btn-icon" aria-hidden="true">🔍</span>
            <span className="header-search-text">Search</span>
            <kbd className="header-search-kbd">/</kbd>
          </button>
        )}

        {/* System Health Presentation (Section 35, 65) */}
        <div className="health-badge-container" aria-label={`System Status: ${healthStatus}`}>
          <span className="health-label">SYSTEM HEALTH</span>
          <div
            className={`health-badge ${
              healthStatus === 'NORMAL'
                ? 'health-normal'
                : healthStatus.includes('DEGRADED')
                ? 'health-degraded'
                : 'health-unavailable'
            }`}
          >
            <span className="health-indicator" aria-hidden="true" />
            <span className="health-text">{healthStatus}</span>
          </div>

          {onHealthStatusChange && (
            <select
              className="health-selector"
              value={healthStatus}
              onChange={(e) => onHealthStatusChange(e.target.value as SystemHealthStatus)}
              aria-label="Simulate System Health State"
              title="Test degraded operating modes (06_WORKFLOWS.md Section 6.3)"
            >
              <option value="NORMAL">NORMAL</option>
              <option value="DEGRADED — Provider Offline">DEGRADED — Provider Offline</option>
              <option value="GRAPH UNAVAILABLE">GRAPH UNAVAILABLE</option>
            </select>
          )}
        </div>

        {/* Global User Role Presentation (Section 21, 66) */}
        <div className="role-badge-container" aria-label={`Active User Role: ${currentRole}`}>
          <span className="role-label">ACTIVE ROLE</span>
          <div className={`role-badge role-${currentRole.toLowerCase()}`}>
            <span className="role-indicator" aria-hidden="true" />
            <span className="role-text">{currentRole}</span>
          </div>

          {onRoleChange && (
            <select
              className="role-selector"
              value={currentRole}
              onChange={(e) => onRoleChange(e.target.value as SystemRole)}
              aria-label="Simulate Active System Role"
              title="Switch role to verify RBAC and PermissionGate behavior"
            >
              <option value="INVESTIGATOR">INVESTIGATOR</option>
              <option value="ANALYST">ANALYST</option>
              <option value="SUPERVISOR">SUPERVISOR</option>
            </select>
          )}
        </div>
      </div>
    </header>
  );
};
