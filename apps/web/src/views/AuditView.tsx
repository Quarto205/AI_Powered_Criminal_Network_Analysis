import React from 'react';
import { MOCK_AUDIT_LOGS } from '../mocks/data';
import { Badge } from '../components/ui/Badge';
import { ShieldCheck, Download, Filter, Lock } from 'lucide-react';

export const AuditView: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '2px' }}>
            <ShieldCheck size={18} color="var(--cnas-navy)" />
            <h1 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--cnas-navy)' }}>
              Compliance & Chain-of-Custody Audit Ledger
            </h1>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--cnas-text-muted)' }}>
            Immutable evidentiary audit log compliant with Indian Evidence Act Section 65B
          </span>
        </div>

        <button
          onClick={() => alert('Certified Audit Ledger Exported (SHA-256 Verified)')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.5rem 1rem',
            backgroundColor: 'var(--cnas-navy)',
            color: '#ffffff',
            borderRadius: 'var(--radius-lg)',
            fontSize: '12px',
            fontWeight: 600,
            boxShadow: 'var(--shadow-xs)',
          }}
        >
          <Download size={15} />
          <span>Export Certified Log</span>
        </button>
      </div>

      {/* Audit Table */}
      <div
        style={{
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-xs)',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--cnas-surface-subtle)', borderBottom: '1px solid var(--cnas-border)', color: 'var(--cnas-text-muted)', textTransform: 'uppercase', fontSize: '10px', letterSpacing: '0.05em' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Timestamp</th>
              <th style={{ padding: '0.75rem 1rem' }}>Investigator</th>
              <th style={{ padding: '0.75rem 1rem' }}>Action</th>
              <th style={{ padding: '0.75rem 1rem' }}>Operational Details</th>
              <th style={{ padding: '0.75rem 1rem' }}>Audit Hash</th>
              <th style={{ padding: '0.75rem 1rem' }}>Network Origin</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_AUDIT_LOGS.map((log) => (
              <tr key={log.id} style={{ borderBottom: '1px solid var(--cnas-border)' }}>
                <td style={{ padding: '0.85rem 1rem', fontFamily: 'var(--font-code)', color: 'var(--cnas-navy)', fontWeight: 600 }}>
                  {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} IST
                </td>
                <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>
                  {log.investigatorName}
                </td>
                <td style={{ padding: '0.85rem 1rem' }}>
                  <Badge variant="navy" size="sm">
                    {log.action}
                  </Badge>
                </td>
                <td style={{ padding: '0.85rem 1rem', color: 'var(--cnas-text-secondary)', maxWidth: '340px' }}>
                  {log.details}
                </td>
                <td style={{ padding: '0.85rem 1rem', fontFamily: 'var(--font-code)', color: 'var(--cnas-blue)', fontSize: '11px' }}>
                  {log.hash}
                </td>
                <td style={{ padding: '0.85rem 1rem', color: 'var(--cnas-text-muted)', fontSize: '11px' }}>
                  {log.ipAddress}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
