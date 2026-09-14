/**
 * Focused Unit & Integration Tests for EvidencePanel Component
 * Dev B — Step 2B
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EvidencePanel, HighlightedExcerpt } from '../components/drawers/EvidencePanel';
import { EntityDrawer } from '../components/drawers/EntityDrawer';
import { SelectionProvider, useSelection } from '../context/SelectionContext';
import { CaseProvider } from '../context/CaseContext';
import { MOCK_GRAPH } from '../mocks/graphMock';
import { MOCK_PROVENANCE_FIR } from '../mocks/evidenceMock';

describe('EvidencePanel Component Tests', () => {
  // 1. Empty state
  it('renders empty state when no evidence or target is selected', () => {
    const handleClose = vi.fn();
    render(<EvidencePanel edgeData={null} nodeData={null} target={null} onClose={handleClose} />);

    expect(screen.getByTestId('evidence-panel-empty')).toBeInTheDocument();
    expect(screen.getByText('No Evidence Selected')).toBeInTheDocument();

    const closeBtn = screen.getByTestId('close-evidence-btn');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  // 2. Evidence / source metadata
  it('renders evidence and source relationship metadata', () => {
    const factualEdge = MOCK_GRAPH.edges[2]; // edge-3: COMMUNICATED_WITH
    render(<EvidencePanel edgeData={factualEdge.data} />);

    expect(screen.getByTestId('evidence-panel')).toBeInTheDocument();
    expect(screen.getByText('Observed Relationship')).toBeInTheDocument();
    expect(screen.getByTestId('relationship-type-badge')).toHaveTextContent('COMMUNICATED_WITH');
    expect(screen.getByTestId('observed-relationship-indicator')).toHaveTextContent('[OBSERVED FACT]');
  });

  // 3. Document information
  it('renders document information and verification status', async () => {
    const factualEdge = MOCK_GRAPH.edges[2];
    render(<EvidencePanel edgeData={factualEdge.data} />);

    // Provenance section exists
    expect(screen.getByTestId('provenance-section')).toBeInTheDocument();

    // Check document file name and card
    const card = await screen.findByTestId('provenance-card');
    expect(card).toBeInTheDocument();
    expect(screen.getByTestId('provenance-filename')).toHaveTextContent(/CDR_Dump_Feb2026_Intercepts.csv/i);
    expect(screen.getByText(/Doc ID:/i)).toBeInTheDocument();
    expect(screen.getByText(/doc-002-cdr-dump-feb/i)).toBeInTheDocument();
  });

  // 4. Provenance information
  it('renders provenance information including offsets and version hash', async () => {
    render(<EvidencePanel provenanceSpan={MOCK_PROVENANCE_FIR} />);

    expect(screen.getByTestId('provenance-filename')).toHaveTextContent('FIR_42_2026_Special_Cell.pdf');
    expect(screen.getByText(/Page:/i)).toBeInTheDocument();
    expect(screen.getByTestId('provenance-span-range')).toHaveTextContent('[340-495]');
    expect(screen.getByTestId('provenance-version-hash')).toHaveTextContent(/sha256-a1b2c3d4/i);
    expect(screen.getByText('SUPPORTS')).toBeInTheDocument();
  });

  // 5. Character span highlighting
  it('highlights the correct character span using HighlightedExcerpt', () => {
    const sampleText = 'Intercepted communications indicated Tariq Khan coordinating transit vehicles';
    // "Tariq Khan" is at index 37 to 47
    render(<HighlightedExcerpt text={sampleText} start={37} end={47} />);

    expect(screen.getByTestId('highlighted-container')).toBeInTheDocument();
    expect(screen.getByTestId('span-highlight')).toHaveTextContent('Tariq Khan');
    expect(screen.getByTestId('span-before').textContent).toBe('Intercepted communications indicated ');
    expect(screen.getByTestId('span-after').textContent).toBe(' coordinating transit vehicles');
  });

  // 6. Safely renders source text (XSS and HTML injection safe)
  it('safely renders untrusted source text without executing HTML or scripts', () => {
    const untrustedText = '<script>alert("xss")</script><img src=x onerror=alert(1) /> Suspect Vikram';
    render(<HighlightedExcerpt text={untrustedText} start={0} end={8} />);

    const highlight = screen.getByTestId('span-highlight');
    expect(highlight).toHaveTextContent('<script>');
    // Verify script tags are rendered strictly as text nodes in the DOM
    expect(document.querySelector('script[src]')).toBeNull();
    expect(screen.getByText(/onerror=alert/i)).toBeInTheDocument();
  });

  // 7. Handles invalid character offsets gracefully
  it('handles invalid or out-of-bounds character offsets gracefully without crashing', () => {
    const text = 'Normal excerpt without proper offset metadata';

    // Negative start
    const { unmount: unmount1 } = render(<HighlightedExcerpt text={text} start={-5} end={10} />);
    expect(screen.getByTestId('unhighlighted-excerpt')).toHaveTextContent(text);
    unmount1();

    // Start >= End
    const { unmount: unmount2 } = render(<HighlightedExcerpt text={text} start={20} end={10} />);
    expect(screen.getByTestId('unhighlighted-excerpt')).toHaveTextContent(text);
    unmount2();

    // Start exceeding string length
    const { unmount: unmount3 } = render(<HighlightedExcerpt text={text} start={100} end={150} />);
    expect(screen.getByTestId('unhighlighted-excerpt')).toHaveTextContent(text);
    unmount3();

    // Missing / null offsets
    const { unmount: unmount4 } = render(<HighlightedExcerpt text={text} start={null} end={null} />);
    expect(screen.getByTestId('unhighlighted-excerpt')).toHaveTextContent(text);
    unmount4();
  });

  // 8. Displays the correct confidence metric
  it('displays the correct confidence metric without relabeling or collapsing', () => {
    // Factual edge with relationship_confidence
    const factualEdge = MOCK_GRAPH.edges[2];
    const { unmount } = render(<EvidencePanel edgeData={factualEdge.data} />);

    expect(screen.getByTestId('confidence-semantics-card')).toBeInTheDocument();
    expect(screen.getByTestId('metric-relationship-confidence')).toHaveTextContent('92%');
    expect(screen.queryByTestId('metric-model-confidence')).not.toBeInTheDocument();
    unmount();

    // Inferred edge with model_confidence
    const predictedEdge = MOCK_GRAPH.edges[9];
    render(<EvidencePanel edgeData={predictedEdge.data} />);

    expect(screen.getByTestId('metric-model-confidence')).toHaveTextContent('84%');
  });

  // 9. Displays Subjective Logic fields when present
  it('displays Subjective Logic opinion tuple fields when present (b + d + u = 1.0)', () => {
    // MOCK_RELATIONSHIP_DETAIL_FACTUAL has belief: 0.85, disbelief: 0.05, uncertainty: 0.10
    render(<EvidencePanel edgeData={MOCK_GRAPH.edges[2].data} />);

    const slSection = screen.getByTestId('subjective-logic-section');
    expect(slSection).toBeInTheDocument();
    expect(screen.getByTestId('sl-belief')).toHaveTextContent('0.85');
    expect(screen.getByTestId('sl-disbelief')).toHaveTextContent('0.05');
    expect(screen.getByTestId('sl-uncertainty')).toHaveTextContent('0.10');

    // Mathematical consistency check
    const b = parseFloat(screen.getByTestId('sl-belief').textContent || '0');
    const d = parseFloat(screen.getByTestId('sl-disbelief').textContent || '0');
    const u = parseFloat(screen.getByTestId('sl-uncertainty').textContent || '0');
    expect(parseFloat((b + d + u).toFixed(2))).toBe(1.0);

    // Non-accusatory label check
    expect(slSection.textContent).toContain('Not an assertion of legal culpability');
  });

  // 10. Distinguishes observed evidence from inferred prediction
  it('distinguishes observed evidence from inferred prediction with explicit badges', () => {
    // Factual Edge
    const factualEdge = MOCK_GRAPH.edges[2];
    const { unmount } = render(<EvidencePanel edgeData={factualEdge.data} />);
    expect(screen.getByTestId('observed-relationship-indicator')).toHaveTextContent('[OBSERVED FACT]');
    expect(screen.queryByTestId('inferred-relationship-indicator')).not.toBeInTheDocument();
    unmount();

    // Predicted Edge
    const predictedEdge = MOCK_GRAPH.edges[9];
    render(<EvidencePanel edgeData={predictedEdge.data} />);
    expect(screen.getByTestId('inferred-relationship-indicator')).toHaveTextContent('[AI INFERRED]');
    expect(screen.queryByTestId('observed-relationship-indicator')).not.toBeInTheDocument();
  });

  // 11. Displays GATv2 prediction disclaimer when applicable
  it('displays GATv2 prediction disclaimer and adheres to non-accusatory invariant', () => {
    const predictedEdge = MOCK_GRAPH.edges[9];
    render(<EvidencePanel edgeData={predictedEdge.data} />);

    const aiCard = screen.getByTestId('ai-prediction-card');
    expect(aiCard).toBeInTheDocument();
    expect(screen.getByText(/GATv2 Graph Neural Network Prediction/i)).toBeInTheDocument();
    expect(screen.getByTestId('ai-disclaimer')).toHaveTextContent(/Investigative Lead Only/i);

    // Verify non-accusatory invariant: never label as guilt or crime probability
    const panelText = screen.getByTestId('evidence-panel').textContent?.toLowerCase() || '';
    expect(panelText).not.toContain('guilt probability');
    expect(panelText).not.toContain('crime probability');
    expect(panelText).not.toContain('kingpin probability');
  });

  // 12. Close button works
  it('triggers explicit close callback when close button is clicked', () => {
    const handleClose = vi.fn();
    render(<EvidencePanel edgeData={MOCK_GRAPH.edges[2].data} onClose={handleClose} />);

    const closeBtn = screen.getByTestId('close-evidence-btn');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  // 13. View Source Evidence from EntityDrawer opens/provides the correct evidence context
  it('connects View Source Evidence from EntityDrawer to EvidencePanel via SelectionContext', async () => {
    const IntegratedTestContainer = () => {
      const { selectedNode, activeDrawer } = useSelection();
      return (
        <div>
          {activeDrawer === 'ENTITY' && selectedNode && <EntityDrawer nodeData={selectedNode} />}
          {activeDrawer === 'EVIDENCE' && selectedNode && <EvidencePanel nodeData={selectedNode} />}
        </div>
      );
    };

    const tariqNode = MOCK_GRAPH.nodes[0]; // Tariq Khan

    const Harness = () => {
      const { selectNode } = useSelection();
      return (
        <div>
          <button data-testid="select-node-btn" onClick={() => selectNode(tariqNode.data)}>
            Select Tariq
          </button>
          <IntegratedTestContainer />
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

    // Initially select Tariq -> EntityDrawer opens
    fireEvent.click(screen.getByTestId('select-node-btn'));
    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();
    expect(screen.getByText('Tariq Khan')).toBeInTheDocument();

    // Click "View Source Evidence" on EntityDrawer
    const viewEvidenceBtn = screen.getByTestId('view-source-evidence-btn');
    fireEvent.click(viewEvidenceBtn);

    // Expect EvidencePanel to open with Tariq Khan's evidence
    await waitFor(() => {
      expect(screen.getByTestId('evidence-panel')).toBeInTheDocument();
    });

    expect(screen.getByText('Observed Entity Evidence')).toBeInTheDocument();
    expect(screen.getAllByText('Tariq Khan').length).toBeGreaterThan(0);
    expect(screen.getByTestId('provenance-section')).toBeInTheDocument();
  });

  // 14. Drawer does not interfere with graph selection/context
  it('operates inside SelectionProvider without resetting graph selection state', () => {
    const StateObserver = () => {
      const { selectedEdge, activeDrawer, closeDrawer } = useSelection();
      return (
        <div>
          <span data-testid="active-drawer-state">{activeDrawer ?? 'NONE'}</span>
          <span data-testid="selected-edge-state">{selectedEdge?.id ?? 'NONE'}</span>
          <button data-testid="trigger-close-btn" onClick={closeDrawer}>
            Close
          </button>
        </div>
      );
    };

    const Harness = () => {
      const { selectEdge } = useSelection();
      return (
        <div>
          <button data-testid="select-edge-btn" onClick={() => selectEdge(MOCK_GRAPH.edges[2].data)}>
            Select Edge
          </button>
          <StateObserver />
        </div>
      );
    };

    render(
      <SelectionProvider>
        <Harness />
      </SelectionProvider>
    );

    expect(screen.getByTestId('active-drawer-state')).toHaveTextContent('NONE');

    // Select edge -> opens EVIDENCE drawer
    fireEvent.click(screen.getByTestId('select-edge-btn'));
    expect(screen.getByTestId('active-drawer-state')).toHaveTextContent('EVIDENCE');
    expect(screen.getByTestId('selected-edge-state')).toHaveTextContent('edge-3');

    // Close drawer -> resets activeDrawer to null, does NOT wipe edge or throw
    fireEvent.click(screen.getByTestId('trigger-close-btn'));
    expect(screen.getByTestId('active-drawer-state')).toHaveTextContent('NONE');
  });
});
