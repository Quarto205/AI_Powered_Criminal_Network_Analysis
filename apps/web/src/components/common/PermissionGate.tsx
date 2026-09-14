/**
 * PermissionGate Component
 * Strictly adheres to 07_AUTH_SECURITY.md (Section 7.1 RBAC Roles).
 * Ensures privileged views/actions are restricted to authorized roles (e.g., SUPERVISOR).
 */

import React from 'react';
import { ShieldAlert, Lock } from 'lucide-react';
import { UserRole } from '../../contracts/common';
import { useCase } from '../../context/CaseContext';

export interface PermissionGateProps {
  requiredRole?: UserRole | UserRole[];
  currentRole?: UserRole;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
  requiredRole = 'SUPERVISOR',
  currentRole: propRole,
  fallback,
  children,
}) => {
  let contextRole: UserRole | undefined;
  try {
    const caseCtx = useCase();
    contextRole = caseCtx.currentRole;
  } catch {
    // Context may not be present in isolated test scenarios
  }

  const effectiveRole = propRole ?? contextRole ?? 'INVESTIGATOR';

  const isAuthorized = Array.isArray(requiredRole)
    ? requiredRole.includes(effectiveRole)
    : effectiveRole === requiredRole;

  if (isAuthorized) {
    return <>{children}</>;
  }

  if (fallback !== undefined) {
    return <>{fallback}</>;
  }

  const requiredLabel = Array.isArray(requiredRole) ? requiredRole.join(' | ') : requiredRole;

  return (
    <div
      data-testid="permission-gate-restricted"
      style={{
        padding: '32px 24px',
        backgroundColor: '#0f172a',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '8px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        gap: '14px',
        maxWidth: '540px',
        margin: '32px auto',
      }}
    >
      <div
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <ShieldAlert size={22} color="#f87171" />
      </div>

      <div>
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', margin: '0 0 6px 0' }}>
          Access Restricted — Privileged Scope
        </h3>
        <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>
          Your current session role does not have authorization to view or export the case audit ledger.
          Audit inspection requires elevated operational credentials.
        </p>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 14px',
          backgroundColor: '#090d16',
          borderRadius: '6px',
          border: '1px solid #1e293b',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <span style={{ color: '#64748b' }}>Active Role:</span>
        <span data-testid="current-role-badge" style={{ color: '#f87171', fontWeight: 600 }}>
          {effectiveRole}
        </span>
        <span style={{ color: '#334155' }}>|</span>
        <span style={{ color: '#64748b' }}>Required:</span>
        <span data-testid="required-role-badge" style={{ color: '#10b981', fontWeight: 600 }}>
          {requiredLabel}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#64748b' }}>
        <Lock size={12} color="#64748b" />
        <span>Section 7.1 RBAC Enforcement Invariant</span>
      </div>
    </div>
  );
};
