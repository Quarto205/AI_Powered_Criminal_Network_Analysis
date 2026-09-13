import React, { useState } from 'react';
import { AppDomain, SystemRole, SystemHealthStatus, CaseDetails } from './types/shell';
import { AppShell } from './components/shell/AppShell';
import { CaseShell } from './components/shell/CaseShell';
import { GlobalSearchModal } from './components/search/GlobalSearchModal';
import { mockActiveCase, mockCaseNotFoundResponse, mockCasesList } from './mocks/caseMock';
import { CaseSearchResult, EntitySearchResult } from './types/search';

export const App: React.FC = () => {
  const [activeDomain, setActiveDomain] = useState<AppDomain>('cases');
  const [currentRole, setCurrentRole] = useState<SystemRole>('INVESTIGATOR');
  const [healthStatus, setHealthStatus] = useState<SystemHealthStatus>('NORMAL');
  const [simulateCaseNotFound, setSimulateCaseNotFound] = useState<boolean>(false);
  const [activeCaseId, setActiveCaseId] = useState<string>(mockActiveCase.case_id);
  const [isGlobalSearchOpen, setIsGlobalSearchOpen] = useState<boolean>(false);
  const [selectedEntityIdFromSearch, setSelectedEntityIdFromSearch] = useState<string | null>(null);

  const selectedCase = mockCasesList.find((c) => c.case_id === activeCaseId) || mockActiveCase;
  const activeCase: CaseDetails | null = simulateCaseNotFound ? null : selectedCase;

  const handleSelectCase = (caseItem: CaseSearchResult) => {
    setActiveCaseId(caseItem.case_id);
    setActiveDomain('cases');
    setSimulateCaseNotFound(false);
  };

  const handleSelectEntity = (entity: EntitySearchResult) => {
    setActiveCaseId(entity.case_id);
    setSelectedEntityIdFromSearch(entity.entity_id);
    setActiveDomain('cases');
    setSimulateCaseNotFound(false);
  };

  return (
    <AppShell
      currentRole={currentRole}
      healthStatus={healthStatus}
      activeDomain={activeDomain}
      onRoleChange={setCurrentRole}
      onHealthStatusChange={setHealthStatus}
      onSelectDomain={setActiveDomain}
      onOpenGlobalSearch={() => setIsGlobalSearchOpen(true)}
    >
      {/* Verification Simulation Strip for Testing RBAC & 404 */}
      <div className="verification-bar" role="toolbar" aria-label="Step 1 Test Controls">
        <span className="verification-tag">STEP 1 VERIFICATION HARNESS</span>
        <div className="verification-controls">
          <button
            type="button"
            className={`verification-btn ${!simulateCaseNotFound ? 'verification-btn-active' : ''}`}
            onClick={() => setSimulateCaseNotFound(false)}
            aria-pressed={!simulateCaseNotFound}
          >
            Authorized Case ({selectedCase.case_code})
          </button>
          <button
            type="button"
            className={`verification-btn ${simulateCaseNotFound ? 'verification-btn-active' : ''}`}
            onClick={() => setSimulateCaseNotFound(true)}
            aria-pressed={simulateCaseNotFound}
          >
            Simulate 404 (Stealth Auth)
          </button>
        </div>
      </div>

      {/* Domain Routing */}
      {activeDomain === 'cases' && (
        <CaseShell
          caseData={activeCase}
          currentUserRole={currentRole}
          onReturnToCases={() => setSimulateCaseNotFound(false)}
          notFoundRequestId={mockCaseNotFoundResponse.request_id}
          selectedEntityId={selectedEntityIdFromSearch}
        />
      )}

      {activeDomain === 'search' && (
        <section className="case-tab-viewport" aria-label="Global Search Domain">
          <div className="placeholder-panel">
            <div className="placeholder-header">
              <span className="placeholder-badge">DOMAIN PLACEHOLDER</span>
              <h3 className="placeholder-title">Cross-Case Global Search</h3>
            </div>
            <p className="placeholder-text">
              System Administrator cross-case entity and phone number mapping (04_API_SPEC.md Section 4.2 /api/v1/search). Standard users receive empty restricted arrays.
            </p>
            <div style={{ marginTop: '16px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setActiveDomain('cases')}
              >
                Return to Active Case
              </button>
            </div>
          </div>
        </section>
      )}

      {activeDomain === 'jobs' && (
        <section className="case-tab-viewport" aria-label="Jobs Tracker Domain">
          <div className="placeholder-panel">
            <div className="placeholder-header">
              <span className="placeholder-badge">DOMAIN PLACEHOLDER</span>
              <h3 className="placeholder-title">Asynchronous Jobs Tracker</h3>
            </div>
            <p className="placeholder-text">
              Background task pipeline monitoring for PDF OCR, NLP entity extraction, and GNN inference runs (04_API_SPEC.md & 09_NAMING_CONVENTIONS.md).
            </p>
            <div style={{ marginTop: '16px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setActiveDomain('cases')}
              >
                Return to Active Case
              </button>
            </div>
          </div>
        </section>
      )}

      {activeDomain === 'settings' && (
        <section className="case-tab-viewport" aria-label="Settings Domain">
          <div className="placeholder-panel">
            <div className="placeholder-header">
              <span className="placeholder-badge">DOMAIN PLACEHOLDER</span>
              <h3 className="placeholder-title">Workspace Security & System Settings</h3>
            </div>
            <p className="placeholder-text">
              Cryptographic boundary verification, environment configuration (SEC-001), and log redaction policies (07_AUTH_SECURITY.md).
            </p>
            <div style={{ marginTop: '16px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setActiveDomain('cases')}
              >
                Return to Active Case
              </button>
            </div>
          </div>
        </section>
      )}
      {/* Global Search Modal Overlay (Section 19, 24, 84) */}
      <GlobalSearchModal
        isOpen={isGlobalSearchOpen}
        onClose={() => setIsGlobalSearchOpen(false)}
        onSelectCase={handleSelectCase}
        onSelectEntity={handleSelectEntity}
      />
    </AppShell>
  );
};
