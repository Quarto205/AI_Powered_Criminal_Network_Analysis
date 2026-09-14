import React from 'react';

export interface CaseNotFoundProps {
  onReturnToCases?: () => void;
  requestId?: string;
}

/**
 * Generic Case Not Found state (06_WORKFLOWS.md Section 6.2).
 * 
 * Invariant:
 * To prevent case enumeration, unauthorized case access returns a generic 404.
 * This component intentionally obscures whether the case exists or whether
 * the user is merely unauthorized. No internal stack traces or backend diagnostics
 * are presented to the client.
 */
export const CaseNotFound: React.FC<CaseNotFoundProps> = ({
  onReturnToCases,
  requestId
}) => {
  return (
    <div className="case-not-found-container" role="region" aria-label="Case Not Found">
      <div className="case-not-found-card">
        <div className="case-not-found-badge" aria-hidden="true">
          STATUS 404
        </div>
        <h2 className="case-not-found-title">Case Not Found</h2>
        <p className="case-not-found-message">
          The requested case resource could not be found or access is not authorized.
        </p>
        <p className="case-not-found-subtext">
          Please verify the case reference code or confirm your case membership credentials with your unit supervisor.
        </p>

        {requestId && (
          <div className="case-not-found-meta">
            <span className="case-not-found-req-label">Diagnostics Request ID:</span>{' '}
            <code className="case-not-found-req-id">{requestId}</code>
          </div>
        )}

        {onReturnToCases && (
          <div className="case-not-found-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={onReturnToCases}
              aria-label="Return to active cases directory"
            >
              Return to Cases
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
