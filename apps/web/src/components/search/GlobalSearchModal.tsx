import React, { useState, useEffect, useRef } from 'react';
import {
  CaseSearchResult,
  EntitySearchResult,
  GlobalSearchPayload
} from '../../types/search';
import { searchAuthorizedRecords } from '../../mocks/searchMock';

export interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectEntity: (entity: EntitySearchResult) => void;
  onSelectCase: (caseItem: CaseSearchResult) => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  onSelectEntity,
  onSelectCase
}) => {
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<GlobalSearchPayload>({ cases: [], entities: [] });
  const inputRef = useRef<HTMLInputElement | null>(null);
  const modalContentRef = useRef<HTMLDivElement | null>(null);

  // Auto-focus input when opened and reset query
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setResults({ cases: [], entities: [] });
      // Small timeout to ensure DOM is ready for focus
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Handle Escape key to close modal
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Execute deterministic search on query change
  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    const searchRes = searchAuthorizedRecords(val);
    setResults(searchRes);
  };

  const handleClearQuery = () => {
    setQuery('');
    setResults({ cases: [], entities: [] });
    inputRef.current?.focus();
  };

  if (!isOpen) {
    return null;
  }

  const isQueryEmpty = query.trim().length === 0;
  const hasResults = results.cases.length > 0 || results.entities.length > 0;

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={(e) => {
        if (modalContentRef.current && !modalContentRef.current.contains(e.target as Node)) {
          onClose();
        }
      }}
    >
      <div
        ref={modalContentRef}
        className="global-search-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Global Search Modal"
      >
        {/* Modal Search Input Header */}
        <div className="modal-search-header">
          <div className="modal-search-input-wrapper">
            <span className="search-icon" aria-hidden="true">🔍</span>
            <label htmlFor="global-search-input" className="visually-hidden">
              Search authorized cases and entities
            </label>
            <input
              id="global-search-input"
              ref={inputRef}
              type="search"
              className="modal-search-input"
              placeholder="Search authorized cases, entities, names or masked identifiers…"
              value={query}
              onChange={handleQueryChange}
              aria-label="Search authorized cases and entities"
              autoComplete="off"
            />
            {query && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={handleClearQuery}
                aria-label="Clear search input"
              >
                ×
              </button>
            )}
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close search dialog"
          >
            Esc
          </button>
        </div>

        {/* Modal Results & Content Body */}
        <div className="modal-search-body" role="region" aria-label="Search Results">
          {isQueryEmpty && (
            <div className="search-empty-prompt" role="status">
              <span className="prompt-icon" aria-hidden="true">⌘</span>
              <p className="prompt-title">Global Investigative Search</p>
              <p className="prompt-subtext">
                Search across authorized cases and canonical entities by title, reference code (e.g.{' '}
                <code>DL-2026-CR-0192</code>), entity name, or masked identifier (e.g.{' '}
                <code>+91-XXXXX</code>, <code>SBIN000XXXX</code>).
              </p>
            </div>
          )}

          {!isQueryEmpty && !hasResults && (
            <div className="search-no-results" role="status">
              <p className="no-results-title">No matching authorized cases or entities found.</p>
              <p className="no-results-subtext">
                Verify search parameters or reference numbers. Access is restricted to authorized case dockets.
              </p>
            </div>
          )}

          {!isQueryEmpty && hasResults && (
            <div className="search-results-container">
              {/* Section 1: Authorized Cases */}
              {results.cases.length > 0 && (
                <div className="search-result-section">
                  <div className="result-section-header">
                    <span className="result-section-title">
                      Authorized Cases ({results.cases.length})
                    </span>
                  </div>
                  <div className="result-section-list">
                    {results.cases.map((c) => (
                      <button
                        key={c.case_id}
                        type="button"
                        className="search-result-card case-card"
                        onClick={() => {
                          onSelectCase(c);
                          onClose();
                        }}
                        aria-label={`Case: ${c.case_code} — ${c.title}, Jurisdiction: ${c.jurisdiction}`}
                      >
                        <div className="result-card-primary">
                          <span className="result-badge case-code-badge">{c.case_code}</span>
                          <span className="result-title">{c.title}</span>
                        </div>
                        <div className="result-card-secondary">
                          <span className="result-meta-label">Jurisdiction:</span>{' '}
                          <span className="result-meta-value">{c.jurisdiction}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Section 2: Matched Entities */}
              {results.entities.length > 0 && (
                <div className="search-result-section">
                  <div className="result-section-header">
                    <span className="result-section-title">
                      Matched Entities ({results.entities.length})
                    </span>
                  </div>
                  <div className="result-section-list">
                    {results.entities.map((e) => (
                      <button
                        key={e.entity_id}
                        type="button"
                        className="search-result-card entity-card"
                        onClick={() => {
                          onSelectEntity(e);
                          onClose();
                        }}
                        aria-label={`Entity: ${e.canonical_name} (${e.entity_type}), Identifier: ${e.masked_identifier}, Case: ${e.case_code || 'Active'}`}
                      >
                        <div className="result-card-primary">
                          <span className={`result-badge entity-badge entity-type-${e.entity_type.toLowerCase()}`}>
                            {e.entity_type}
                          </span>
                          <span className="result-title">{e.canonical_name}</span>
                          <span className="result-masked-tag">{e.masked_identifier}</span>
                        </div>
                        <div className="result-card-secondary">
                          {e.case_code && (
                            <span className="result-case-link">Case: {e.case_code}</span>
                          )}
                          <span className="result-status-tag">Status: {e.status}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer / Navigation Instructions */}
        <div className="modal-search-footer">
          <div className="search-footer-shortcuts">
            <span className="shortcut-tag">
              <kbd>Esc</kbd> to close
            </span>
            <span className="shortcut-tag">
              <kbd>↵</kbd> to select
            </span>
          </div>
          <span className="search-footer-status">
            Authorized Scope: Active Session
          </span>
        </div>
      </div>
    </div>
  );
};
