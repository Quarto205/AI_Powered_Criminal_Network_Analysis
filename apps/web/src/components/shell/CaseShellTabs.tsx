import React from 'react';
import { CaseShellTabId, TabDefinition } from '../../types/shell';

export interface CaseShellTabsProps {
  activeTab: CaseShellTabId;
  onSelectTab: (tab: CaseShellTabId) => void;
}

export const CASE_TABS: TabDefinition[] = [
  {
    id: 'overview',
    label: 'Overview',
    description: 'Case summary, document counts, unresolved reviews, active pattern alerts'
  },
  {
    id: 'graph',
    label: 'Graph',
    description: 'Interactive Cytoscape.js canvas for neighborhood traversals'
  },
  {
    id: 'timeline',
    label: 'Timeline',
    description: 'Temporal slider for communications, transactions, and events'
  },
  {
    id: 'entities',
    label: 'Entities',
    description: 'Canonical entity directory, aliases, and attribute profiles'
  },
  {
    id: 'evidence',
    label: 'Evidence',
    description: 'Provenance window with supporting document excerpts and confidence breakdown'
  },
  {
    id: 'alerts',
    label: 'Alerts',
    description: 'Rule-engine pattern detections and active investigator alerts'
  },
  {
    id: 'audit',
    label: 'Audit',
    requiredRole: 'SUPERVISOR',
    description: 'Append-only ledger of access logs and model overrides (Supervisor only)'
  }
];

export const CaseShellTabs: React.FC<CaseShellTabsProps> = ({
  activeTab,
  onSelectTab
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const currentIndex = CASE_TABS.findIndex((t) => t.id === activeTab);
    if (currentIndex === -1) return;

    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % CASE_TABS.length;
      onSelectTab(CASE_TABS[nextIndex].id);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + CASE_TABS.length) % CASE_TABS.length;
      onSelectTab(CASE_TABS[prevIndex].id);
    }
  };

  return (
    <nav className="case-tabs-nav" aria-label="Case Subsystems">
      <div
        className="case-tabs-list"
        role="tablist"
        aria-label="Case Navigation Tabs"
        onKeyDown={handleKeyDown}
      >
        {CASE_TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              role="tab"
              type="button"
              className={`case-tab-btn ${isActive ? 'case-tab-active' : ''}`}
              aria-selected={isActive}
              aria-controls={`tabpanel-${tab.id}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => onSelectTab(tab.id)}
              title={tab.description}
            >
              <span className="case-tab-label">{tab.label}</span>
              {tab.requiredRole && (
                <span className="case-tab-role-tag" aria-label={`Requires ${tab.requiredRole}`}>
                  {tab.requiredRole.substring(0, 5)}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
