import React, { useState, useEffect, useRef } from 'react';
import { useSearch } from '../../context/SearchContext';
import { useCase } from '../../context/CaseContext';
import { Search, User, FileText, Building, Clock, ArrowRight, X } from 'lucide-react';

export const CommandPalette: React.FC = () => {
  const { isSearchOpen, closeSearch, query, setQuery } = useSearch();
  const { entities, evidenceDocs, timelineEvents, inspectInGraph, viewDocumentDossier, setActiveTab } = useCase();
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (isSearchOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  }, [isSearchOpen]);

  if (!isSearchOpen) return null;

  const normalized = query.toLowerCase().trim();

  // Filter within active case scope
  const filteredEntities = entities.filter(
    (e) =>
      e.name.toLowerCase().includes(normalized) ||
      e.primaryRole.toLowerCase().includes(normalized) ||
      e.aliases.some((a) => a.toLowerCase().includes(normalized))
  );

  const filteredDocs = evidenceDocs.filter(
    (d) =>
      d.title.toLowerCase().includes(normalized) ||
      d.filename.toLowerCase().includes(normalized) ||
      d.category.toLowerCase().includes(normalized)
  );

  const filteredEvents = timelineEvents.filter(
    (ev) =>
      ev.title.toLowerCase().includes(normalized) ||
      ev.description.toLowerCase().includes(normalized)
  );

  const allResults = [
    ...filteredEntities.map((e) => ({
      type: 'entity' as const,
      id: e.id,
      title: e.name,
      subtitle: e.primaryRole,
      badge: e.type,
      action: () => inspectInGraph(e.id),
    })),
    ...filteredDocs.map((d) => ({
      type: 'document' as const,
      id: d.id,
      title: d.title,
      subtitle: `${d.category} · ${d.fileSize}`,
      badge: 'DOC',
      action: () => viewDocumentDossier(d.id),
    })),
    ...filteredEvents.map((ev) => ({
      type: 'event' as const,
      id: ev.id,
      title: ev.title,
      subtitle: ev.displayTime,
      badge: ev.type,
      action: () => {
        setActiveTab('timeline');
      },
    })),
  ];

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, allResults.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + allResults.length) % Math.max(1, allResults.length));
    } else if (e.key === 'Enter' && allResults[selectedIndex]) {
      e.preventDefault();
      allResults[selectedIndex].action();
      closeSearch();
    }
  };

  return (
    <div
      onClick={closeSearch}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(11, 28, 48, 0.4)',
        backdropFilter: 'blur(4px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '12vh',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '620px',
          backgroundColor: 'var(--cnas-surface)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--cnas-border)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Search Input Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '1rem 1.25rem',
            borderBottom: '1px solid var(--cnas-border)',
          }}
        >
          <Search size={20} color="var(--cnas-blue)" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Search entities, accounts, wire transfers, evidence in active case..."
            style={{
              flex: 1,
              border: 'none',
              fontSize: '15px',
              fontWeight: 500,
              color: 'var(--cnas-text-primary)',
              backgroundColor: 'transparent',
              outline: 'none',
              padding: 0,
              boxShadow: 'none',
            }}
          />
          <button
            onClick={closeSearch}
            style={{
              padding: '4px',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--cnas-text-muted)',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Results Stream */}
        <div
          style={{
            maxHeight: '400px',
            overflowY: 'auto',
            padding: '0.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
          }}
        >
          {allResults.length === 0 ? (
            <div
              style={{
                padding: '2.5rem 1rem',
                textAlign: 'center',
                color: 'var(--cnas-text-muted)',
                fontSize: '13px',
              }}
            >
              No matching intelligence records found in active case.
            </div>
          ) : (
            allResults.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={`${item.type}-${item.id}`}
                  onClick={() => {
                    item.action();
                    closeSearch();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor: isSelected ? 'var(--cnas-surface-container)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'var(--cnas-surface)',
                        border: '1px solid var(--cnas-border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--cnas-navy)',
                      }}
                    >
                      {item.type === 'entity' && <User size={14} />}
                      {item.type === 'document' && <FileText size={14} />}
                      {item.type === 'event' && <Clock size={14} />}
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--cnas-text-primary)' }}>
                        {item.title}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                        {item.subtitle}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      style={{
                        fontFamily: 'var(--font-code)',
                        fontSize: '10px',
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-xs)',
                        backgroundColor: 'var(--cnas-surface-subtle)',
                        color: 'var(--cnas-text-secondary)',
                        border: '1px solid var(--cnas-border)',
                      }}
                    >
                      {item.badge}
                    </span>
                    <ArrowRight size={14} color="var(--cnas-text-muted)" />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer controls */}
        <div
          style={{
            padding: '0.5rem 1rem',
            borderTop: '1px solid var(--cnas-border)',
            backgroundColor: 'var(--cnas-surface-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '11px',
            color: 'var(--cnas-text-muted)',
          }}
        >
          <span>Use ↑ ↓ to navigate, ↵ to inspect</span>
          <span>Esc to close</span>
        </div>
      </div>
    </div>
  );
};
