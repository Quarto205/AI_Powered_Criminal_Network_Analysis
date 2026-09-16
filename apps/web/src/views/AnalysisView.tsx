import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import { Badge } from '../components/ui/Badge';
import {
  Sparkles,
  RefreshCw,
  Share2,
  Sliders,
  ChevronRight,
  TrendingUp,
  Layers,
  Network,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

export const AnalysisView: React.FC = () => {
  const { priorityLeads, inspectInGraph } = useCase();
  const [activeSubTab, setActiveSubTab] = useState<'leads' | 'patterns' | 'resolution'>('leads');
  const [hopDepth, setHopDepth] = useState<number>(2);
  const [confidenceCutoff, setConfidenceCutoff] = useState<number>(85);
  const [selectedTopology, setSelectedTopology] = useState<string>('Force-Directed');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Sub-Navigation & Header Bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', overflowX: 'auto' }}>
          <button
            onClick={() => setActiveSubTab('leads')}
            style={{
              padding: '0.45rem 0.85rem',
              borderRadius: 'var(--radius-lg)',
              fontSize: '12px',
              fontWeight: 700,
              backgroundColor: activeSubTab === 'leads' ? 'var(--cnas-navy)' : 'var(--cnas-surface-subtle)',
              color: activeSubTab === 'leads' ? '#ffffff' : 'var(--cnas-text-secondary)',
              border: '1px solid var(--cnas-border)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Sparkles size={14} color={activeSubTab === 'leads' ? '#ffffff' : 'var(--cnas-ai-primary)'} />
            <span>AI Leads ({priorityLeads.length})</span>
          </button>

          <button
            onClick={() => setActiveSubTab('patterns')}
            style={{
              padding: '0.45rem 0.85rem',
              borderRadius: 'var(--radius-lg)',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: activeSubTab === 'patterns' ? 'var(--cnas-navy)' : 'var(--cnas-surface-subtle)',
              color: activeSubTab === 'patterns' ? '#ffffff' : 'var(--cnas-text-secondary)',
              border: '1px solid var(--cnas-border)',
            }}
          >
            Patterns & Motifs
          </button>

          <button
            onClick={() => setActiveSubTab('resolution')}
            style={{
              padding: '0.45rem 0.85rem',
              borderRadius: 'var(--radius-lg)',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: activeSubTab === 'resolution' ? 'var(--cnas-navy)' : 'var(--cnas-surface-subtle)',
              color: activeSubTab === 'resolution' ? '#ffffff' : 'var(--cnas-text-secondary)',
              border: '1px solid var(--cnas-border)',
            }}
          >
            Entity Resolution
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--cnas-surface-subtle)', border: '1px solid var(--cnas-border)', padding: '4px 8px', borderRadius: 'var(--radius-md)' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)' }}>Engine:</span>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-code)', fontWeight: 700, color: 'var(--cnas-blue)' }}>GNN-SAGE-v2</span>
          </div>

          <button
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.45rem 0.85rem',
              backgroundColor: 'var(--cnas-surface)',
              border: '1px solid var(--cnas-border)',
              borderRadius: 'var(--radius-lg)',
              color: 'var(--cnas-navy)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <RefreshCw size={13} />
            <span>Re-cluster</span>
          </button>
        </div>
      </div>

      {/* 2. Primary 3-Column Analytical Workspace Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Configuration Drawer (3 Columns) */}
        <div
          style={{
            gridColumn: 'span 3',
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.25rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Sliders size={16} color="var(--cnas-navy)" />
              <h2 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                Graph Controls
              </h2>
            </div>
            <button
              onClick={() => {
                setHopDepth(2);
                setConfidenceCutoff(85);
                setSelectedTopology('Force-Directed');
              }}
              style={{ fontSize: '11px', color: 'var(--cnas-blue)', fontWeight: 600 }}
            >
              Reset
            </button>
          </div>

          {/* Hop Depth */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 600, color: 'var(--cnas-text-secondary)' }}>
              <span>Hop Depth</span>
              <span style={{ fontFamily: 'var(--font-code)', color: 'var(--cnas-navy)' }}>{hopDepth} Hops</span>
            </div>
            <input
              type="range"
              min={1}
              max={4}
              value={hopDepth}
              onChange={(e) => setHopDepth(Number(e.target.value))}
              style={{ accentColor: 'var(--cnas-blue)', cursor: 'pointer' }}
            />
          </div>

          {/* Spatial Topology */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)' }}>
              Spatial Topology
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
              {['Force-Directed', 'Concentric', 'Hierarchical', 'Spectral'].map((top) => (
                <button
                  key={top}
                  onClick={() => setSelectedTopology(top)}
                  style={{
                    padding: '0.4rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '11px',
                    fontWeight: 600,
                    textAlign: 'left',
                    backgroundColor: selectedTopology === top ? 'var(--cnas-surface-high)' : 'var(--cnas-surface-subtle)',
                    color: selectedTopology === top ? 'var(--cnas-navy)' : 'var(--cnas-text-muted)',
                    border: '1px solid var(--cnas-border)',
                  }}
                >
                  {top}
                </button>
              ))}
            </div>
          </div>

          {/* AI Cutoff Slider */}
          <div
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--cnas-ai-subtle)',
              border: '1px dashed var(--cnas-ai-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--cnas-ai-text)', fontSize: '12px', fontWeight: 700 }}>
                <Sparkles size={14} />
                <span>AI Confidence Cutoff</span>
              </div>
              <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', fontWeight: 700, color: 'var(--cnas-ai-text)' }}>
                {confidenceCutoff}%
              </span>
            </div>
            <input
              type="range"
              min={70}
              max={99}
              value={confidenceCutoff}
              onChange={(e) => setConfidenceCutoff(Number(e.target.value))}
              style={{ accentColor: 'var(--cnas-ai-primary)', cursor: 'pointer' }}
            />
          </div>
        </div>

        {/* Right / Main: Leads & Analysis Workspace (9 Columns) */}
        <div style={{ gridColumn: 'span 9', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {activeSubTab === 'leads' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {priorityLeads.map((lead) => (
                <div
                  key={lead.id}
                  style={{
                    backgroundColor: 'var(--cnas-surface)',
                    border: '1px solid var(--cnas-border)',
                    borderRadius: 'var(--radius-xl)',
                    padding: '1.25rem',
                    boxShadow: 'var(--shadow-xs)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span
                        style={{
                          fontFamily: 'var(--font-code)',
                          fontSize: '11px',
                          fontWeight: 700,
                          backgroundColor: lead.rank === 1 ? 'var(--cnas-navy)' : 'var(--cnas-risk)',
                          color: '#ffffff',
                          padding: '2px 8px',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        RANK 0{lead.rank}
                      </span>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          backgroundColor: 'var(--cnas-ai-subtle)',
                          color: 'var(--cnas-ai-text)',
                          border: '1px dashed var(--cnas-ai-border)',
                          padding: '2px 8px',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        Predicted Association Score: {lead.confidenceScore}%
                      </span>
                    </div>

                    <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>
                      Identified {lead.identifiedAgo}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {lead.title}
                  </h3>

                  <p style={{ fontSize: '13px', color: 'var(--cnas-text-secondary)', lineHeight: 1.5 }}>
                    {lead.description}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--cnas-border)', paddingTop: '0.65rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                      <span>Target Entities:</span>
                      {lead.targetEntities.map((tid) => (
                        <span key={tid} style={{ fontFamily: 'var(--font-code)', color: 'var(--cnas-navy)', fontWeight: 600 }}>
                          {tid}
                        </span>
                      ))}
                    </div>

                    <button
                      onClick={() => inspectInGraph(lead.targetEntities[0])}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '4px 10px',
                        backgroundColor: 'var(--cnas-navy)',
                        color: '#ffffff',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '11px',
                        fontWeight: 600,
                        boxShadow: 'var(--shadow-xs)',
                      }}
                    >
                      <span>Investigate in Network</span>
                      <ChevronRight size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeSubTab === 'patterns' && (
            <div
              style={{
                backgroundColor: 'var(--cnas-surface)',
                border: '1px solid var(--cnas-border)',
                borderRadius: 'var(--radius-xl)',
                padding: '1.5rem',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--cnas-navy)', marginBottom: '0.5rem' }}>
                Detected Hawala Structural Motifs
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--cnas-text-secondary)', lineHeight: 1.5 }}>
                Algorithmic subgraph matching isolates recurring topologies characteristic of smurfing fan-out, mirror overseas entities, and rapid cash liquidation hubs.
              </p>
            </div>
          )}

          {activeSubTab === 'resolution' && (
            <div
              style={{
                backgroundColor: 'var(--cnas-surface)',
                border: '1px solid var(--cnas-border)',
                borderRadius: 'var(--radius-xl)',
                padding: '1.5rem',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--cnas-navy)', marginBottom: '0.5rem' }}>
                Entity Disambiguation & Resolution Queue
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--cnas-text-secondary)', lineHeight: 1.5 }}>
                Cross-document name variant resolution pairing PAN, passport, and MSISDN identifiers to establish unified suspect dossiers.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
