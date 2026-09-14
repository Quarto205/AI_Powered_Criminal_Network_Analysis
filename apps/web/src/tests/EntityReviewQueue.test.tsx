/**
 * Comprehensive Unit & Integration Tests for EntityReviewQueue Component
 * Strictly conforms to 01_SHARED_TYPES.md, 04_API_SPEC.md, 05_AI_CONTRACTS.md, and 08_UI_DATA_CONTRACT.md.
 *
 * Dev B — Step 3: Entity Resolution Triage Queue
 * Covers all 17 test requirements from Step 3:
 * 1. Empty queue state
 * 2. Pending candidate renders correctly
 * 3. Canonical entity information renders
 * 4. Candidate/source information renders
 * 5. Similarity score is displayed separately from extraction confidence
 * 6. Similarity threshold configuration works
 * 7. Confirm button creates correct review payload
 * 8. Reject button creates correct review payload
 * 9. target_type is exactly ENTITY_RESOLUTION
 * 10. Override notes are passed when supplied
 * 11. Successful review transitions/removes item from pending queue
 * 12. NEW -> REVIEWED state is represented correctly
 * 13. Reject results in REJECTED state
 * 14. Masked identifiers remain masked
 * 15. Raw source text is not modified
 * 16. No accusatory/guilt/kingpin terminology
 * 17. Graph/selection context is preserved
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EntityReviewQueue } from '../components/triage/EntityReviewQueue';
import { EntityDrawer } from '../components/drawers/EntityDrawer';
import { SelectionProvider, useSelection } from '../context/SelectionContext';
import { CaseProvider } from '../context/CaseContext';
import { MOCK_ENTITY_REVIEW_ITEMS } from '../mocks/evidenceMock';
import { MOCK_GRAPH } from '../mocks/graphMock';
import { ReviewActions, ReviewTargetTypes } from '../types/contracts';
import { apiClient } from '../api';

describe('EntityReviewQueue Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Empty queue state
  it('1. renders a clear non-alarming empty state when there are zero pending reviews', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue items={[]} />
      </CaseProvider>
    );

    expect(screen.getByTestId('pending-count-badge')).toHaveTextContent('0 Pending');
    expect(screen.getByTestId('empty-queue-message')).toHaveTextContent('No pending entity-resolution reviews.');
    expect(screen.getByTestId('empty-queue-container')).toHaveTextContent('No pending entity-resolution reviews.');
  });

  // 2. Pending candidate renders correctly
  it('2. renders pending candidate items and header with pending count', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    expect(screen.getByTestId('review-queue-header')).toHaveTextContent('Entity Resolution Review');
    expect(screen.getByTestId('pending-count-badge')).toHaveTextContent('2 Pending');
    expect(screen.getByTestId('pending-review-list')).toBeInTheDocument();
    expect(screen.getByTestId('review-item-rev-001-vikram-s')).toBeInTheDocument();
    expect(screen.getByTestId('review-item-rev-003-rk-gupta')).toBeInTheDocument();
  });

  // 3. Canonical entity information renders
  it('3. renders canonical target entity information', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    const canonicalPanel = screen.getByTestId('canonical-entity-panel');
    expect(canonicalPanel).toBeInTheDocument();
    expect(screen.getByTestId('canonical-name')).toHaveTextContent('Vikram Sharma');
    expect(screen.getByTestId('canonical-type')).toHaveTextContent('PERSON');
    expect(screen.getByTestId('canonical-aliases')).toHaveTextContent('"Vicky Delhi"');
    expect(screen.getByTestId('canonical-case-id')).toHaveTextContent('e7b1a2c4-893f-4e12-b567-91a0c4581234');
  });

  // 4. Candidate / source information renders
  it('4. renders candidate mention and source document information', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    const candidatePanel = screen.getByTestId('candidate-mention-panel');
    expect(candidatePanel).toBeInTheDocument();
    expect(screen.getByTestId('candidate-extracted-text')).toHaveTextContent('"Vikram S."');
    expect(screen.getByTestId('candidate-type')).toHaveTextContent('PERSON');
    expect(screen.getByTestId('candidate-source-doc')).toHaveTextContent('FIR_42_2026_Special_Cell.pdf');
    expect(screen.getByTestId('candidate-doc-id')).toHaveTextContent('doc-001-fir-42-2024');
    expect(screen.getByTestId('candidate-offsets')).toHaveTextContent('[1042-1051]');
    expect(screen.getByTestId('candidate-source-snippet')).toHaveTextContent(/Vikram S. was accompanied by two associates/i);
    expect(screen.getByTestId('candidate-match-algorithm')).toHaveTextContent('JARO_WINKLER');
  });

  // 5. Similarity score is displayed separately from extraction confidence
  it('5. displays similarity score separately from extraction confidence', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    // Similarity score (0.78 / 78%)
    const similarityBadge = screen.getByTestId('candidate-similarity-score');
    expect(similarityBadge).toHaveTextContent('78%');

    // Extraction confidence (0.91 / 91%)
    const extractionConfidenceBadge = screen.getByTestId('candidate-extraction-confidence');
    expect(extractionConfidenceBadge).toHaveTextContent('91%');

    // Ensure they have distinct labels and values
    expect(screen.getByText(/Similarity Score/i)).toBeInTheDocument();
    expect(screen.getByText(/Extraction Confidence/i)).toBeInTheDocument();
  });

  // 6. Similarity threshold configuration works
  it('6. respects configurable similarity threshold props', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue thresholds={{ autoMerge: 0.90, reviewMin: 0.70 }} />
      </CaseProvider>
    );

    const thresholdsDisplay = screen.getByTestId('thresholds-display');
    expect(thresholdsDisplay).toHaveTextContent('Review Band: 0.70 – 0.90');
  });

  // 7, 9, 10, 11, 12. Confirm button creates correct review payload and transitions state
  it('7, 9, 10, 11, 12. handles Confirm Merge: passes target_type ENTITY_RESOLUTION, action CONFIRM, override notes, and updates state', async () => {
    const handleReview = vi.fn();
    const submitReviewSpy = vi.spyOn(apiClient, 'submitReview');

    render(
      <CaseProvider>
        <EntityReviewQueue onReview={handleReview} />
      </CaseProvider>
    );

    // Enter reviewer override notes
    const notesInput = screen.getByTestId('override-notes-input');
    fireEvent.change(notesInput, {
      target: { value: 'Corroborated by co-defendant call detail records.' },
    });

    // Click Confirm Merge
    const confirmBtn = screen.getByTestId('confirm-merge-btn');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(submitReviewSpy).toHaveBeenCalledTimes(1);
      expect(handleReview).toHaveBeenCalledTimes(1);
    });

    // 7 & 9 & 10. Verify exact API payload
    expect(submitReviewSpy).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        target_id: 'rev-001-vikram-s',
        target_type: ReviewTargetTypes.ENTITY_RESOLUTION,
        action: ReviewActions.CONFIRM,
        reason: 'Corroborated by co-defendant call detail records.',
        override_notes: 'Corroborated by co-defendant call detail records.',
      })
    );

    // 11. Item removed from pending queue
    expect(screen.getByTestId('pending-count-badge')).toHaveTextContent('1 Pending');

    // 12. Item represented as reviewed in ALL filter
    fireEvent.click(screen.getByTestId('filter-all-btn'));
    fireEvent.click(screen.getByTestId('review-item-rev-001-vikram-s'));

    // Verify canonical aliases view now reflects the merged mention
    const aliasesContainer = screen.getByTestId('canonical-aliases');
    expect(aliasesContainer).toHaveTextContent('"Vikram S."');
  });

  // 8, 9, 10, 13. Reject button creates correct review payload and transitions to REJECTED
  it('8, 9, 10, 13. handles Reject Match: passes target_type ENTITY_RESOLUTION, action REJECT, override notes, and preserves entities separate', async () => {
    const handleReview = vi.fn();
    const submitReviewSpy = vi.spyOn(apiClient, 'submitReview');

    render(
      <CaseProvider>
        <EntityReviewQueue onReview={handleReview} />
      </CaseProvider>
    );

    const notesInput = screen.getByTestId('override-notes-input');
    fireEvent.change(notesInput, {
      target: { value: 'Different age and residence profile from primary suspect.' },
    });

    const rejectBtn = screen.getByTestId('reject-match-btn');
    fireEvent.click(rejectBtn);

    await waitFor(() => {
      expect(submitReviewSpy).toHaveBeenCalledTimes(1);
      expect(handleReview).toHaveBeenCalledTimes(1);
    });

    // 8 & 9. Verify exact API payload with REJECT action
    expect(submitReviewSpy).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        target_id: 'rev-001-vikram-s',
        target_type: ReviewTargetTypes.ENTITY_RESOLUTION,
        action: ReviewActions.REJECT,
        reason: 'Different age and residence profile from primary suspect.',
        override_notes: 'Different age and residence profile from primary suspect.',
      })
    );

    // 13. Item removed from pending queue and not merged as alias
    expect(screen.getByTestId('pending-count-badge')).toHaveTextContent('1 Pending');

    fireEvent.click(screen.getByTestId('filter-all-btn'));
    fireEvent.click(screen.getByTestId('review-item-rev-001-vikram-s'));

    const aliasesContainer = screen.getByTestId('canonical-aliases');
    expect(aliasesContainer).not.toHaveTextContent('"Vikram S."');
  });

  // 14. Masked identifiers remain masked
  it('14. preserves masking on sensitive canonical identifiers', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    const identifiers = screen.getByTestId('canonical-identifiers');
    expect(identifiers).toHaveTextContent('+91 98731 •••••');
    // Ensure raw 10-digit number is never exposed in the DOM
    expect(identifiers.textContent).not.toContain('9873102941');
  });

  // 15. Raw source text is not modified
  it('15. guarantees source fixture and original snippet immutability', async () => {
    const originalStatus = MOCK_ENTITY_REVIEW_ITEMS[0].review_status;
    const originalSnippet = MOCK_ENTITY_REVIEW_ITEMS[0].provenance.snippet;
    const originalAliasesLength = MOCK_ENTITY_REVIEW_ITEMS[0].candidate_entity.existing_aliases.length;

    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    const confirmBtn = screen.getByTestId('confirm-merge-btn');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByTestId('pending-count-badge')).toHaveTextContent('1 Pending');
    });

    // Source fixture in memory must remain completely unmutated
    expect(MOCK_ENTITY_REVIEW_ITEMS[0].review_status).toBe(originalStatus);
    expect(MOCK_ENTITY_REVIEW_ITEMS[0].provenance.snippet).toBe(originalSnippet);
    expect(MOCK_ENTITY_REVIEW_ITEMS[0].candidate_entity.existing_aliases.length).toBe(originalAliasesLength);
  });

  // 16. No accusatory / guilt / kingpin terminology
  it('16. adheres to non-accusatory terminology: never labels similarity as guilt or crime probability', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    const queueText = screen.getByTestId('entity-review-queue').textContent?.toLowerCase() || '';

    expect(queueText).not.toContain('guilt probability');
    expect(queueText).not.toContain('crime probability');
    expect(queueText).not.toContain('kingpin probability');
    expect(queueText).not.toContain('guilt score');
    expect(queueText).toContain('does not indicate criminality or legal guilt');
  });

  // 17. Graph / selection context is preserved
  it('17. preserves graph/selection context when queue is opened alongside graph canvas', async () => {
    const ShellSimulation = () => {
      const { selectedNode, activeDrawer, closeDrawer } = useSelection();
      return (
        <div>
          {activeDrawer === 'ENTITY' && selectedNode && <EntityDrawer nodeData={selectedNode} />}
          {activeDrawer === 'REVIEW_QUEUE' && <EntityReviewQueue onClose={closeDrawer} />}
        </div>
      );
    };

    const Harness = () => {
      const { selectNode, selectedNode } = useSelection();
      return (
        <div>
          <button data-testid="select-node-btn" onClick={() => selectNode(MOCK_GRAPH.nodes[0].data)}>
            Select Tariq
          </button>
          <span data-testid="current-selection-id">{selectedNode?.id ?? 'none'}</span>
          <ShellSimulation />
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

    // 1. Select node
    fireEvent.click(screen.getByTestId('select-node-btn'));
    expect(screen.getByTestId('current-selection-id')).toHaveTextContent('node-person-1');
    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();

    // 2. Open review queue
    const flagBtn = screen.getByTestId('flag-entity-resolution-btn');
    fireEvent.click(flagBtn);

    await waitFor(() => {
      expect(screen.getByTestId('entity-review-queue')).toBeInTheDocument();
    });

    // 3. Verify node selection context remained intact
    expect(screen.getByTestId('current-selection-id')).toHaveTextContent('node-person-1');

    // 4. Close queue -> selection still intact
    const closeQueueBtn = screen.getByTestId('close-queue-btn');
    fireEvent.click(closeQueueBtn);

    await waitFor(() => {
      expect(screen.queryByTestId('entity-review-queue')).not.toBeInTheDocument();
    });
    expect(screen.getByTestId('current-selection-id')).toHaveTextContent('node-person-1');
  });

  // Filtering controls test
  it('filters queue items by entity type and similarity level', () => {
    render(
      <CaseProvider>
        <EntityReviewQueue />
      </CaseProvider>
    );

    const typeFilter = screen.getByTestId('filter-entity-type');
    fireEvent.change(typeFilter, { target: { value: 'PHONE' } });

    // Both pending items in mock are PERSON, so PHONE yields 0 matching items
    expect(screen.getByTestId('empty-queue-message')).toHaveTextContent('No pending entity-resolution reviews.');

    // Reset to ALL
    fireEvent.change(typeFilter, { target: { value: 'ALL' } });
    expect(screen.getByTestId('review-item-rev-001-vikram-s')).toBeInTheDocument();
  });
});
