import React from 'react';
import { SystemRole } from '../../types/shell';

export interface PermissionGateProps {
  currentRole: SystemRole;
  allowedRoles: SystemRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * UI visibility boundary for role-based features (07_AUTH_SECURITY.md).
 * 
 * IMPORTANT ARCHITECTURAL NOTE:
 * This component controls client-side visual display only and is NOT a security boundary.
 * Authoritative security and access control are strictly enforced server-side by the API layer.
 */
export const PermissionGate: React.FC<PermissionGateProps> = ({
  currentRole,
  allowedRoles,
  children,
  fallback
}) => {
  const isAuthorized = allowedRoles.includes(currentRole);

  if (isAuthorized) {
    return <>{children}</>;
  }

  if (fallback !== undefined) {
    return <>{fallback}</>;
  }

  return (
    <div
      className="restricted-banner"
      role="status"
      aria-label="Restricted View"
    >
      <div className="restricted-header">
        <span className="restricted-tag">[RESTRICTED]</span>
        <h4 className="restricted-title">Access Restricted</h4>
      </div>
      <p className="restricted-message">
        Access to this view requires elevated permissions (Allowed: {allowedRoles.join(', ')}). Your active role is{' '}
        <strong>{currentRole}</strong>.
      </p>
      <p className="restricted-note">
        UI visibility gate active. Authoritative permissions are validated at the backend API layer.
      </p>
    </div>
  );
};
