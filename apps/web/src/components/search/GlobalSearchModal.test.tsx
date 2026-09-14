import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GlobalSearchModal } from './GlobalSearchModal';

describe('GlobalSearchModal Component (Step 4)', () => {
  it('does not render when isOpen is false', () => {
    const { container } = render(
      <GlobalSearchModal
        isOpen={false}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders modal dialog when isOpen is true with accessible attributes', () => {
    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    const dialog = screen.getByRole('dialog', { name: 'Global Search Modal' });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute('aria-modal', 'true');

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('displays initial guidance state when query is empty', () => {
    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    expect(screen.getByText('Global Investigative Search')).toBeInTheDocument();
    expect(screen.getByText(/Search across authorized cases and canonical entities/i)).toBeInTheDocument();
  });

  it('searches authorized cases by case_code or title', () => {
    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    fireEvent.change(searchInput, { target: { value: 'DL-2026' } });

    // Section 1: Authorized Cases appears with matching case
    expect(screen.getByText(/^Authorized Cases/i)).toBeInTheDocument();
    expect(screen.getByText('DL-2026-CR-0192')).toBeInTheDocument();
    expect(screen.getByText('Syndicate Hawala & Mule Network Investigation')).toBeInTheDocument();
    expect(screen.getByText('Delhi NCR — Special Cell')).toBeInTheDocument();
  });

  it('searches authorized entities by canonical name and masked identifier', () => {
    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    // Search masked phone number
    fireEvent.change(searchInput, { target: { value: '+91-XXXXX-5678' } });

    expect(screen.getByText(/^Matched Entities/i)).toBeInTheDocument();
    expect(screen.getByText('Phone ••••5678')).toBeInTheDocument();
    expect(screen.getByText('+91-XXXXX-5678')).toBeInTheDocument();
  });

  it('searches masked bank accounts safely', () => {
    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    fireEvent.change(searchInput, { target: { value: 'SBIN000XXXX4921' } });

    expect(screen.getByText('Account ••••4921')).toBeInTheDocument();
    expect(screen.getByText('SBIN000XXXX4921')).toBeInTheDocument();
  });

  it('shows generic no-results message without leaking case existence when no match found', () => {
    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    fireEvent.change(searchInput, { target: { value: 'unknown-forbidden-query-xyz' } });

    expect(
      screen.getByText('No matching authorized cases or entities found.')
    ).toBeInTheDocument();
    // Stealth isolation invariant: no unauthorized hints
    expect(screen.queryByText(/unauthorized/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/forbidden/i)).not.toBeInTheDocument();
  });

  it('calls onSelectCase and onClose when a case result card is clicked', () => {
    const onSelectCase = vi.fn();
    const onClose = vi.fn();

    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={onClose}
        onSelectCase={onSelectCase}
        onSelectEntity={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    fireEvent.change(searchInput, { target: { value: 'MH-2026' } });

    const caseBtn = screen.getByRole('button', { name: /^Case: MH-2026-EC-0084/i });
    fireEvent.click(caseBtn);

    expect(onSelectCase).toHaveBeenCalledTimes(1);
    expect(onSelectCase).toHaveBeenCalledWith(
      expect.objectContaining({ case_code: 'MH-2026-EC-0084' })
    );
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onSelectEntity and onClose when an entity result card is clicked', () => {
    const onSelectEntity = vi.fn();
    const onClose = vi.fn();

    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={onClose}
        onSelectCase={vi.fn()}
        onSelectEntity={onSelectEntity}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    fireEvent.change(searchInput, { target: { value: 'Person A' } });

    const entityBtn = screen.getByRole('button', { name: /Entity: Person A/i });
    fireEvent.click(entityBtn);

    expect(onSelectEntity).toHaveBeenCalledTimes(1);
    expect(onSelectEntity).toHaveBeenCalledWith(
      expect.objectContaining({ canonical_name: 'Person A' })
    );
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes modal when Escape key is pressed', () => {
    const onClose = vi.fn();

    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={onClose}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('clears query when clear button is clicked', () => {
    render(
      <GlobalSearchModal
        isOpen={true}
        onClose={vi.fn()}
        onSelectCase={vi.fn()}
        onSelectEntity={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search authorized cases, entities/i);
    fireEvent.change(searchInput, { target: { value: 'Test Query' } });
    expect(searchInput).toHaveValue('Test Query');

    const clearBtn = screen.getByRole('button', { name: /Clear search input/i });
    fireEvent.click(clearBtn);

    expect(searchInput).toHaveValue('');
    expect(screen.getByText('Global Investigative Search')).toBeInTheDocument();
  });
});
