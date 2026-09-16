import React from 'react';
import { useCase, WorkspaceTab } from '../../context/CaseContext';
import { useSearch } from '../../context/SearchContext';
import {
  FolderOpen,
  Search,
  Bot,
  LayoutDashboard,
  Share2,
  Clock,
  FileText,
  BarChart3,
  ShieldAlert,
} from 'lucide-react';

export const AppSidebar: React.FC = () => {
  const { activeTab, setActiveTab } = useCase();
  const { openSearch } = useSearch();

  const navItemStyle = (isActive: boolean): React.CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    padding: '0.55rem 0.85rem',
    borderRadius: 'var(--radius-lg)',
    fontSize: '13px',
    fontWeight: isActive ? 600 : 500,
    color: isActive ? '#ffffff' : 'var(--cnas-text-secondary)',
    backgroundColor: isActive ? 'var(--cnas-navy)' : 'transparent',
    boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    textAlign: 'left',
  });

  return (
    <aside
      style={{
        position: 'fixed',
        left: 0,
        top: '64px',
        bottom: 0,
        width: '240px',
        backgroundColor: 'var(--cnas-surface)',
        borderRight: '1px solid var(--cnas-border)',
        boxShadow: 'var(--shadow-xs)',
        zIndex: 40,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '1rem 0.75rem',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {/* Top Quick Links */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <button
            onClick={() => setActiveTab('cases')}
            style={navItemStyle(activeTab === 'cases')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <FolderOpen size={16} color={activeTab === 'cases' ? '#ffffff' : 'var(--cnas-navy)'} />
              <span>Cases</span>
            </div>
          </button>

          <button
            onClick={openSearch}
            style={navItemStyle(false)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <Search size={16} color="var(--cnas-navy)" />
              <span>Search</span>
            </div>
            <span
              style={{
                fontFamily: 'var(--font-code)',
                fontSize: '10px',
                color: 'var(--cnas-text-muted)',
                backgroundColor: 'var(--cnas-surface-subtle)',
                padding: '1px 5px',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              /
            </span>
          </button>
        </div>

        <div style={{ height: '1px', backgroundColor: 'var(--cnas-border)', margin: '2px 0' }} />

        {/* Primary Workspace Section */}
        <div>
          <div
            style={{
              padding: '0.25rem 0.85rem',
              fontSize: '10px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
              color: 'var(--cnas-text-muted)',
            }}
          >
            Primary Workspace
          </div>

          <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '4px' }}>
            <button
              onClick={() => setActiveTab('copilot')}
              style={navItemStyle(activeTab === 'copilot')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <Bot size={16} color={activeTab === 'copilot' ? '#ffffff' : 'var(--cnas-ai-primary)'} />
                <span>AI Copilot</span>
              </div>
              <span
                style={{
                  fontSize: '9px',
                  fontWeight: 700,
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: activeTab === 'copilot' ? 'rgba(255,255,255,0.2)' : 'var(--cnas-ai-subtle)',
                  color: activeTab === 'copilot' ? '#ffffff' : 'var(--cnas-ai-text)',
                }}
              >
                LIVE
              </span>
            </button>

            <button
              onClick={() => setActiveTab('overview')}
              style={navItemStyle(activeTab === 'overview')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <LayoutDashboard size={16} />
                <span>Overview</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('network')}
              style={navItemStyle(activeTab === 'network')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <Share2 size={16} />
                <span>Network</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('timeline')}
              style={navItemStyle(activeTab === 'timeline')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <Clock size={16} />
                <span>Timeline</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('evidence')}
              style={navItemStyle(activeTab === 'evidence')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <FileText size={16} />
                <span>Evidence</span>
              </div>
            </button>
          </nav>
        </div>

        <div style={{ height: '1px', backgroundColor: 'var(--cnas-border)', margin: '2px 0' }} />

        {/* Secondary & Advanced */}
        <div>
          <div
            style={{
              padding: '0.25rem 0.85rem',
              fontSize: '10px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
              color: 'var(--cnas-text-muted)',
            }}
          >
            Secondary & Advanced
          </div>

          <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '4px' }}>
            <button
              onClick={() => setActiveTab('analysis')}
              style={navItemStyle(activeTab === 'analysis')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <BarChart3 size={16} />
                <span>Analysis</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              style={navItemStyle(activeTab === 'audit')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <ShieldAlert size={16} />
                <span>Compliance & Audit</span>
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Bottom Engine Status Box */}
      <div
        style={{
          padding: '0.75rem',
          borderRadius: 'var(--radius-lg)',
          backgroundColor: 'var(--cnas-surface-subtle)',
          border: '1px solid var(--cnas-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', fontWeight: 600 }}>
            Engine Status
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
            <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
              v4.2-Secure
            </span>
            <span style={{ fontSize: '10px', color: 'var(--cnas-verified)', fontWeight: 600 }}>
              Active
            </span>
          </div>
        </div>
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: 'var(--cnas-verified)',
            boxShadow: '0 0 0 3px rgba(5, 150, 105, 0.2)',
          }}
          className="pulse-live"
        />
      </div>
    </aside>
  );
};
