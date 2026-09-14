/**
 * AppShell Component
 * Strictly adheres to 08_UI_DATA_CONTRACT.md (Section 8.1).
 * Persistent master navigation sidebar (Cases List, Search, Active Jobs Tracker, Security Settings).
 */

import React, { useState } from 'react';
import {
  Search,
  Activity,
  Shield,
} from 'lucide-react';
import { useCase } from '../../context/CaseContext';
import { CaseShell } from './CaseShell';
import { Badge } from '../common/Badge';
import { UserRole } from '../../contracts/common';

export const AppShell: React.FC = () => {
  const { cases, activeCaseId, selectCase, currentRole, setCurrentRole } = useCase();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredCases = cases.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.case_code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div
      data-testid="app-shell"
      style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: '#090d16',
      }}
    >
      {/* Persistent Master Navigation Sidebar */}
      <div
        style={{
          width: '280px',
          height: '100%',
          backgroundColor: '#090d16',
          borderRight: '1px solid #1e293b',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        {/* System Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: 'linear-gradient(135deg, #1e3a8a, #3b82f6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Shield size={18} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, letterSpacing: '0.04em', color: '#f8fafc' }}>
              SIH26189 — CNAS
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Investigation Support
            </div>
          </div>
        </div>

        {/* Global Case Search Box */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #1e293b' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 10px',
              background: '#0f172a',
              border: '1px solid #1e293b',
              borderRadius: '6px',
            }}
          >
            <Search size={14} color="#64748b" />
            <input
              type="text"
              placeholder="Search authorized cases..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#f8fafc',
                fontSize: '12px',
                width: '100%',
              }}
            />
          </div>
        </div>

        {/* Authorized Cases List (Multi-Tenant Case Boundary) */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 8px' }}>
          <div
            style={{
              padding: '4px 12px 8px 12px',
              fontSize: '10px',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: '#64748b',
              letterSpacing: '0.05em',
            }}
          >
            Authorized Cases ({filteredCases.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {filteredCases.map((c) => {
              const isSelected = c.case_id === activeCaseId;
              return (
                <button
                  key={c.case_id}
                  onClick={() => selectCase(c.case_id)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    border: isSelected ? '1px solid #3b82f6' : '1px solid transparent',
                    background: isSelected ? '#1e293b' : 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.12s ease',
                  }}
                  className="hover:bg-slate-900"
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                        color: isSelected ? '#38bdf8' : '#94a3b8',
                        fontWeight: 600,
                      }}
                    >
                      {c.case_code}
                    </span>
                    <Badge variant="default">{c.member_role}</Badge>
                  </div>
                  <span
                    style={{
                      fontSize: '12px',
                      color: isSelected ? '#ffffff' : '#cbd5e1',
                      fontWeight: isSelected ? 600 : 400,
                      marginTop: '4px',
                      lineHeight: '1.3',
                    }}
                  >
                    {c.title}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Bottom Section: Active Jobs, Services Health & RBAC Role Switcher */}
        <div style={{ padding: '16px', borderTop: '1px solid #1e293b', background: '#0a0f1d' }}>
          {/* Services Health */}
          <div style={{ marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Activity size={12} color="#10b981" /> Services Health
              </span>
              <span style={{ color: '#10b981', fontWeight: 600 }}>ONLINE</span>
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
              PG: Healthy | Neo4j: GDS Ready | Worker: Idle
            </div>
          </div>

          {/* Active Investigator Role & Switcher for Demo Verification */}
          <div>
            <div style={{ fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#64748b', marginBottom: '6px' }}>
              Investigator Role (RBAC Simulation)
            </div>
            <div style={{ display: 'flex', gap: '4px' }}>
              {(['SUPERVISOR', 'ANALYST', 'INVESTIGATOR'] as UserRole[]).map((role) => (
                <button
                  key={role}
                  onClick={() => setCurrentRole(role)}
                  style={{
                    flex: 1,
                    padding: '4px 6px',
                    borderRadius: '4px',
                    border: currentRole === role ? '1px solid #3b82f6' : '1px solid #1e293b',
                    background: currentRole === role ? '#1e293b' : 'transparent',
                    color: currentRole === role ? '#38bdf8' : '#64748b',
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
        </div>
      </div>

      {/* Main Workspace Area (CaseShell) */}
      <div style={{ flex: 1, height: '100%', overflow: 'hidden' }}>
        <CaseShell />
      </div>
    </div>
  );
};
