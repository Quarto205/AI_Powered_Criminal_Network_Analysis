/**
 * Pattern List & Suspicious Motif Alerts Tab Component
 * Strictly adheres to 05_AI_CONTRACTS.md and 08_UI_DATA_CONTRACT.md.
 * Non-accusatory language: Pattern Alert, Priority Ranking, Investigative Lead.
 */

import React from 'react';
import { AlertsPanel } from '../panels/AlertsPanel';

export const AlertsTab: React.FC<{ onNavigateToGraph?: () => void }> = ({ onNavigateToGraph }) => {
  return (
    <div style={{ height: '100%', width: '100%', overflow: 'hidden' }}>
      <AlertsPanel
        onFocusEntities={() => {
          if (onNavigateToGraph) {
            onNavigateToGraph();
          }
        }}
      />
    </div>
  );
};
