import React, { useContext } from 'react';
import { AppDomain } from '../../types/shell';
import { CaseContext } from '../../context/CaseContext';
import { DEMO_CASES_LIST } from '../../fixtures/demoCase';

export interface AppShellSidebarProps {
  activeDomain: AppDomain;
  onSelectDomain: (domain: AppDomain) => void;
  onOpenGlobalSearch?: () => void;
  currentRole?: string;
  onRoleChange?: (role: string) => void;
}

interface SidebarItem {
  id: AppDomain;
  label: string;
  iconText: string;
  badge?: string;
  description: string;
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  {
    id: 'cases',
    label: 'Cases',
    iconText: 'CS',
    badge: '1 Active',
    description: 'Active case investigations and dossier workspace'
  },
  {
    id: 'search',
    label: 'Global Search',
    iconText: 'SR',
    description: 'Cross-case entity lookup (System Admin only)'
  },
  {
    id: 'jobs',
    label: 'Jobs Tracker',
    iconText: 'JB',
    description: 'Document ingestion and asynchronous analysis jobs'
  },
  {
    id: 'settings',
    label: 'Settings',
    iconText: 'ST',
    description: 'Security configurations and environment audit'
  }
];

export const AppShellSidebar: React.FC<AppShellSidebarProps> = ({
  activeDomain,
  onSelectDomain,
  onOpenGlobalSearch,
  currentRole,
  onRoleChange
}) => {
  const caseCtx = useContext(CaseContext);
  const displayCases = (caseCtx?.cases && caseCtx.cases.length > 0) ? caseCtx.cases : DEMO_CASES_LIST;
  return (
    <aside className="app-sidebar" aria-label="Global Application Navigation">
      <nav className="sidebar-nav">
        <div className="sidebar-section-title">WORKSPACE</div>
        <ul className="sidebar-menu">
          {SIDEBAR_ITEMS.map((item) => {
            const isActive = activeDomain === item.id;
            return (
              <li key={item.id} className="sidebar-item">
                <button
                  type="button"
                  className={`sidebar-btn ${isActive ? 'sidebar-btn-active' : ''}`}
                  onClick={() => {
                    if (item.id === 'search' && onOpenGlobalSearch) {
                      onOpenGlobalSearch();
                    } else {
                      onSelectDomain(item.id);
                    }
                  }}
                  aria-current={isActive ? 'page' : undefined}
                  title={item.description}
                >
                  <span className="sidebar-icon-text" aria-hidden="true">
                    {item.iconText}
                  </span>
                  <span className="sidebar-label">{item.label}</span>
                  {item.badge && (
                    <span className="sidebar-badge">{item.badge}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Authorized Cases List (Multi-Tenant Case Boundary) */}
      {caseCtx && (
        <div className="sidebar-cases-list" style={{ padding: '8px 12px', borderTop: '1px solid #1e293b', flex: 1, overflowY: 'auto' }}>
          <div className="sidebar-section-title" style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '6px' }}>
            Authorized Cases ({displayCases.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {displayCases.map((c) => {
              const isSelected = caseCtx?.activeCaseId === c.case_id;
              return (
                <button
                  key={c.case_id}
                  type="button"
                  onClick={() => caseCtx?.selectCase(c.case_id)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: isSelected ? '1px solid #3b82f6' : '1px solid transparent',
                    background: isSelected ? '#1e293b' : 'transparent',
                    color: '#f8fafc',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#38bdf8' }}>{c.case_code}</span>
                    <span style={{ fontSize: '10px', color: '#94a3b8' }}>{c.member_role}</span>
                  </div>
                  <span style={{ fontSize: '12px', color: '#f8fafc', fontWeight: 500, marginTop: '2px' }}>{c.title}</span>
                  <span style={{ fontSize: '10px', color: '#64748b' }}>{c.jurisdiction}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* RBAC Role Simulation */}
      {caseCtx && (
        <div style={{ padding: '12px', borderTop: '1px solid #1e293b', background: '#0a0f1d' }}>
          <div style={{ fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#64748b', marginBottom: '6px' }}>
            Investigator Role (RBAC Simulation)
          </div>
          <div style={{ display: 'flex', gap: '4px' }}>
            {(['SUPERVISOR', 'ANALYST', 'INVESTIGATOR'] as const).map((role) => (
              <button
                key={role}
                type="button"
                onClick={() => {
                  onRoleChange?.(role);
                  if (caseCtx?.setCurrentRole) {
                    caseCtx.setCurrentRole(role);
                  }
                }}
                style={{
                  flex: 1,
                  padding: '4px 6px',
                  borderRadius: '4px',
                  border: (currentRole === role || caseCtx?.currentRole === role) ? '1px solid #3b82f6' : '1px solid #1e293b',
                  background: (currentRole === role || caseCtx?.currentRole === role) ? '#1e293b' : 'transparent',
                  color: (currentRole === role || caseCtx?.currentRole === role) ? '#38bdf8' : '#64748b',
                  fontSize: '10px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {role.substring(0, 4)}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="sidebar-footer">
        <div className="sidebar-footer-card">
          <span className="sidebar-footer-title">SECURITY BOUNDARY</span>
          <p className="sidebar-footer-text">
            PostgreSQL System-of-Record
            <br />
            Neo4j Analytical Projection
          </p>
        </div>
      </div>
    </aside>
  );
};
