import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useCase } from '../../context/CaseContext';
import { useSearch } from '../../context/SearchContext';
import {
  Search,
  Shield,
  ChevronDown,
  Bell,
  Activity,
  LogOut,
  FolderOpen
} from 'lucide-react';

interface AppHeaderProps {
  onOpenJobsDrawer: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ onOpenJobsDrawer }) => {
  const { currentUser, logout } = useAuth();
  const { activeCase, cases, setActiveCase, setActiveTab } = useCase();
  const { openSearch } = useSearch();
  const [isCaseMenuOpen, setIsCaseMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  return (
    <header
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '64px',
        backgroundColor: 'rgba(255, 255, 255, 0.94)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--cnas-border)',
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.5rem',
        boxShadow: 'var(--shadow-xs)',
      }}
    >
      {/* Left Section: Logo & Active Case Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Brand Logo */}
        <div
          onClick={() => setActiveTab('overview')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            cursor: 'pointer',
          }}
        >
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--cnas-navy) 0%, #0051d5 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: 'var(--shadow-xs)',
            }}
          >
            <Shield size={18} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 800,
                fontSize: '17px',
                lineHeight: 1,
                color: 'var(--cnas-navy)',
                letterSpacing: '-0.02em',
              }}
            >
              CNAS
            </span>
            <span
              style={{
                fontSize: '9px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--cnas-text-muted)',
                lineHeight: 1.2,
                marginTop: '2px',
              }}
            >
              Forensic Intelligence
            </span>
          </div>
        </div>

        <div style={{ height: '24px', width: '1px', backgroundColor: 'var(--cnas-border)' }} />

        {/* Active Case Context Pill */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsCaseMenuOpen((prev) => !prev)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              backgroundColor: 'var(--cnas-surface-subtle)',
              border: '1px solid var(--cnas-border)',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-lg)',
              cursor: 'pointer',
              transition: 'background var(--transition-fast)',
            }}
          >
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
            <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-code)',
                    fontSize: '11px',
                    fontWeight: 700,
                    color: 'var(--cnas-navy)',
                  }}
                >
                  {activeCase.caseNumber}
                </span>
                <span style={{ color: 'var(--cnas-text-dim)', fontSize: '11px' }}>·</span>
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--cnas-text-primary)',
                    maxWidth: '220px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {activeCase.title.split('—')[0]}
                </span>
              </div>
              <span
                style={{
                  fontSize: '10px',
                  color: 'var(--cnas-text-muted)',
                  lineHeight: 1.1,
                  marginTop: '1px',
                }}
              >
                {activeCase.jurisdiction}
              </span>
            </div>
            <ChevronDown size={14} color="var(--cnas-text-muted)" />
          </button>

          {/* Case Dropdown Menu */}
          {isCaseMenuOpen && (
            <div
              style={{
                position: 'absolute',
                top: '115%',
                left: 0,
                width: '320px',
                backgroundColor: 'var(--cnas-surface)',
                border: '1px solid var(--cnas-border)',
                borderRadius: 'var(--radius-xl)',
                boxShadow: 'var(--shadow-lg)',
                padding: '0.5rem',
                zIndex: 100,
              }}
            >
              <div
                style={{
                  padding: '0.35rem 0.5rem',
                  fontSize: '10px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--cnas-text-muted)',
                }}
              >
                Switch Active Case
              </div>
              {cases.map((c) => (
                <div
                  key={c.id}
                  onClick={() => {
                    setActiveCase(c);
                    setIsCaseMenuOpen(false);
                  }}
                  style={{
                    padding: '0.65rem',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    backgroundColor: c.id === activeCase.id ? 'var(--cnas-surface-container)' : 'transparent',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px',
                    marginBottom: '2px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                      {c.caseNumber}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--cnas-verified)', fontWeight: 600 }}>
                      {c.status}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--cnas-text-primary)' }}>
                    {c.title}
                  </span>
                </div>
              ))}
              <div style={{ height: '1px', backgroundColor: 'var(--cnas-border)', margin: '4px 0' }} />
              <button
                onClick={() => {
                  setActiveTab('cases');
                  setIsCaseMenuOpen(false);
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--cnas-blue)',
                  fontSize: '12px',
                  fontWeight: 600,
                }}
              >
                <FolderOpen size={14} />
                <span>View All Authorized Cases</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Center Section: Global Search Bar */}
      <div style={{ flex: '1', maxWidth: '460px', margin: '0 1.5rem' }}>
        <button
          onClick={openSearch}
          style={{
            width: '100%',
            height: '36px',
            padding: '0 0.85rem',
            backgroundColor: 'var(--cnas-surface-subtle)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            transition: 'border-color var(--transition-fast)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--cnas-text-muted)' }}>
            <Search size={16} />
            <span style={{ fontSize: '12px' }}>Search entities, documents, cases, events...</span>
          </div>
          <kbd
            style={{
              fontFamily: 'var(--font-code)',
              fontSize: '10px',
              color: 'var(--cnas-text-muted)',
              backgroundColor: 'var(--cnas-surface)',
              border: '1px solid var(--cnas-border)',
              padding: '2px 5px',
              borderRadius: 'var(--radius-xs)',
              boxShadow: 'var(--shadow-xs)',
            }}
          >
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right Section: Jobs Drawer, Notifications, User Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          {/* Ingestion & Extraction Jobs Drawer Trigger */}
          <button
            onClick={onOpenJobsDrawer}
            style={{
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 'var(--radius-md)',
              color: 'var(--cnas-text-secondary)',
            }}
            title="Live Ingestion & Analysis Jobs"
          >
            <Activity size={18} />
          </button>

          {/* Notifications */}
          <button
            style={{
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 'var(--radius-md)',
              color: 'var(--cnas-text-secondary)',
              position: 'relative',
            }}
            title="Notifications"
          >
            <Bell size={18} />
            <span
              style={{
                position: 'absolute',
                top: '7px',
                right: '7px',
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: 'var(--cnas-blue)',
              }}
            />
          </button>
        </div>

        <div style={{ height: '24px', width: '1px', backgroundColor: 'var(--cnas-border)' }} />

        {/* Authenticated Investigator Profile */}
        <div style={{ position: 'relative' }}>
          <div
            onClick={() => setIsUserMenuOpen((prev) => !prev)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              cursor: 'pointer',
              padding: '0.25rem',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'right' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--cnas-text-primary)' }}>
                {currentUser?.name}
              </span>
              <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>
                {currentUser?.role}
              </span>
            </div>
            <img
              src={currentUser?.avatarUrl}
              alt={currentUser?.name}
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                objectFit: 'cover',
                border: '2px solid var(--cnas-surface-high)',
              }}
            />
          </div>

          {isUserMenuOpen && (
            <div
              style={{
                position: 'absolute',
                top: '115%',
                right: 0,
                width: '240px',
                backgroundColor: 'var(--cnas-surface)',
                border: '1px solid var(--cnas-border)',
                borderRadius: 'var(--radius-xl)',
                boxShadow: 'var(--shadow-lg)',
                padding: '0.5rem',
                zIndex: 100,
              }}
            >
              <div style={{ padding: '0.5rem', borderBottom: '1px solid var(--cnas-border)' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                  {currentUser?.name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                  Badge: {currentUser?.badgeNumber}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', marginTop: '2px' }}>
                  Unit: {currentUser?.unit}
                </div>
              </div>
              <button
                onClick={() => {
                  logout();
                  setIsUserMenuOpen(false);
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--cnas-risk)',
                  fontSize: '12px',
                  fontWeight: 600,
                  marginTop: '4px',
                }}
              >
                <LogOut size={14} />
                <span>Log Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
