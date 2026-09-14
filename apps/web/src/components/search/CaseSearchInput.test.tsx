import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CaseSearchInput } from './CaseSearchInput';
import { CASE_1_ID, CASE_2_ID } from '../../mocks/searchMock';

describe('CaseSearchInput Component (Step 4)', () => {
  it('renders search input with placeholder and accessible attributes', () => {
    render(
      <CaseSearchInput
        activeCaseId={CASE_1_ID}
        onSelectEntity={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('type', 'search');
  });

  it('filters entities strictly within active case by canonical name', () => {
    render(
      <CaseSearchInput
        activeCaseId={CASE_1_ID}
        onSelectEntity={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    fireEvent.change(input, { target: { value: 'Person' } });

    // Matching entities in Case 1 appear
    expect(screen.getByText('Person A')).toBeInTheDocument();
    expect(screen.getByText('Person B')).toBeInTheDocument();

    // Critical scope security invariant: Person C belongs to Case 2, so it MUST NOT appear!
    expect(screen.queryByText('Person C')).not.toBeInTheDocument();
  });

  it('matches entities by masked identifier in active case', () => {
    render(
      <CaseSearchInput
        activeCaseId={CASE_1_ID}
        onSelectEntity={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    fireEvent.change(input, { target: { value: '+91-XXXXX-5678' } });

    expect(screen.getByText('Phone ••••5678')).toBeInTheDocument();
    expect(screen.getByText('+91-XXXXX-5678')).toBeInTheDocument();
  });

  it('respects maximum limit of 10 visible results', () => {
    render(
      <CaseSearchInput
        activeCaseId={CASE_1_ID}
        onSelectEntity={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    // Search a broad query matching all 11 entities in Case 1
    fireEvent.change(input, { target: { value: 'e' } });

    const resultOptions = screen.getAllByRole('option');
    expect(resultOptions.length).toBeLessThanOrEqual(10);
  });

  it('calls onSelectEntity when an entity option is clicked and closes dropdown', () => {
    const onSelectEntity = vi.fn();

    render(
      <CaseSearchInput
        activeCaseId={CASE_1_ID}
        onSelectEntity={onSelectEntity}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    fireEvent.change(input, { target: { value: 'Person A' } });

    const option = screen.getByRole('option', { name: /Person A/i });
    fireEvent.click(option);

    expect(onSelectEntity).toHaveBeenCalledTimes(1);
    expect(onSelectEntity).toHaveBeenCalledWith(
      expect.objectContaining({ canonical_name: 'Person A' })
    );

    // Dropdown closes after selection
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('renders empty message when no entity matches inside active case', () => {
    render(
      <CaseSearchInput
        activeCaseId={CASE_1_ID}
        onSelectEntity={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    fireEvent.change(input, { target: { value: 'non-matching-entity-xyz' } });

    expect(
      screen.getByText('No matching entities found in current case.')
    ).toBeInTheDocument();
  });

  it('enforces isolation between Case 1 and Case 2 entities', () => {
    // Render with Case 2 ID
    render(
      <CaseSearchInput
        activeCaseId={CASE_2_ID}
        onSelectEntity={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    fireEvent.change(input, { target: { value: 'Person' } });

    // In Case 2, Person C is present
    expect(screen.getByText('Person C')).toBeInTheDocument();

    // Person A and Person B belong to Case 1 and must NOT leak into Case 2
    expect(screen.queryByText('Person A')).not.toBeInTheDocument();
    expect(screen.queryByText('Person B')).not.toBeInTheDocument();
  });

  it('clears query and closes dropdown when clear button is clicked', () => {
    render(
      <CaseSearchInput
        activeCaseId={CASE_1_ID}
        onSelectEntity={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Search entities in active case…');
    fireEvent.change(input, { target: { value: 'Person' } });
    expect(screen.getByRole('listbox')).toBeInTheDocument();

    const clearBtn = screen.getByRole('button', { name: /Clear case search query/i });
    fireEvent.click(clearBtn);

    expect(input).toHaveValue('');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
});
