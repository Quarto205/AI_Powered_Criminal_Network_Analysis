/**
 * Unit & Integration Tests for AlertsPanel Component
 * Strictly adheres to 01_SHARED_TYPES.md, 04_API_SPEC.md, 05_AI_CONTRACTS.md, and 08_UI_DATA_CONTRACT.md.
 *
 * Dev B — Step 4:
 * Covers all 15 minimum requirements for AlertsPanel:
 * 1. Alert cards render
 * 2. Severity renders correctly
 * 3. Status renders correctly
 * 4. Motif type renders correctly
 * 5. Contributing entities render
 * 6. Financial cycle renders
 * 7. Communication burst renders
 * 8. Fan-out/fan-in renders
 * 9. Bridge/cut-point renders
 * 10. Insufficient Temporal Data appears for incomplete temporal data
 * 11. Severity filtering works
 * 12. Status filtering works
 * 13. Focus on Canvas uses existing selection architecture
 * 14. Mark Reviewed changes NEW -> REVIEWED
 * 15. Graph state is preserved
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { AlertsPanel } from '../components/panels/AlertsPanel';
import { CaseProvider } from '../context/CaseContext';
import { SelectionProvider, useSelection } from '../context/SelectionContext';
import { DEMO_ALERTS } from '../fixtures/demoAlerts';
import { MOCK_GRAPH_NODES } from '../mocks/graphMock';

describe('AlertsPanel Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Alert cards render
  it('1. renders alert cards and header with total count', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    expect(screen.getByTestId('alerts-panel')).toBeInTheDocument();
    expect(screen.getByTestId('alerts-header-title')).toHaveTextContent('Pattern & Motif Alerts');
    expect(screen.getByTestId('alerts-count-badge')).toHaveTextContent('5 Alerts');
    expect(screen.getByTestId('alert-card-alt-001')).toBeInTheDocument();
    expect(screen.getByTestId('alert-card-alt-002')).toBeInTheDocument();
  });

  // 2. Severity renders correctly
  it('2. renders alert severity badges accurately', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const highSeverityCards = screen.getAllByTestId('alert-severity-badge');
    expect(highSeverityCards[0]).toHaveTextContent('HIGH');
    expect(highSeverityCards[2]).toHaveTextContent('MEDIUM');
    expect(highSeverityCards[4]).toHaveTextContent('LOW');
  });

  // 3. Status renders correctly
  it('3. renders alert status badges accurately', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const statusBadges = screen.getAllByTestId('alert-status-badge');
    expect(statusBadges[0]).toHaveTextContent('NEW');
    expect(statusBadges[2]).toHaveTextContent('REVIEWED');
  });

  // 4. Motif type renders correctly
  it('4. renders recognized motif categories with icons and descriptions', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const motifBadges = screen.getAllByTestId('alert-motif-type');
    expect(motifBadges.length).toBe(5);
  });

  // 5. Contributing entities render
  it('5. renders contributing entities list with canonical names and roles', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const card1 = screen.getByTestId('alert-card-alt-001');
    expect(within(card1).getByTestId('entity-badge-node-bank-1')).toHaveTextContent('HDFC-XXXX8921(ORIGIN)');
    expect(within(card1).getByTestId('entity-badge-node-bank-2')).toHaveTextContent('ICICI-XXXX4410(INTERMEDIARY)');
    expect(within(card1).getByTestId('entity-badge-node-bank-3')).toHaveTextContent('SBI-XXXX1102(CASH_OUT)');
  });

  // 6. Financial cycle renders
  it('6. renders financial cycle motif (A -> B -> C -> A)', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const card1 = screen.getByTestId('alert-card-alt-001');
    expect(card1).toHaveTextContent(/Financial Transaction Cycle \(A → B → C → A\)/i);
    expect(card1).toHaveTextContent(/Potential closed funds cycle detected/i);
    expect(card1).toHaveTextContent('Window: 72 hrs');
  });

  // 7. Communication burst renders
  it('7. renders communication burst motif', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const card2 = screen.getByTestId('alert-card-alt-002');
    expect(card2).toHaveTextContent(/Communication Burst/i);
    expect(card2).toHaveTextContent(/Anomalous call frequency surge/i);
  });

  // 8. Fan-out / fan-in renders
  it('8. renders rapid fan-out / fan-in disbursement motif', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const card4 = screen.getByTestId('alert-card-alt-004');
    expect(card4).toHaveTextContent(/Rapid Fan-Out \/ Fan-In/i);
    expect(card4).toHaveTextContent(/transferred funds to 5 recipient accounts within 10 minutes/i);
  });

  // 9. Bridge / cut-point renders
  it('9. renders high-betweenness bridge node / cut-point motif', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const card3 = screen.getByTestId('alert-card-alt-003');
    expect(card3).toHaveTextContent(/Bridge Node \/ Cut-Point/i);
    expect(card3).toHaveTextContent(/exhibits top-percentile betweenness centrality/i);
  });

  // 10. Insufficient Temporal Data appears for incomplete temporal data
  it('10. explicitly displays "Insufficient Temporal Data" when timestamps are missing or incomplete', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    // alt-005 has temporal_data_incomplete: true
    const card5 = screen.getByTestId('alert-card-alt-005');
    expect(card5).toBeInTheDocument();
    expect(card5).toHaveTextContent(/Insufficient Temporal Data/i);
    expect(screen.getByTestId('insufficient-temporal-badge')).toBeInTheDocument();
  });

  // 11. Severity filtering works
  it('11. filters alerts correctly by severity level', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const severitySelect = screen.getByTestId('filter-severity');
    fireEvent.change(severitySelect, { target: { value: 'HIGH' } });

    // In DEMO_ALERTS, alt-001, alt-002, alt-004 are HIGH (3 items)
    expect(screen.getByTestId('alerts-count-badge')).toHaveTextContent('3 Alerts');
    expect(screen.getByTestId('alert-card-alt-001')).toBeInTheDocument();
    expect(screen.getByTestId('alert-card-alt-002')).toBeInTheDocument();
    expect(screen.getByTestId('alert-card-alt-004')).toBeInTheDocument();
    expect(screen.queryByTestId('alert-card-alt-003')).not.toBeInTheDocument();
  });

  // 12. Status filtering works
  it('12. filters alerts correctly by status (NEW vs REVIEWED)', () => {
    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} />
      </CaseProvider>
    );

    const statusSelect = screen.getByTestId('filter-status');
    fireEvent.change(statusSelect, { target: { value: 'REVIEWED' } });

    // Only alt-003 is initially REVIEWED
    expect(screen.getByTestId('alerts-count-badge')).toHaveTextContent('1 Alerts');
    expect(screen.getByTestId('alert-card-alt-003')).toBeInTheDocument();
    expect(screen.queryByTestId('alert-card-alt-001')).not.toBeInTheDocument();
  });

  // 13. Focus on Canvas uses existing selection architecture
  it('13. handles Focus on Canvas: invokes callback and selects contributing node via SelectionContext', () => {
    const handleFocus = vi.fn();

    const Harness = () => {
      const { selectedNode } = useSelection();
      return (
        <div>
          <span data-testid="active-selected-node">{selectedNode?.id ?? 'none'}</span>
          <AlertsPanel alerts={DEMO_ALERTS.alerts} onFocusEntities={handleFocus} />
        </div>
      );
    };

    render(
      <CaseProvider>
        <SelectionProvider>
          <Harness />
        </SelectionProvider>
      </CaseProvider>
    );

    const focusBtns = screen.getAllByTestId('focus-canvas-btn');
    fireEvent.click(focusBtns[0]); // alt-001 has node-bank-1 as first entity

    expect(handleFocus).toHaveBeenCalledWith(['node-bank-1', 'node-bank-2', 'node-bank-3']);
    expect(screen.getByTestId('active-selected-node')).toHaveTextContent('node-bank-1');
  });

  // 14. Mark Reviewed changes NEW -> REVIEWED
  it('14. handles Mark Reviewed: transitions status from NEW to REVIEWED', async () => {
    const handleAlertReviewed = vi.fn();

    render(
      <CaseProvider>
        <AlertsPanel alerts={DEMO_ALERTS.alerts} onAlertReviewed={handleAlertReviewed} />
      </CaseProvider>
    );

    // alt-001 is NEW
    const card1 = screen.getByTestId('alert-card-alt-001');
    const markBtn = card1.querySelector('[data-testid="mark-reviewed-btn"]');
    expect(markBtn).toBeInTheDocument();

    if (markBtn) {
      fireEvent.click(markBtn);
    }

    expect(handleAlertReviewed).toHaveBeenCalledWith('alt-001');

    // Status badge on card1 updates to REVIEWED
    await waitFor(() => {
      const statusBadge = card1.querySelector('[data-testid="alert-status-badge"]');
      expect(statusBadge).toHaveTextContent('REVIEWED');
    });

    // Mark Reviewed button disappears once reviewed
    expect(card1.querySelector('[data-testid="mark-reviewed-btn"]')).not.toBeInTheDocument();
  });

  // 15. Graph state is preserved
  it('15. operates alongside SelectionContext without resetting graph selection state', () => {
    const Harness = () => {
      const { selectNode, selectedNode } = useSelection();
      return (
        <div>
          <button data-testid="select-tariq-btn" onClick={() => selectNode(MOCK_GRAPH_NODES[0].data)}>
            Select Tariq
          </button>
          <span data-testid="current-node-selection">{selectedNode?.id ?? 'none'}</span>
          <AlertsPanel alerts={DEMO_ALERTS.alerts} />
        </div>
      );
    };

    render(
      <CaseProvider>
        <SelectionProvider>
          <Harness />
        </SelectionProvider>
      </CaseProvider>
    );

    // Initial select
    fireEvent.click(screen.getByTestId('select-tariq-btn'));
    expect(screen.getByTestId('current-node-selection')).toHaveTextContent('node-person-1');

    // Filter alerts in panel
    fireEvent.change(screen.getByTestId('filter-severity'), { target: { value: 'HIGH' } });

    // Node selection remains intact
    expect(screen.getByTestId('current-node-selection')).toHaveTextContent('node-person-1');
  });
});
