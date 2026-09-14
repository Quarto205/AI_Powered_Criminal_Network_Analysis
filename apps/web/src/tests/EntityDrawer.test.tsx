/**
 * Focused Unit & Integration Tests for EntityDrawer Component
 * Validates DEV B — Step 2A requirements.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EntityDrawer } from '../components/drawers/EntityDrawer';
import { CaseProvider } from '../context/CaseContext';
import { SelectionProvider } from '../context/SelectionContext';
import { EntityTypes, RelationshipTypes } from '../types/contracts';
import {
  MOCK_GRAPH_NODES,
  MOCK_GRAPH_EDGES,
} from '../mocks/graphMock';
import { MOCK_CASE_CODE, MOCK_CASE_DETAIL } from '../mocks/caseMock';

describe('EntityDrawer Component Tests', () => {
  it('renders gracefully when no entity or edge is selected', () => {
    const handleClose = vi.fn();
    render(<EntityDrawer nodeData={null} edgeData={null} onClose={handleClose} />);

    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();
    expect(screen.getByTestId('no-selection-message')).toBeInTheDocument();
    expect(screen.getByText(/No entity or relationship selected/i)).toBeInTheDocument();

    // Close button works in empty state
    const closeBtn = screen.getByTestId('close-drawer-btn');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders entity header with canonical name, explicit text type, and status badges', () => {
    const node = MOCK_GRAPH_NODES[0]; // Tariq Khan (PERSON, UNDER_SURVEILLANCE)
    render(<EntityDrawer nodeData={node.data} />);

    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();
    expect(screen.getByText('Tariq Khan')).toBeInTheDocument();

    const typeBadge = screen.getByTestId('entity-type-badge');
    expect(typeBadge).toHaveTextContent(`Type: ${EntityTypes.PERSON}`);

    const statusBadge = screen.getByTestId('entity-status-badge');
    expect(statusBadge).toHaveTextContent('Status: UNDER_SURVEILLANCE');
  });

  it('renders masked canonical identifiers and protects sensitive PII', () => {
    const phoneNode = MOCK_GRAPH_NODES[3]; // +91 98110 XXXXX (PHONE)
    render(<EntityDrawer nodeData={phoneNode.data} />);

    const identSection = screen.getByTestId('entity-identifiers');
    expect(identSection).toBeInTheDocument();
    expect(screen.getByText('+91 98110 •••••')).toBeInTheDocument();
  });

  it('renders corroborated aliases when present', async () => {
    const tariqNode = MOCK_GRAPH_NODES[0];
    render(<EntityDrawer nodeData={tariqNode.data} />);

    const aliasesSection = screen.getByTestId('entity-aliases');
    expect(aliasesSection).toBeInTheDocument();
    expect(screen.getByText(/"Bhaijaan"/i)).toBeInTheDocument();
  });

  it('renders SNA metrics and priority ranking with non-accusatory terminology', () => {
    const tariqNode = MOCK_GRAPH_NODES[0];
    render(<EntityDrawer nodeData={tariqNode.data} />);

    expect(screen.getByText(/Social Network Analysis \(SNA\) & Priority/i)).toBeInTheDocument();

    const priorityMetric = screen.getByTestId('priority-metric');
    expect(priorityMetric).toHaveTextContent('89');

    expect(screen.getByTestId('sna-degree')).toBeInTheDocument();
    expect(screen.getByTestId('sna-betweenness')).toBeInTheDocument();
    expect(screen.getByTestId('sna-pagerank')).toBeInTheDocument();

    // Verify non-accusatory invariant: do not call metrics a "guilt score", "crime probability", or "kingpin probability"
    const drawerText = screen.getByTestId('entity-drawer').textContent ?? '';
    expect(drawerText).not.toContain('guilt score');
    expect(drawerText).not.toContain('kingpin');
    expect(drawerText).not.toContain('crime probability');
    expect(drawerText).toContain('Does not indicate criminality or guilt');
  });

  it('renders associated cases context correctly', () => {
    const tariqNode = MOCK_GRAPH_NODES[0];
    render(<EntityDrawer nodeData={tariqNode.data} />);

    const casesSection = screen.getByTestId('associated-cases');
    expect(casesSection).toBeInTheDocument();
    expect(screen.getByText(MOCK_CASE_CODE)).toBeInTheDocument();
    expect(screen.getByText(MOCK_CASE_DETAIL.title)).toBeInTheDocument();
  });

  it('triggers action callbacks: View Source Evidence & Flag for Entity Resolution', () => {
    const tariqNode = MOCK_GRAPH_NODES[0];
    const handleViewEvidence = vi.fn();
    const handleFlagReview = vi.fn();

    render(
      <EntityDrawer
        nodeData={tariqNode.data}
        onViewEvidence={handleViewEvidence}
        onFlagReview={handleFlagReview}
      />
    );

    const evidenceBtn = screen.getByTestId('view-source-evidence-btn');
    fireEvent.click(evidenceBtn);
    expect(handleViewEvidence).toHaveBeenCalledWith({ type: 'entity', id: tariqNode.data.id });
    expect(screen.getByTestId('action-feedback-banner')).toHaveTextContent(/Source evidence context prepared/i);

    const flagBtn = screen.getByTestId('flag-entity-resolution-btn');
    fireEvent.click(flagBtn);
    expect(handleFlagReview).toHaveBeenCalledWith({ type: 'entity', id: tariqNode.data.id });
    expect(screen.getByTestId('action-feedback-banner')).toHaveTextContent(/queued for resolution review/i);
  });

  it('inspects observed factual edge: displays solid indicator, source citations, and confidence', () => {
    const solidEdge = MOCK_GRAPH_EDGES[2]; // COMMUNICATED_WITH (solid)
    render(<EntityDrawer edgeData={solidEdge.data} />);

    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();
    expect(screen.getByTestId('relationship-type-badge')).toHaveTextContent(`Type: ${RelationshipTypes.COMMUNICATED_WITH}`);
    expect(screen.getByTestId('observed-relationship-indicator')).toHaveTextContent('[OBSERVED FACT]');
    expect(screen.getByText(/Verified Source-Backed Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/92%/i)).toBeInTheDocument();
    expect(screen.getByText(/4 source record\(s\)/i)).toBeInTheDocument();
  });

  it('inspects AI-inferred edge: displays dashed indicator, GATv2 model info, and non-accusatory disclaimer', () => {
    const predictedEdge = MOCK_GRAPH_EDGES[9]; // GATv2 predicted KNOWS edge (dashed)
    render(<EntityDrawer edgeData={predictedEdge.data} />);

    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();
    expect(screen.getByTestId('inferred-relationship-indicator')).toHaveTextContent('[AI INFERRED / PREDICTION]');
    expect(screen.getByText(/GATv2 Graph Link Prediction/i)).toBeInTheDocument();
    expect(screen.getByText('GATv2-Supervised-LinkPredictor')).toBeInTheDocument();
    expect(screen.getByText('ISOTONIC_CALIBRATED')).toBeInTheDocument();
    expect(screen.getByText(/84%/i)).toBeInTheDocument();
    expect(screen.getByText(/Machine learning predictions are investigative leads only/i)).toBeInTheDocument();
  });

  it('triggers explicit close button callback', () => {
    const handleClose = vi.fn();
    const node = MOCK_GRAPH_NODES[0];
    render(<EntityDrawer nodeData={node.data} onClose={handleClose} />);

    const closeBtn = screen.getByTestId('close-drawer-btn');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('integrates seamlessly with SelectionProvider and CaseProvider without resetting context', async () => {
    render(
      <CaseProvider>
        <SelectionProvider>
          <EntityDrawer
            nodeData={{
              id: 'ent-person-001',
              label: 'Rajesh Sharma',
              entity_type: EntityTypes.PERSON,
              case_id: '3fa85f64-5717-4562-b3fc-2c963f66afa6',
              status: 'ACTIVE',
              risk_score: 0.89,
            }}
          />
        </SelectionProvider>
      </CaseProvider>
    );

    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();
    expect(screen.getByText('Rajesh Sharma')).toBeInTheDocument();
    expect(await screen.findByText(/Corroborated Aliases/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Raju Seth/i).length).toBeGreaterThan(0);
  });
});
