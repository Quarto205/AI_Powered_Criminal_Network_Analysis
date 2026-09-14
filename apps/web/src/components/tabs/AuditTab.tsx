/**
 * Case Audit Ledger Tab Component
 * Strictly adheres to 07_AUTH_SECURITY.md and 02_DATABASE_SCHEMA.md (audit_logs table).
 */

import React from 'react';
import { AuditPanel } from '../panels/AuditPanel';
import { useCase } from '../../context/CaseContext';

export const AuditTab: React.FC = () => {
  const { activeCaseId, currentRole } = useCase();

  return (
    <div style={{ height: '100%', overflow: 'hidden' }}>
      <AuditPanel caseId={activeCaseId ?? undefined} currentRole={currentRole} />
    </div>
  );
};

