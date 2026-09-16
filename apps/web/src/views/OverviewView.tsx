import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import { Badge } from '../components/ui/Badge';
import { AnimatedCounter } from '../components/ui/AnimatedCounter';
import { AmbientConstellation } from '../components/3d/AmbientConstellation';
import {
  FileText,
  Share2,
  FolderOpen,
  ArrowRight,
  Shield,
  Clock,
  Printer,
  Plus,
  Sparkles,
  ChevronRight,
  Radio,
  ExternalLink,
  Layers,
  Box
} from 'lucide-react';

export const OverviewView: React.FC = () => {
  const {
    activeCase,
    setActiveTab,
    inspectInGraph,
    viewDocumentDossier,
    priorityLeads,
    timelineEvents,
    evidenceDocs
  } = useCase();

  const [use3dHero, setUse3dHero] = useState<boolean>(false);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* 1. Case Master Bar */}
      <section
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          borderBottom: '1px solid var(--cnas-border)',
          paddingBottom: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1.25rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', maxWidth: '780px' }}>
            <h1
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '24px',
                fontWeight: 800,
                color: 'var(--cnas-navy)',
                letterSpacing: '-0.02em',
                lineHeight: 1.25,
              }}
            >
              {activeCase.title}
            </h1>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '12px', color: 'var(--cnas-text-muted)' }}>
              <span>
                Lead Investigator:{' '}
                <strong style={{ color: 'var(--cnas-text-primary)' }}>
                  {activeCase.leadInvestigator.name}
                </strong>
              </span>
              <span>•</span>
              <span>
                Current Shift:{' '}
                <span style={{ fontFamily: 'var(--font-code)', color: 'var(--cnas-text-primary)', fontWeight: 600 }}>
                  {activeCase.stage}
                </span>
              </span>
            </div>
          </div>

          {/* Quick Case Utility Triggers */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <button
              onClick={() => window.print()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.5rem 0.85rem',
                backgroundColor: 'var(--cnas-surface)',
                border: '1px solid var(--cnas-border)',
                borderRadius: 'var(--radius-lg)',
                color: 'var(--cnas-navy)',
                fontSize: '12px',
                fontWeight: 600,
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <Printer size={15} />
              <span>Briefing PDF</span>
            </button>

            <button
              onClick={() => setActiveTab('evidence')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.5rem 0.95rem',
                backgroundColor: 'var(--cnas-navy)',
                color: '#ffffff',
                borderRadius: 'var(--radius-lg)',
                fontSize: '12px',
                fontWeight: 600,
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <Plus size={15} />
              <span>Attach Discovery</span>
            </button>
          </div>
        </div>
      </section>

      {/* 2. Unadorned 4-Metric Strip */}
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {/* Metric 1 */}
        <div
          style={{
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.25rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--cnas-text-muted)' }}>
              Case Status
            </span>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: 'var(--cnas-verified)',
                boxShadow: '0 0 0 3px rgba(5, 150, 105, 0.15)',
              }}
              className="pulse-live"
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 800, color: 'var(--cnas-navy)' }}>
              Active
            </span>
            <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', fontWeight: 600, color: 'var(--cnas-verified)' }}>
              Live Feed
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', marginTop: '4px' }}>
            Interception & nodal surveillance
          </span>
        </div>

        {/* Metric 2 */}
        <div
          onClick={() => setActiveTab('network')}
          style={{
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.25rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--cnas-text-muted)' }}>
              Entity Graph
            </span>
            <Share2 size={16} color="var(--cnas-blue)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 800, color: 'var(--cnas-navy)' }}>
              <AnimatedCounter value={activeCase.entityCount} />
            </span>
            <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
              Mapped
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', marginTop: '4px' }}>
            4 targets under direct observation
          </span>
        </div>

        {/* Metric 3 */}
        <div
          onClick={() => setActiveTab('evidence')}
          style={{
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.25rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--cnas-text-muted)' }}>
              Evidence Ledger
            </span>
            <FolderOpen size={16} color="var(--cnas-navy)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 800, color: 'var(--cnas-navy)' }}>
              <AnimatedCounter value={activeCase.evidenceCount} />
            </span>
            <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
              Files
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', marginTop: '4px' }}>
            Chain of custody hash-verified
          </span>
        </div>

        {/* Metric 4 */}
        <div
          onClick={() => setActiveTab('analysis')}
          style={{
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.25rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--cnas-text-muted)' }}>
              Priority Leads
            </span>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--cnas-risk)' }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 800, color: 'var(--cnas-risk)' }}>
              <AnimatedCounter value={activeCase.criticalLeadsCount} />
            </span>
            <span style={{ fontFamily: 'var(--font-code)', fontSize: '11px', fontWeight: 600, color: 'var(--cnas-risk)' }}>
              Critical
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', marginTop: '4px' }}>
            High inference confidence (&gt;88%)
          </span>
        </div>
      </section>

      {/* 3. Central Workstation Mosaic (Network Canvas & Priority Feed) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        {/* Visual Topology Preview (8 Columns) */}
        <div
          style={{
            gridColumn: 'span 8',
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <Share2 size={18} color="var(--cnas-navy)" />
                <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                  Nodal Core Snapshot
                </h2>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--cnas-text-muted)', marginTop: '2px' }}>
                Primary nexus identified around central facilitator
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              {/* 3D vs 2D Toggle */}
              <button
                onClick={() => setUse3dHero((prev) => !prev)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--cnas-surface-subtle)',
                  border: '1px solid var(--cnas-border)',
                  fontSize: '11px',
                  fontWeight: 600,
                  color: 'var(--cnas-navy)',
                }}
                title="Toggle between 3D Constellation and 2D Topological Stage"
              >
                {use3dHero ? <Box size={13} color="var(--cnas-blue)" /> : <Layers size={13} />}
                <span>{use3dHero ? '3D View' : '2D Graph'}</span>
              </button>

              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-code)',
                  color: 'var(--cnas-text-muted)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--cnas-surface-subtle)',
                }}
              >
                4 Linked Hubs
              </span>

              <button
                onClick={() => setActiveTab('network')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  color: 'var(--cnas-blue)',
                  fontSize: '12px',
                  fontWeight: 600,
                }}
              >
                <span>Explore Network</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>

          {/* Graph Stage Container */}
          <div
            style={{
              position: 'relative',
              width: '100%',
              height: '380px',
              backgroundColor: 'rgba(239, 244, 255, 0.45)',
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid var(--cnas-surface-high)',
            }}
          >
            {use3dHero ? (
              <AmbientConstellation count={48} />
            ) : (
              <>
                {/* Ambient Dot Matrix */}
                <svg
                  style={{
                    position: 'absolute',
                    inset: 0,
                    width: '100%',
                    height: '100%',
                    opacity: 0.6,
                    pointerEvents: 'none',
                  }}
                >
                  <defs>
                    <pattern id="dot-matrix-overview" width="28" height="28" patternUnits="userSpaceOnUse">
                      <circle cx="2" cy="2" r="1" fill="#cbdbf5" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#dot-matrix-overview)" />
                </svg>

                {/* SVG Connections */}
                <svg
                  viewBox="0 0 760 380"
                  style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
                >
                  {/* Orbit rings */}
                  <circle cx="380" cy="190" r="90" fill="none" stroke="#dce9ff" strokeWidth="1" opacity="0.8" />
                  <circle cx="380" cy="190" r="170" fill="none" stroke="#dce9ff" strokeWidth="1" strokeDasharray="6 6" opacity="0.5" />

                  {/* Tariq to Al-Zubair */}
                  <line x1="380" y1="190" x2="190" y2="100" stroke="#316bf3" strokeWidth="2" strokeDasharray="4 4" />
                  <text x="270" y="135" fill="#43474e" fontSize="10" fontFamily="Inter">₹1.8 Cr Hawala</text>

                  {/* Tariq to ICICI */}
                  <line x1="380" y1="190" x2="570" y2="90" stroke="#0051d5" strokeWidth="2" />
                  <text x="490" y="130" fill="#0051d5" fontSize="10" fontWeight="600" fontFamily="Inter">Layered Trans.</text>

                  {/* Tariq to Vikas S. */}
                  <line x1="380" y1="190" x2="380" y2="305" stroke="#a8c8f8" strokeWidth="1.5" />
                  <text x="390" y="255" fill="#43474e" fontSize="10" fontFamily="Inter">VoIP CDR (42x)</text>

                  {/* Tariq to Chandni Chowk */}
                  <line x1="380" y1="190" x2="180" y2="280" stroke="#e11d48" strokeWidth="1.5" strokeDasharray="3 3" />
                  <text x="235" y="248" fill="#ba1a1a" fontSize="10" fontWeight="600" fontFamily="Inter">Cash Courier</text>
                </svg>

                {/* Node: Tariq M. (Center) */}
                <div
                  onClick={() => inspectInGraph('ent-tariq')}
                  style={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <div
                    style={{
                      width: '60px',
                      height: '60px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--cnas-navy)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: 'var(--shadow-md)',
                      border: '6px solid rgba(168, 200, 248, 0.4)',
                    }}
                  >
                    <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '18px' }}>TM</span>
                  </div>
                  <div
                    style={{
                      marginTop: '6px',
                      textAlign: 'center',
                      backgroundColor: 'var(--cnas-surface)',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-sm)',
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)', display: 'block' }}>
                      Tariq M.
                    </span>
                    <span style={{ fontSize: '9px', fontWeight: 700, color: 'var(--cnas-risk)', textTransform: 'uppercase' }}>
                      Prime Facilitator
                    </span>
                  </div>
                </div>

                {/* Node: Al-Zubair Exports (Top Left) */}
                <div
                  onClick={() => inspectInGraph('ent-al-zubair')}
                  style={{
                    position: 'absolute',
                    left: '16%',
                    top: '16%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <div
                    style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--cnas-surface)',
                      border: '2px solid var(--cnas-blue)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--cnas-blue)',
                      fontWeight: 700,
                      fontSize: '12px',
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    AZ
                  </div>
                  <div style={{ marginTop: '4px', textAlign: 'center', backgroundColor: 'var(--cnas-surface)', padding: '2px 6px', borderRadius: 'var(--radius-xs)', boxShadow: 'var(--shadow-xs)' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--cnas-navy)', display: 'block' }}>Al-Zubair FZE</span>
                    <span style={{ fontSize: '9px', color: 'var(--cnas-text-muted)' }}>Dubai Conduit</span>
                  </div>
                </div>

                {/* Node: ICICI Acct ••••4921 (Top Right) */}
                <div
                  onClick={() => inspectInGraph('ent-icici-acct')}
                  style={{
                    position: 'absolute',
                    right: '16%',
                    top: '14%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <div
                    style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--cnas-surface)',
                      border: '2px solid var(--cnas-verified)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--cnas-verified)',
                      fontWeight: 700,
                      fontSize: '12px',
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    IC
                  </div>
                  <div style={{ marginTop: '4px', textAlign: 'center', backgroundColor: 'var(--cnas-surface)', padding: '2px 6px', borderRadius: 'var(--radius-xs)', boxShadow: 'var(--shadow-xs)' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--cnas-navy)', display: 'block' }}>ICICI ••••4921</span>
                    <span style={{ fontSize: '9px', color: 'var(--cnas-verified)', fontWeight: 600 }}>Shell Mirror</span>
                  </div>
                </div>

                {/* Node: Vikas S. (Bottom Center) */}
                <div
                  onClick={() => inspectInGraph('ent-vikas')}
                  style={{
                    position: 'absolute',
                    left: '50%',
                    bottom: '12%',
                    transform: 'translateX(-50%)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <div
                    style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--cnas-surface)',
                      border: '2px solid var(--cnas-navy)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--cnas-navy)',
                      fontWeight: 700,
                      fontSize: '11px',
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    VS
                  </div>
                  <div style={{ marginTop: '4px', textAlign: 'center', backgroundColor: 'var(--cnas-surface)', padding: '2px 6px', borderRadius: 'var(--radius-xs)', boxShadow: 'var(--shadow-xs)' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--cnas-navy)', display: 'block' }}>Vikas S.</span>
                    <span style={{ fontSize: '9px', color: 'var(--cnas-text-muted)' }}>Logistics</span>
                  </div>
                </div>

                {/* Node: Chandni Chowk Point (Bottom Left) */}
                <div
                  onClick={() => inspectInGraph('ent-chandni-chowk')}
                  style={{
                    position: 'absolute',
                    left: '16%',
                    bottom: '16%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <div
                    style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--cnas-surface)',
                      border: '2px solid var(--cnas-risk)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--cnas-risk)',
                      fontWeight: 700,
                      fontSize: '11px',
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    CC
                  </div>
                  <div style={{ marginTop: '4px', textAlign: 'center', backgroundColor: 'var(--cnas-surface)', padding: '2px 6px', borderRadius: 'var(--radius-xs)', boxShadow: 'var(--shadow-xs)' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--cnas-navy)', display: 'block' }}>Chandni Chowk</span>
                    <span style={{ fontSize: '9px', color: 'var(--cnas-risk)', fontWeight: 600 }}>Dispersal Hub</span>
                  </div>
                </div>
              </>
            )}

            {/* In-canvas Quick Focus Tag */}
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                right: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(8px)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-xs)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '11px',
                color: 'var(--cnas-text-muted)',
                border: '1px solid var(--cnas-border)',
              }}
            >
              <span>Graph Density: <strong style={{ color: 'var(--cnas-text-primary)' }}>Moderate (k=4)</strong></span>
              <span>·</span>
              <span>Clustering: <strong style={{ color: 'var(--cnas-text-primary)' }}>0.78</strong></span>
            </div>
          </div>

          {/* Graph Contextual Footer Strip */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '0.85rem',
              fontSize: '11px',
              color: 'var(--cnas-text-muted)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--cnas-navy)' }} />
                Facilitator Core
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--cnas-blue)' }} />
                Banking & Corporate
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--cnas-risk)' }} />
                Intercept / Dispersal
              </span>
            </div>
            <span style={{ fontFamily: 'var(--font-code)' }}>Layout: Force-Directed Minimal (Euclidean)</span>
          </div>
        </div>

        {/* Right Side: Priority Leads & Target Briefing (4 Columns) */}
        <div style={{ gridColumn: 'span 4', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Priority Leads Card */}
          <div
            style={{
              backgroundColor: 'var(--cnas-surface)',
              border: '1px solid var(--cnas-border)',
              borderRadius: 'var(--radius-xl)',
              padding: '1.25rem',
              boxShadow: 'var(--shadow-xs)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Sparkles size={16} color="var(--cnas-risk)" />
                <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                  Priority Leads
                </h2>
              </div>
              <Badge variant="risk" size="sm">
                2 Urgent
              </Badge>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {priorityLeads.slice(0, 2).map((lead) => (
                <div
                  key={lead.id}
                  onClick={() => setActiveTab('analysis')}
                  style={{
                    padding: '0.85rem',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor: 'var(--cnas-surface-subtle)',
                    border: '1px solid var(--cnas-border)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <span
                        style={{
                          fontFamily: 'var(--font-code)',
                          fontSize: '10px',
                          fontWeight: 700,
                          backgroundColor: lead.rank === 1 ? 'var(--cnas-navy)' : 'var(--cnas-risk)',
                          color: '#ffffff',
                          padding: '1px 5px',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        RANK 0{lead.rank}
                      </span>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 600,
                          padding: '1px 5px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'var(--cnas-ai-subtle)',
                          color: 'var(--cnas-ai-text)',
                        }}
                      >
                        GNN {lead.confidenceScore}% Match
                      </span>
                    </div>
                    <Sparkles size={13} color="var(--cnas-ai-primary)" />
                  </div>

                  <h3 style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-text-primary)' }}>
                    {lead.title}
                  </h3>
                  <p style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', lineHeight: 1.4 }}>
                    {lead.description}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px', paddingTop: '4px', borderTop: '1px solid var(--cnas-border)' }}>
                    <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>
                      Identified: {lead.identifiedAgo}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--cnas-blue)', fontWeight: 600, display: 'flex', alignItems: 'center' }}>
                      <span>View Lead</span>
                      <ChevronRight size={13} />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Surveillance Live Feed Callout */}
          <div
            style={{
              padding: '0.85rem 1rem',
              borderRadius: 'var(--radius-xl)',
              backgroundColor: 'var(--cnas-navy)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(255, 255, 255, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Radio size={16} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '12px', fontWeight: 700 }}>Live CDR Intercept Stream</span>
                <span style={{ fontSize: '10px', color: 'var(--cnas-surface-dim)' }}>
                  Active listening node: Delhi NCR
                </span>
              </div>
            </div>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: 'var(--cnas-verified)',
                boxShadow: '0 0 0 3px rgba(5, 150, 105, 0.3)',
              }}
              className="pulse-live"
            />
          </div>
        </div>
      </div>

      {/* 4. Bottom Workspace Deck: Chronological Timeline Stream & Forensic Ledger */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        {/* Incident Stream (8 Columns) */}
        <div
          style={{
            gridColumn: 'span 8',
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <Clock size={16} color="var(--cnas-navy)" />
                <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                  Incident Stream
                </h2>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                Chronological record of live transmissions and field logs
              </span>
            </div>

            <button
              onClick={() => setActiveTab('timeline')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                color: 'var(--cnas-blue)',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              <span>View Timeline</span>
              <ArrowRight size={14} />
            </button>
          </div>

          {/* Minimal Stream List with Connecting Line */}
          <div style={{ position: 'relative', paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div
              style={{
                position: 'absolute',
                left: '6px',
                top: '6px',
                bottom: '8px',
                width: '1px',
                backgroundColor: 'var(--cnas-border)',
              }}
            />

            {timelineEvents.slice(0, 3).map((event) => (
              <div
                key={event.id}
                style={{
                  position: 'relative',
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '1rem',
                }}
              >
                {/* Node dot */}
                <span
                  style={{
                    position: 'absolute',
                    left: '-1.5rem',
                    top: '4px',
                    width: '9px',
                    height: '9px',
                    borderRadius: '50%',
                    backgroundColor:
                      event.severity === 'CRITICAL'
                        ? 'var(--cnas-risk)'
                        : event.severity === 'WARN'
                        ? 'var(--cnas-blue)'
                        : 'var(--cnas-navy)',
                    boxShadow: '0 0 0 3px #ffffff',
                  }}
                />

                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', maxWidth: '580px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--cnas-text-primary)' }}>
                      {event.title}
                    </span>
                    <Badge
                      variant={
                        event.severity === 'CRITICAL'
                          ? 'risk'
                          : event.severity === 'WARN'
                          ? 'neutral'
                          : 'navy'
                      }
                      size="sm"
                    >
                      {event.type}
                    </Badge>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--cnas-text-muted)', lineHeight: 1.4 }}>
                    {event.description}
                  </p>
                </div>

                <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <div style={{ fontFamily: 'var(--font-code)', fontSize: '11px', fontWeight: 600, color: 'var(--cnas-navy)' }}>
                    {event.displayTime.split('·')[0].trim()}
                  </div>
                  <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>
                    {event.displayTime.split('·')[1]?.trim() || 'Today'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Immediate Case Context & Evidence Fast-Access (4 Columns) */}
        <div
          style={{
            gridColumn: 'span 4',
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.25rem',
            boxShadow: 'var(--shadow-xs)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <FileText size={16} color="var(--cnas-navy)" />
              <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                Key Evidence Files
              </h2>
            </div>
            <button
              onClick={() => setActiveTab('evidence')}
              style={{ fontSize: '12px', color: 'var(--cnas-blue)', fontWeight: 600 }}
            >
              All ({evidenceDocs.length})
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {evidenceDocs.slice(0, 3).map((doc) => (
              <div
                key={doc.id}
                onClick={() => viewDocumentDossier(doc.id)}
                style={{
                  padding: '0.65rem',
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: 'var(--cnas-surface-subtle)',
                  border: '1px solid var(--cnas-border)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--cnas-surface)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--cnas-navy)',
                    }}
                  >
                    <FileText size={14} />
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-navy)' }}>
                      {doc.filename}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>
                      SHA256: {doc.sha256.substring(0, 8)}...
                    </div>
                  </div>
                </div>
                <span style={{ fontSize: '10px', fontFamily: 'var(--font-code)', color: 'var(--cnas-text-muted)' }}>
                  {doc.fileSize}
                </span>
              </div>
            ))}
          </div>

          {/* Quick Investigator Note */}
          <div
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--cnas-surface-subtle)',
              border: '1px solid var(--cnas-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)' }}>
                Investigator Note
              </span>
              <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>12m ago</span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--cnas-text-primary)', fontStyle: 'italic', lineHeight: 1.4 }}>
              "Coordinating with ED Zonal office for parallel PMLA asset freezing before 20:00 IST close."
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
