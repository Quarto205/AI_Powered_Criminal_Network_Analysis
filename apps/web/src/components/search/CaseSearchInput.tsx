import React, { useState, useRef, useEffect } from 'react';
import { EntitySearchResult } from '../../types/search';
import { searchCaseEntities } from '../../mocks/searchMock';

export interface CaseSearchInputProps {
  activeCaseId: string;
  onSelectEntity: (entity: EntitySearchResult) => void;
  placeholder?: string;
}

export const CaseSearchInput: React.FC<CaseSearchInputProps> = ({
  activeCaseId,
  onSelectEntity,
  placeholder = 'Search entities in active case…'
}) => {
  const [query, setQuery] = useState<string>('');
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const results = query.trim().length > 0 ? searchCaseEntities(activeCaseId, query, 10) : [];

  // Close dropdown on click outside or Escape
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    setIsOpen(val.trim().length > 0);
  };

  const handleClear = () => {
    setQuery('');
    setIsOpen(false);
  };

  const handleSelect = (entity: EntitySearchResult) => {
    onSelectEntity(entity);
    setIsOpen(false);
  };

  return (
    <div
      ref={containerRef}
      className="case-search-container"
      role="search"
      aria-label="Case entity search"
    >
      <div className="case-search-box">
        <span className="case-search-icon" aria-hidden="true">🔎</span>
        <label htmlFor="case-search-input" className="visually-hidden">
          Search entities in active case
        </label>
        <input
          id="case-search-input"
          type="search"
          className="case-search-input"
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            if (query.trim().length > 0) {
              setIsOpen(true);
            }
          }}
          aria-label="Search entities in active case"
          aria-expanded={isOpen}
          aria-controls="case-search-results-list"
          autoComplete="off"
        />
        {query && (
          <button
            type="button"
            className="case-search-clear"
            onClick={handleClear}
            aria-label="Clear case search query"
          >
            ×
          </button>
        )}
      </div>

      {/* Case Scoped Results Popover */}
      {isOpen && query.trim().length > 0 && (
        <div
          id="case-search-results-list"
          className="case-search-dropdown"
          role="listbox"
          aria-label="Case entities search results"
        >
          <div className="case-search-dropdown-header">
            <span className="case-search-scope-label">
              CURRENT CASE ENTITIES ({results.length})
            </span>
          </div>

          {results.length === 0 ? (
            <div className="case-search-empty-state" role="status">
              No matching entities found in current case.
            </div>
          ) : (
            <div className="case-search-results-list">
              {results.map((entity) => (
                <button
                  key={entity.entity_id}
                  type="button"
                  className="case-search-result-item"
                  role="option"
                  aria-selected="false"
                  onClick={() => handleSelect(entity)}
                  aria-label={`${entity.canonical_name} (${entity.entity_type}), ${entity.masked_identifier}`}
                >
                  <div className="case-result-item-main">
                    <span className={`result-badge entity-badge entity-type-${entity.entity_type.toLowerCase()}`}>
                      {entity.entity_type}
                    </span>
                    <span className="case-result-name">{entity.canonical_name}</span>
                  </div>
                  <span className="case-result-masked">{entity.masked_identifier}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
