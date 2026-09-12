import React from 'react';
import { AppDomain } from '../../types/shell';

export interface AppShellSidebarProps {
  activeDomain: AppDomain;
  onSelectDomain: (domain: AppDomain) => void;
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
  onSelectDomain
}) => {
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
                  onClick={() => onSelectDomain(item.id)}
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
