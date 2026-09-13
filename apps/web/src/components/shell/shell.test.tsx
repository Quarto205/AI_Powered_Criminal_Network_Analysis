import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AppShell } from './AppShell';
import { CaseShell } from './CaseShell';
import { PermissionGate } from './PermissionGate';
import { CaseNotFound } from './CaseNotFound';
import { mockActiveCase } from '../../mocks/caseMock';

describe('AppShell Component', () => {
  it('renders application header, active user role, health status, and main children', () => {
    render(
      <AppShell
        currentRole="INVESTIGATOR"
        healthStatus="NORMAL"
        activeDomain="cases"
        onSelectDomain={() => {}}
      >
        <div data-testid="viewport-content">Test Child Content</div>
      </AppShell>
    );

    expect(screen.getByText('SIH26189')).toBeInTheDocument();
    expect(screen.getByText('AI-Powered Criminal Network Analysis System')).toBeInTheDocument();
    expect(screen.getByText('INVESTIGATOR')).toBeInTheDocument();
    expect(screen.getByText('NORMAL')).toBeInTheDocument();
    expect(screen.getByTestId('viewport-content')).toBeInTheDocument();
  });

  it('renders degraded system health status with explicit text representation', () => {
    render(
      <AppShell
        currentRole="ANALYST"
        healthStatus="DEGRADED — Provider Offline"
        activeDomain="cases"
        onSelectDomain={() => {}}
      >
        <div>Content</div>
      </AppShell>
    );

    expect(screen.getByText('DEGRADED — Provider Offline')).toBeInTheDocument();
  });

  it('triggers onOpenGlobalSearch via Header and Sidebar search buttons', () => {
    const onOpenGlobalSearch = vi.fn();

    render(
      <AppShell
        currentRole="INVESTIGATOR"
        healthStatus="NORMAL"
        activeDomain="cases"
        onSelectDomain={() => {}}
        onOpenGlobalSearch={onOpenGlobalSearch}
      >
        <div>Content</div>
      </AppShell>
    );

    // Header search button
    const headerSearchBtn = screen.getByRole('button', { name: /Search authorized cases/i });
    expect(headerSearchBtn).toBeInTheDocument();
    fireEvent.click(headerSearchBtn);
    expect(onOpenGlobalSearch).toHaveBeenCalledTimes(1);

    // Sidebar search button
    const sidebarSearchBtn = screen.getByRole('button', { name: /Global Search/i });
    fireEvent.click(sidebarSearchBtn);
    expect(onOpenGlobalSearch).toHaveBeenCalledTimes(2);
  });

  it('triggers onOpenGlobalSearch on universal "/" shortcut, but ignores typing inside editable controls', () => {
    const onOpenGlobalSearch = vi.fn();

    render(
      <AppShell
        currentRole="INVESTIGATOR"
        healthStatus="NORMAL"
        activeDomain="cases"
        onSelectDomain={() => {}}
        onOpenGlobalSearch={onOpenGlobalSearch}
      >
        <input data-testid="test-input" type="text" />
      </AppShell>
    );

    // 1. Pressing '/' on document triggers global search
    fireEvent.keyDown(window, { key: '/' });
    expect(onOpenGlobalSearch).toHaveBeenCalledTimes(1);

    // 2. Typing '/' inside an input MUST NOT trigger global search
    const input = screen.getByTestId('test-input');
    input.focus();
    fireEvent.keyDown(input, { key: '/' });
    expect(onOpenGlobalSearch).toHaveBeenCalledTimes(1); // Still 1
  });
});

describe('CaseShell Component', () => {
  it('renders case code, title, jurisdiction, lifecycle state, and counts', () => {
    render(
      <CaseShell
        caseData={mockActiveCase}
        currentUserRole="INVESTIGATOR"
      />
    );

    expect(screen.getByText('DL-2026-CR-0192')).toBeInTheDocument();
    expect(screen.getByText(mockActiveCase.title)).toBeInTheDocument();
    expect(screen.getByText('Delhi NCR — Special Cell')).toBeInTheDocument();
    expect(screen.getAllByText('GRAPH_READY').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('14').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('48').length).toBeGreaterThanOrEqual(1);
  });

  it('switches tabs without page reload and preserves case context', () => {
    render(
      <CaseShell
        caseData={mockActiveCase}
        currentUserRole="INVESTIGATOR"
      />
    );

    // Initial tab is Overview
    expect(screen.getByText('Overview Workspace')).toBeInTheDocument();

    // Click Graph tab
    const graphTabBtn = screen.getByRole('tab', { name: /Graph/i });
    fireEvent.click(graphTabBtn);

    // Graph canvas is displayed, Overview is no longer active
    expect(screen.getByTestId('cytoscape-container')).toBeInTheDocument();
    expect(screen.getByText('EVIDENCE CLASSIFICATION')).toBeInTheDocument();
    expect(screen.queryByText('Overview Workspace')).not.toBeInTheDocument();

    // Case metadata remains intact
    expect(screen.getByText('DL-2026-CR-0192')).toBeInTheDocument();
  });

  it('renders GraphToolbar in Graph tab and updates graph upon search and filter interactions', () => {
    render(
      <CaseShell
        caseData={mockActiveCase}
        currentUserRole="INVESTIGATOR"
        initialTab="graph"
      />
    );

    // 1. Both GraphToolbar and GraphCanvas exist in the graph tab
    expect(screen.getByRole('toolbar', { name: /Graph visualization controls/i })).toBeInTheDocument();
    expect(screen.getByTestId('cytoscape-container')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search nodes in canvas...')).toBeInTheDocument();

    // 2. Search for non-existent node -> renders empty state
    const searchInput = screen.getByPlaceholderText('Search nodes in canvas...');
    fireEvent.change(searchInput, { target: { value: 'non-matching-query-xyz' } });

    expect(
      screen.getByText('No graph relationships available for current pivot.')
    ).toBeInTheDocument();

    // 3. Clear search -> restores canvas and legend
    const clearBtn = screen.getByRole('button', { name: /Clear search text/i });
    fireEvent.click(clearBtn);

    expect(screen.getByTestId('cytoscape-container')).toBeInTheDocument();
    expect(screen.getByText('EVIDENCE CLASSIFICATION')).toBeInTheDocument();

    // 4. Layout selector updates layout state
    const layoutSelect = screen.getByLabelText(/Layout:/i);
    fireEvent.change(layoutSelect, { target: { value: 'grid' } });
    expect(layoutSelect).toHaveValue('grid');
  });

  it('renders CaseSearchInput and pivots to graph tab with selected node on entity selection', () => {
    render(
      <CaseShell
        caseData={mockActiveCase}
        currentUserRole="INVESTIGATOR"
        initialTab="overview"
      />
    );

    // Starts on overview tab
    expect(screen.getByText('Overview Workspace')).toBeInTheDocument();

    // Find CaseSearchInput in header
    const caseSearchInput = screen.getByPlaceholderText('Search entities in active case…');
    expect(caseSearchInput).toBeInTheDocument();

    // Type 'Person B'
    fireEvent.change(caseSearchInput, { target: { value: 'Person B' } });

    // Option appears
    const option = screen.getByRole('option', { name: /Person B/i });
    expect(option).toBeInTheDocument();

    // Click option
    fireEvent.click(option);

    // Pivots to graph tab and renders selected bar
    expect(screen.getByTestId('cytoscape-container')).toBeInTheDocument();
    expect(screen.getByText('NODE: Person')).toBeInTheDocument();
    expect(screen.getByText('Person B')).toBeInTheDocument();
  });
});

describe('PermissionGate Component & Audit Security', () => {
  it('allows access for authorized SUPERVISOR role', () => {
    render(
      <PermissionGate currentRole="SUPERVISOR" allowedRoles={['SUPERVISOR']}>
        <div data-testid="supervisor-content">Sensitive Audit Ledger</div>
      </PermissionGate>
    );

    expect(screen.getByTestId('supervisor-content')).toBeInTheDocument();
    expect(screen.queryByText('[RESTRICTED]')).not.toBeInTheDocument();
  });

  it('blocks access for INVESTIGATOR role and renders restricted banner', () => {
    render(
      <PermissionGate currentRole="INVESTIGATOR" allowedRoles={['SUPERVISOR']}>
        <div data-testid="supervisor-content">Sensitive Audit Ledger</div>
      </PermissionGate>
    );

    expect(screen.queryByTestId('supervisor-content')).not.toBeInTheDocument();
    expect(screen.getByText('[RESTRICTED]')).toBeInTheDocument();
    expect(screen.getByText(/Access Restricted/i)).toBeInTheDocument();
  });

  it('blocks access for ANALYST role as well', () => {
    render(
      <PermissionGate currentRole="ANALYST" allowedRoles={['SUPERVISOR']}>
        <div data-testid="supervisor-content">Sensitive Audit Ledger</div>
      </PermissionGate>
    );

    expect(screen.queryByTestId('supervisor-content')).not.toBeInTheDocument();
    expect(screen.getByText('[RESTRICTED]')).toBeInTheDocument();
  });
});

describe('CaseNotFound (Stealth Authorization)', () => {
  it('renders generic 404 message without exposing case existence or authorization secrets', () => {
    render(<CaseNotFound requestId="req_test_123" />);

    expect(screen.getByText('Case Not Found')).toBeInTheDocument();
    expect(
      screen.getByText('The requested case resource could not be found or access is not authorized.')
    ).toBeInTheDocument();
    expect(screen.getByText('req_test_123')).toBeInTheDocument();

    // Invariant: no stack traces, no internal database mentions
    expect(screen.queryByText(/PostgreSQL/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Neo4j/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unauthorized/i)).not.toBeInTheDocument();
  });
});
