import React from 'react';
import { useCase } from '../context/CaseContext';
import { Badge } from '../components/ui/Badge';
import { FolderOpen, ArrowRight, Shield, Users, FileText, AlertTriangle } from 'lucide-react';

export const CasesView: React.FC = () => {
  const { cases, activeCase, setActiveCase, setActiveTab } = useCase();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <FolderOpen size={18} color="var(--cnas-blue)" />
          <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cnas-blue)' }}>
            Authorised Case Dossiers
          </span>
        </div>
        <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--cnas-navy)' }}>
          Active Investigation Matters
        </h1>
        <p style={{ fontSize: '13px', color: 'var(--cnas-text-secondary)', marginTop: '4px' }}>
          Restricted to authorized credentials of Inspector Ananya Roy (Special Cell / Crime Branch)
        </p>
      </div>

      {/* Case Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.25rem' }}>
        {cases.map((c) => {
          const isActive = c.id === activeCase.id;
          return (
            <div
              key={c.id}
              onClick={() => {
                setActiveCase(c);
                setActiveTab('overview');
              }}
              style={{
                backgroundColor: 'var(--cnas-surface)',
                border: isActive ? '2px solid var(--cnas-blue)' : '1px solid var(--cnas-border)',
                borderRadius: 'var(--radius-xl)',
                padding: '1.5rem',
                boxShadow: isActive ? 'var(--shadow-md)' : 'var(--shadow-xs)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '1.25rem',
                transition: 'all var(--transition-fast)',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-code)',
                      fontSize: '11px',
                      fontWeight: 700,
                      backgroundColor: 'var(--cnas-surface-subtle)',
                      border: '1px solid var(--cnas-border)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--cnas-navy)',
                    }}
                  >
                    {c.caseNumber}
                  </span>
                  <Badge variant="verified" size="sm" pulse={c.status === 'ACTIVE'}>
                    {c.status} INVESTIGATION
                  </Badge>
                </div>

                <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--cnas-navy)', lineHeight: 1.3 }}>
                  {c.title}
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--cnas-text-secondary)', marginTop: '6px', lineHeight: 1.45 }}>
                  {c.description}
                </p>
              </div>

              <div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr',
                    gap: '0.5rem',
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--cnas-surface-subtle)',
                    border: '1px solid var(--cnas-border)',
                    marginBottom: '1rem',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>Entities</span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--cnas-navy)' }}>{c.entityCount}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>Evidence</span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--cnas-navy)' }}>{c.evidenceCount}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>Leads</span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--cnas-risk)' }}>{c.criticalLeadsCount}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                    {c.jurisdiction}
                  </span>
                  <span
                    style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      color: 'var(--cnas-blue)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <span>Open Case</span>
                    <ArrowRight size={14} />
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
