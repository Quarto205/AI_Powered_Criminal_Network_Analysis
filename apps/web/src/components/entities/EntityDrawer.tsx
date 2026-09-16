import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCase } from '../../context/CaseContext';
import { Badge } from '../ui/Badge';
import {
  X,
  Pin,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Phone,
  Sparkles,
  ChevronRight,
  Focus,
  Share2,
} from 'lucide-react';

export const EntityDrawer: React.FC = () => {
  const { selectedEntity, isDrawerOpen, setIsDrawerOpen, viewDocumentDossier, setActiveTab } = useCase();
  const [activeTab, setActiveTabLocal] = useState<'overview' | 'connections' | 'evidence' | 'activity' | 'ai'>('overview');

  if (!isDrawerOpen || !selectedEntity) return null;

  return (
    <AnimatePresence>
      <motion.aside
        initial={{ x: '100%', opacity: 0.5 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: '100%', opacity: 0 }}
        transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
        style={{
          position: 'fixed',
          top: '64px',
          right: 0,
          bottom: 0,
          width: '420px',
          backgroundColor: 'var(--cnas-surface)',
          borderLeft: '1px solid var(--cnas-border)',
          boxShadow: 'var(--shadow-drawer)',
          zIndex: 45,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Top Banner & Subject Identity */}
        <div
          style={{
            padding: '1.25rem',
            background: 'linear-gradient(180deg, var(--cnas-surface-subtle) 0%, var(--cnas-surface) 100%)',
            borderBottom: '1px solid var(--cnas-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ position: 'relative' }}>
                <img
                  src={selectedEntity.photoUrl || 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80'}
                  alt={selectedEntity.name}
                  style={{
                    width: '52px',
                    height: '52px',
                    borderRadius: 'var(--radius-lg)',
                    objectFit: 'cover',
                    backgroundColor: 'var(--cnas-surface-container)',
                    boxShadow: 'var(--shadow-xs)',
                  }}
                />
                <span
                  style={{
                    position: 'absolute',
                    bottom: '-2px',
                    right: '-2px',
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--cnas-risk)',
                    border: '2px solid #ffffff',
                  }}
                  title="High Threat Level"
                />
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {selectedEntity.name}
                  </h2>
                  {selectedEntity.biometricVerified && (
                    <span title="Verified Biometrics" style={{ display: 'inline-flex', alignItems: 'center' }}>
                      <CheckCircle2 size={16} color="var(--cnas-blue)" />
                    </span>
                  )}
                </div>
                <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                  {selectedEntity.primaryRole}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <button
                style={{
                  padding: '6px',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--cnas-text-muted)',
                }}
                title="Pin Dossier"
              >
                <Pin size={16} />
              </button>
              <button
                onClick={() => setIsDrawerOpen(false)}
                style={{
                  padding: '6px',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--cnas-text-muted)',
                }}
                title="Close Drawer"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Status Chip & Centrality */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.85rem' }}>
            <Badge variant="risk" pulse>
              Active Target · Under Surveillance
            </Badge>
            <span
              style={{
                fontFamily: 'var(--font-code)',
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--cnas-navy)',
                backgroundColor: 'var(--cnas-surface-container)',
                padding: '2px 6px',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              DEGREE: {selectedEntity.degreeCentrality}
            </span>
          </div>
        </div>

        {/* Tab Navigation Strip */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'var(--cnas-surface-subtle)',
            borderBottom: '1px solid var(--cnas-border)',
            padding: '0 0.5rem',
            gap: '2px',
          }}
        >
          {(['overview', 'connections', 'evidence', 'activity', 'ai'] as const).map((tab) => {
            const isActive = activeTab === tab;
            const labels = {
              overview: 'Overview',
              connections: `Connections (${selectedEntity.connectionsCount})`,
              evidence: `Evidence (${selectedEntity.evidenceCount})`,
              activity: 'Activity',
              ai: 'AI Leads',
            };
            return (
              <button
                key={tab}
                onClick={() => setActiveTabLocal(tab)}
                style={{
                  padding: '0.65rem 0.65rem',
                  fontSize: '11px',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? 'var(--cnas-navy)' : 'var(--cnas-text-muted)',
                  borderBottom: isActive ? '2px solid var(--cnas-navy)' : '2px solid transparent',
                  transition: 'all var(--transition-fast)',
                }}
              >
                {labels[tab]}
              </button>
            );
          })}
        </div>

        {/* Tab Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {activeTab === 'overview' && (
            <>
              {/* Aliases */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cnas-text-muted)' }}>
                  Known Aliases
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {selectedEntity.aliases.map((alias, i) => (
                    <span
                      key={i}
                      style={{
                        padding: '0.25rem 0.5rem',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--cnas-surface-subtle)',
                        border: '1px solid var(--cnas-border)',
                        fontSize: '12px',
                        color: 'var(--cnas-text-primary)',
                      }}
                    >
                      {alias}
                    </span>
                  ))}
                </div>
              </div>

              {/* Identifiers Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '0.65rem',
                  backgroundColor: 'var(--cnas-surface-subtle)',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--cnas-border)',
                }}
              >
                <div>
                  <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--cnas-text-muted)', textTransform: 'uppercase' }}>
                    PAN IDENTIFIER
                  </div>
                  <div style={{ fontFamily: 'var(--font-code)', fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {selectedEntity.identifiers.pan || 'N/A'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--cnas-text-muted)', textTransform: 'uppercase' }}>
                    PASSPORT NO.
                  </div>
                  <div style={{ fontFamily: 'var(--font-code)', fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {selectedEntity.identifiers.passport || 'N/A'}
                  </div>
                </div>

                <div style={{ gridColumn: 'span 2', paddingTop: '4px', borderTop: '1px solid var(--cnas-border)' }}>
                  <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--cnas-text-muted)', textTransform: 'uppercase' }}>
                    PRIMARY MSISDN
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
                    <span style={{ fontFamily: 'var(--font-code)', fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                      {selectedEntity.identifiers.msisdn || 'N/A'}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--cnas-verified)', fontWeight: 600 }}>
                      {selectedEntity.identifiers.msisdnStatus || 'Active'}
                    </span>
                  </div>
                </div>
              </div>

              {/* AI Predictive Association Box - Epistemic Purple Dashed */}
              {selectedEntity.aiClusterInsight && (
                <div
                  style={{
                    backgroundColor: 'var(--cnas-ai-subtle)',
                    border: '1px dashed var(--cnas-ai-border)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '0.85rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--cnas-ai-text)', fontSize: '12px', fontWeight: 700 }}>
                      <Sparkles size={14} />
                      <span>AI Latent Cluster Match ({selectedEntity.aiClusterInsight.matchScore}%)</span>
                    </div>
                    <span
                      style={{
                        fontFamily: 'var(--font-code)',
                        fontSize: '10px',
                        fontWeight: 700,
                        backgroundColor: '#ffffff',
                        color: 'var(--cnas-ai-text)',
                        padding: '1px 5px',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--cnas-ai-border)',
                      }}
                    >
                      {selectedEntity.aiClusterInsight.code}
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--cnas-text-primary)', lineHeight: 1.45 }}>
                    {selectedEntity.aiClusterInsight.explanation}
                  </p>
                </div>
              )}

              {/* Direct Graph Connections */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cnas-text-muted)' }}>
                    Direct Connections ({selectedEntity.connectionsCount})
                  </span>
                  <button
                    onClick={() => setActiveTab('network')}
                    style={{ fontSize: '11px', color: 'var(--cnas-blue)', fontWeight: 600 }}
                  >
                    Graph View
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                  <div
                    style={{
                      padding: '0.65rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--cnas-surface-subtle)',
                      border: '1px solid var(--cnas-border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ width: '28px', height: '28px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--cnas-surface-high)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '11px', color: 'var(--cnas-navy)' }}>
                        AZ
                      </span>
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-navy)' }}>
                          Al-Zubair Exports FZE
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>
                          Direct Signatory · 12 Invoices
                        </div>
                      </div>
                    </div>
                    <ChevronRight size={14} color="var(--cnas-text-muted)" />
                  </div>

                  <div
                    style={{
                      padding: '0.65rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--cnas-surface-subtle)',
                      border: '1px solid var(--cnas-border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ width: '28px', height: '28px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--cnas-review-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '11px', color: 'var(--cnas-review)' }}>
                        AC
                      </span>
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-navy)' }}>
                          ICICI Acct ••••4921
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>
                          Sole Signatory · Fan-out source ₹4.5 Cr
                        </div>
                      </div>
                    </div>
                    <ChevronRight size={14} color="var(--cnas-text-muted)" />
                  </div>
                </div>
              </div>

              {/* Linked Court Evidence */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cnas-text-muted)' }}>
                  Linked Court Evidence
                </span>
                <div
                  onClick={() => viewDocumentDossier('doc-2')}
                  style={{
                    padding: '0.65rem',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor: 'var(--cnas-surface-subtle)',
                    border: '1px solid var(--cnas-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <FileText size={16} color="var(--cnas-navy)" />
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-navy)' }}>
                        Customs_BillOfLading_JAFZA9102.pdf
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--cnas-verified)', fontWeight: 600 }}>
                        Section 65B Certified · SHA-256 Valid
                      </div>
                    </div>
                  </div>
                  <ChevronRight size={14} color="var(--cnas-text-muted)" />
                </div>
              </div>
            </>
          )}

          {activeTab === 'connections' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <span style={{ fontSize: '12px', color: 'var(--cnas-text-muted)' }}>
                Showing 5 direct linkages mapped in the active investigation.
              </span>
              {/* Connection items */}
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--cnas-border)', backgroundColor: 'var(--cnas-surface-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--cnas-navy)' }}>Al-Zubair Exports FZE</div>
                <div style={{ fontSize: '11px', color: 'var(--cnas-text-secondary)', marginTop: '2px' }}>₹1.8 Cr Hawala Remittance · 12 commercial manifests</div>
                <Badge variant="verified" size="sm" style={{ marginTop: '6px' }}>Source Verified</Badge>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--cnas-border)', backgroundColor: 'var(--cnas-surface-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--cnas-navy)' }}>ICICI Acct ••••4921</div>
                <div style={{ fontSize: '11px', color: 'var(--cnas-text-secondary)', marginTop: '2px' }}>Sole signatory token holder · ₹4.5 Cr disbursement</div>
                <Badge variant="verified" size="sm" style={{ marginTop: '6px' }}>Source Verified</Badge>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px dashed var(--cnas-ai-border)', backgroundColor: 'var(--cnas-ai-subtle)' }}>
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--cnas-ai-text)' }}>Al-Madina FZE (AI Inferred)</div>
                <div style={{ fontSize: '11px', color: 'var(--cnas-text-secondary)', marginTop: '2px' }}>GNN Latent cluster link prediction (94% confidence)</div>
                <Badge variant="ai-inferred" size="sm" style={{ marginTop: '6px' }}>AI Predicted</Badge>
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div
                onClick={() => viewDocumentDossier('doc-1')}
                style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--cnas-border)', backgroundColor: 'var(--cnas-surface-subtle)', cursor: 'pointer' }}
              >
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--cnas-navy)' }}>ICICI Bank Statement May 2026</div>
                <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>SHA-256: 4b2a99...91f</div>
                <Badge variant="verified" size="sm" style={{ marginTop: '6px' }}>Sec 65B Certified</Badge>
              </div>
              <div
                onClick={() => viewDocumentDossier('doc-2')}
                style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--cnas-border)', backgroundColor: 'var(--cnas-surface-subtle)', cursor: 'pointer' }}
              >
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--cnas-navy)' }}>UAE Cargo Bill of Lading JAFZA-9102</div>
                <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>SHA-256: 7c891e...102c</div>
                <Badge variant="verified" size="sm" style={{ marginTop: '6px' }}>Customs Inward Manifest</Badge>
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ borderLeft: '2px solid var(--cnas-blue)', paddingLeft: '0.75rem' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--cnas-navy)' }}>VoIP Encrypted Session Logged</div>
                <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>16:15 IST Today · 04m 18s duration to UAE Gateway</div>
              </div>
              <div style={{ borderLeft: '2px solid var(--cnas-risk)', paddingLeft: '0.75rem' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--cnas-navy)' }}>Cash Dispersal Alert Dispatched</div>
                <div style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>18:30 IST Today · ₹45,00,000 fan-out tranche</div>
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-lg)', backgroundColor: 'var(--cnas-ai-subtle)', border: '1px dashed var(--cnas-ai-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--cnas-ai-text)', fontSize: '12px', fontWeight: 700 }}>
                  <Sparkles size={14} />
                  <span>Offshore Smurfing Network Corroboration</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--cnas-text-primary)', marginTop: '4px', lineHeight: 1.4 }}>
                  Multi-hop graph neural network identifies a 94% probabilistic tie between Tariq M. and unregistered Dubai corporate front Al-Madina FZE.
                </p>
                <div style={{ marginTop: '8px', display: 'flex', gap: '4px' }}>
                  <button
                    onClick={() => setActiveTab('analysis')}
                    style={{ fontSize: '10px', padding: '3px 8px', borderRadius: 'var(--radius-xs)', backgroundColor: 'var(--cnas-ai-primary)', color: '#ffffff', fontWeight: 600 }}
                  >
                    Inspect in Analysis
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons Footer */}
        <div
          style={{
            padding: '0.85rem 1.25rem',
            borderTop: '1px solid var(--cnas-border)',
            backgroundColor: 'var(--cnas-surface-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <button
            onClick={() => setActiveTab('network')}
            style={{
              flex: 1,
              height: '36px',
              backgroundColor: 'var(--cnas-navy)',
              color: '#ffffff',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.4rem',
              boxShadow: 'var(--shadow-xs)',
            }}
          >
            <Focus size={14} />
            <span>Focus Ego-Network</span>
          </button>

          <button
            style={{
              height: '36px',
              padding: '0 0.85rem',
              backgroundColor: 'var(--cnas-surface)',
              border: '1px solid var(--cnas-border)',
              color: 'var(--cnas-navy)',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <Share2 size={14} />
            <span>Export Brief</span>
          </button>
        </div>
      </motion.aside>
    </AnimatePresence>
  );
};
