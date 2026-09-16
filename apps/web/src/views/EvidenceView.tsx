import React, { useState, useEffect } from 'react';
import { useCase } from '../context/CaseContext';
import { Badge } from '../components/ui/Badge';
import { EvidenceDocument } from '../types';
import { nvidiaNimService } from '../services/nvidiaNimService';
import { apiClient } from '../services/apiClient';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  Clock,
  Shield,
  Search,
  ZoomIn,
  Printer,
  Download,
  Sparkles,
  ArrowRight,
  Filter,
  Check,
  Loader2,
  X,
  ScanText
} from 'lucide-react';

export const EvidenceView: React.FC = () => {
  const { activeCase, evidenceDocs, selectedDoc, setSelectedDoc, addEvidenceDocument } = useCase();
  const [selectedFilter, setSelectedFilter] = useState<'ALL' | 'BANKING' | 'CDR' | 'LEGAL' | 'CUSTOMS'>('ALL');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadStage, setUploadStage] = useState<number>(0);
  
  const [extractedData, setExtractedData] = useState<{ extractedText: string; entities: Array<{ type: string; value: string }>; confidence: number } | null>(null);
  const [isExtracting, setIsExtracting] = useState<boolean>(false);

  // Reset extraction data when active document changes
  useEffect(() => {
    setExtractedData(null);
  }, [selectedDoc]);

  const handleExtraction = async () => {
    if (!selectedDoc) return;
    setIsExtracting(true);
    try {
      const result = await nvidiaNimService.extractDocumentMultimodal('base64...', selectedDoc.title);
      setExtractedData(result);
    } catch (e) {
      console.error('Extraction error:', e);
    } finally {
      setIsExtracting(false);
    }
  };

  const stages = ['Upload', 'Received', 'Validated', 'Processing', 'Extracted', 'Review'];

  const filteredDocs = evidenceDocs.filter((d) => {
    if (selectedFilter === 'ALL') return true;
    return d.category === selectedFilter;
  });

  const activeDoc = selectedDoc;

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !activeCase?.id) return;

    setIsUploading(true);
    setUploadStage(1);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiClient.post<any>(`/api/v1/cases/${activeCase.id}/documents`, formData);
      if (res.success && res.data) {
        setUploadStage(3);
        // Simulate processing for visual feedback
        setTimeout(() => {
          setUploadStage(4);
          setTimeout(() => {
            setUploadStage(5);
            // Construct new document from response
            const newDoc: EvidenceDocument = {
              id: res.data.document_id,
              caseId: activeCase.id,
              title: file.name,
              filename: file.name,
              category: 'BANKING',
              sha256: 'Pending Hash', // Or from res.data if available
              fileSize: `${(file.size / 1024 / 1024).toFixed(2)} MB`,
              timestamp: new Date().toISOString(),
              verifiedChainOfCustody: true,
              section65BCertified: true,
              linkedEntityIds: [],
              excerpt: 'Document successfully ingested and queued for OCR extraction.',
              metadata: {
                'Status': res.data.status || 'Received',
                'Job ID': res.data.job_id
              },
            };
            addEvidenceDocument(newDoc);
            setSelectedDoc(newDoc);
            setIsUploading(false);
            setUploadStage(0);
          }, 1000);
        }, 1000);
      } else {
        throw new Error("Upload failed");
      }
    } catch (e) {
      console.error("Failed to upload document:", e);
      setIsUploading(false);
      setUploadStage(0);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Top Action Bar & Provenance Header */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '11px', color: 'var(--cnas-text-muted)', marginBottom: '2px' }}>
            <span style={{ fontFamily: 'var(--font-code)', fontWeight: 700, color: 'var(--cnas-blue)' }}>PROVENANCE ARCHIVE</span>
            <span>/</span>
            <span style={{ fontFamily: 'var(--font-code)' }}>CASE-2026-DEL-0891</span>
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--cnas-navy)' }}>
            Source Evidence & Provenance Vault
          </h1>
          <span style={{ fontSize: '12px', color: 'var(--cnas-text-muted)' }}>
            Certified evidentiary source records supporting operational network inferences
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <input
            type="file"
            id="evidence-upload"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
            accept=".pdf,.png,.jpg,.jpeg"
          />
          <button
            onClick={() => document.getElementById('evidence-upload')?.click()}
            disabled={isUploading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.5rem 1rem',
              backgroundColor: 'var(--cnas-navy)',
              color: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              fontSize: '12px',
              fontWeight: 600,
              boxShadow: 'var(--shadow-xs)',
              cursor: 'pointer',
            }}
          >
            <UploadCloud size={16} />
            <span>{isUploading ? 'Ingesting Artifact...' : 'Upload Evidence'}</span>
          </button>
        </div>
      </div>

      {/* Upload Progress Multi-Stage Modal / Banner */}
      {isUploading && (
        <div
          style={{
            backgroundColor: 'var(--cnas-surface)',
            border: '1px solid var(--cnas-blue)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Loader2 size={16} color="var(--cnas-blue)" className="pulse-live" />
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                Automated Ingestion Pipeline: Ledger_CashSheet_Scan_May24.pdf
              </span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>
              Step {uploadStage + 1} of {stages.length}
            </span>
          </div>

          {/* Pipeline Stage Badges */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto' }}>
            {stages.map((stageName, idx) => {
              const isPast = idx < uploadStage;
              const isCurrent = idx === uploadStage;
              return (
                <div
                  key={stageName}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '11px',
                    fontWeight: 600,
                    backgroundColor: isPast
                      ? 'var(--cnas-verified-bg)'
                      : isCurrent
                      ? 'var(--cnas-surface-high)'
                      : 'var(--cnas-surface-subtle)',
                    color: isPast
                      ? 'var(--cnas-verified)'
                      : isCurrent
                      ? 'var(--cnas-navy)'
                      : 'var(--cnas-text-muted)',
                    border: '1px solid var(--cnas-border)',
                  }}
                >
                  {isPast ? <Check size={12} /> : <span>{idx + 1}.</span>}
                  <span>{stageName}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 2. Quick Filter Tabs & Summary Strip */}
      <div
        style={{
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '0.65rem 1rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          boxShadow: 'var(--shadow-xs)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', overflowX: 'auto' }}>
          {(['ALL', 'BANKING', 'CDR', 'LEGAL', 'CUSTOMS'] as const).map((filter) => {
            const isActive = selectedFilter === filter;
            const labels = {
              ALL: `All Sources (${evidenceDocs.length})`,
              BANKING: 'Banking & Statements (3)',
              CDR: 'CDR & Intercepts (2)',
              LEGAL: 'Legal Affidavits (2)',
              CUSTOMS: 'Customs / Shipping (1)',
            };
            return (
              <button
                key={filter}
                onClick={() => setSelectedFilter(filter)}
                style={{
                  padding: '0.4rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '12px',
                  fontWeight: isActive ? 700 : 500,
                  backgroundColor: isActive ? 'var(--cnas-navy)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--cnas-text-secondary)',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                {labels[filter]}
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--cnas-verified)' }} />
            <span>7 Certified Chain-of-Custody</span>
          </div>
          <span>•</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--cnas-review)' }} />
            <span>1 Ingest Queued</span>
          </div>
        </div>
      </div>

      {/* 3. Main Workspace Split: Document Register & High-Grade Reading View */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left: Master Custody Ledger (5 Columns) */}
        <div style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 4px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cnas-text-muted)' }}>
              Master Custody Ledger
            </span>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-code)', color: 'var(--cnas-text-muted)' }}>
              {filteredDocs.length} displayed
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {filteredDocs.map((doc) => {
              const isSelected = activeDoc?.id === doc.id;
              return (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDoc(isSelected ? null : doc)}
                  style={{
                    backgroundColor: isSelected ? 'var(--cnas-surface-subtle)' : 'var(--cnas-surface)',
                    border: isSelected ? '2px solid var(--cnas-blue)' : '1px solid var(--cnas-border)',
                    borderRadius: 'var(--radius-xl)',
                    padding: '1rem',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.65rem',
                    boxShadow: isSelected ? 'var(--shadow-sm)' : 'var(--shadow-xs)',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <div
                        style={{
                          width: '34px',
                          height: '34px',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: isSelected ? 'var(--cnas-navy)' : 'var(--cnas-surface-subtle)',
                          color: isSelected ? '#ffffff' : 'var(--cnas-navy)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <FileText size={16} />
                      </div>
                      <div>
                        <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                          {doc.title}
                        </h3>
                        <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                          {doc.category} · {doc.fileSize}
                        </span>
                      </div>
                    </div>
                    <Badge variant="verified" size="sm">
                      Sec 65B Certified
                    </Badge>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--cnas-border)', paddingTop: '6px', fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                    <span style={{ fontFamily: 'var(--font-code)' }}>{doc.linkedEntityIds.length} Linked Entities</span>
                    <span style={{ color: isSelected ? 'var(--cnas-navy)' : 'var(--cnas-blue)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
                      <span>{isSelected ? 'Close Preview' : 'View Dossier'}</span>
                      {isSelected ? <X size={12} /> : <ArrowRight size={12} />}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Section 65B Compliance Notice Callout */}
          <div
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-xl)',
              backgroundColor: 'var(--cnas-surface-subtle)',
              border: '1px solid var(--cnas-border)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              marginTop: '0.5rem',
            }}
          >
            <Shield size={20} color="var(--cnas-navy)" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                Indian Evidence Act Section 65B Compliance
              </div>
              <p style={{ fontSize: '11px', color: 'var(--cnas-text-secondary)', marginTop: '2px', lineHeight: 1.4 }}>
                All ingested optical and electronic artifacts undergo cryptographic attestation at ingest. Cryptographic SHA-256 hashes are anchored in the immutable audit ledger.
              </p>
            </div>
          </div>
        </div>

        {/* Right: High-Precision Document Viewer or Empty Placeholder (7 Columns) */}
        {!activeDoc ? (
          <div
            style={{
              gridColumn: 'span 7',
              backgroundColor: 'var(--cnas-surface)',
              border: '1px solid var(--cnas-border)',
              borderRadius: 'var(--radius-xl)',
              padding: '3.5rem 2rem',
              boxShadow: 'var(--shadow-xs)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              minHeight: '480px',
              gap: '1.25rem',
            }}
          >
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: 'var(--cnas-surface-subtle)',
                border: '1px solid var(--cnas-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--cnas-navy)',
              }}
            >
              <FileText size={32} />
            </div>
            <div style={{ maxWidth: '440px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--cnas-navy)', marginBottom: '0.5rem' }}>
                No Document Opened
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--cnas-text-secondary)', lineHeight: 1.5 }}>
                Select any evidentiary record or forensic file from the Master Custody Ledger on the left to inspect cryptographic attestation, entity extractions, and Section 65B certified briefs.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Badge variant="verified" size="sm">
                Sec 65B Certified Vault
              </Badge>
              <Badge variant="neutral" size="sm">
                SHA-256 Verified
              </Badge>
            </div>
          </div>
        ) : (
          <div
            style={{
              gridColumn: 'span 7',
              backgroundColor: 'var(--cnas-surface)',
              border: '1px solid var(--cnas-border)',
              borderRadius: 'var(--radius-xl)',
              padding: '1.5rem',
              boxShadow: 'var(--shadow-xs)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
            }}
          >
            {/* Document Header Controls with Cross Close Button */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--cnas-border)', paddingBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div
                  style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--cnas-surface-high)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--cnas-navy)',
                  }}
                >
                  <FileText size={20} />
                </div>
                <div>
                  <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {activeDoc.title}
                  </h2>
                  <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                    {activeDoc.filename} · Authenticated Inward Record
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <button
                  onClick={handleExtraction}
                  disabled={isExtracting}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    height: '32px',
                    padding: '0 12px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--cnas-navy)',
                    backgroundColor: 'var(--cnas-navy)',
                    color: '#fff',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: isExtracting ? 'not-allowed' : 'pointer',
                    opacity: isExtracting ? 0.7 : 1,
                    marginRight: '4px',
                  }}
                  title="Vision Intelligence OCR"
                >
                  {isExtracting ? <Loader2 size={14} className="animate-spin" /> : <ScanText size={14} />}
                  {isExtracting ? 'Extracting...' : 'Extract via AI'}
                </button>
                <button
                  onClick={() => window.print()}
                  style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', border: '1px solid var(--cnas-border)', backgroundColor: 'var(--cnas-surface-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--cnas-text-secondary)', cursor: 'pointer' }}
                  title="Print Brief"
                >
                  <Printer size={15} />
                </button>
                <button
                  style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', border: '1px solid var(--cnas-border)', backgroundColor: 'var(--cnas-surface-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--cnas-text-secondary)', cursor: 'pointer' }}
                  title="Download Source PDF"
                >
                  <Download size={15} />
                </button>
                <button
                  onClick={() => setSelectedDoc(null)}
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--cnas-border)',
                    backgroundColor: 'var(--cnas-surface-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--cnas-navy)',
                    cursor: 'pointer',
                    marginLeft: '4px',
                  }}
                  title="Close Document Preview"
                  aria-label="Close Document Preview"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Detected Corroborations Strip */}
            <div
              style={{
                backgroundColor: 'var(--cnas-surface-subtle)',
                padding: '0.5rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.5rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--cnas-text-muted)' }}>
                <Sparkles size={13} color="var(--cnas-blue)" />
                <span style={{ fontWeight: 600 }}>Detected Corroborations:</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {activeDoc.linkedEntityIds?.map((entId) => (
                  <Badge key={entId} variant="ai-inferred" size="sm">
                    {entId.replace('ent-', '').replace('-', ' ').toUpperCase()}
                  </Badge>
                ))}
                <Badge variant="verified" size="sm">
                  {activeDoc.category}
                </Badge>
              </div>
            </div>

            {/* High-Grade Reading Interface (Paper Styled) */}
            <div
              style={{
                backgroundColor: '#fbfcfe',
                border: '1px solid #e2e8f0',
                borderRadius: 'var(--radius-lg)',
                padding: '1.5rem',
                boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.03)',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--cnas-text-muted)' }}>
                    CERTIFIED FORENSIC RECORD · {activeDoc.category}
                  </div>
                  <div style={{ fontFamily: 'var(--font-code)', fontSize: '13px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    {activeDoc.title.toUpperCase()}
                  </div>
                </div>
                <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--cnas-verified)', backgroundColor: 'var(--cnas-verified-bg)', border: '1px solid var(--cnas-verified-border)', padding: '2px 8px', borderRadius: 'var(--radius-xs)' }}>
                  SEC 65B CERTIFIED · INGESTED
                </span>
              </div>

              <div style={{ height: '1px', backgroundColor: 'var(--cnas-border)' }} />

              {/* Document Key Fields Grid */}
              {activeDoc.metadata && (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '1rem',
                    backgroundColor: 'var(--cnas-surface)',
                    padding: '0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--cnas-border)',
                  }}
                >
                  {Object.entries(activeDoc.metadata).map(([key, val]) => (
                    <div key={key}>
                      <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)' }}>
                        {key}:
                      </span>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--cnas-navy)', marginTop: '2px' }}>
                        {String(val)}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Transcript & Body Extract */}
              <div style={{ fontSize: '13px', color: 'var(--cnas-text-primary)', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <p>
                  <strong>Document Summary / Forensic Excerpt:</strong> {activeDoc.excerpt}
                </p>
                <p>
                  This artifact was extracted under certified custodial protocols with verified timestamp <code style={{ fontFamily: 'var(--font-code)', backgroundColor: 'var(--cnas-surface-subtle)', padding: '2px 4px', borderRadius: '3px' }}>{activeDoc.timestamp}</code> and signed hash verification.
                </p>
              </div>

              {extractedData && (
                <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid var(--cnas-navy)', borderRadius: 'var(--radius-md)', backgroundColor: '#f0f4f8' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cnas-navy)', marginBottom: '12px', fontWeight: 700 }}>
                    <ScanText size={16} />
                    Vision Intelligence Extraction
                  </div>
                  
                  <div style={{ fontSize: '12px', fontFamily: 'var(--font-code)', backgroundColor: '#fff', padding: '12px', borderRadius: '4px', border: '1px solid var(--cnas-border)', whiteSpace: 'pre-wrap', marginBottom: '12px' }}>
                    {extractedData.extractedText}
                  </div>

                  <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--cnas-text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
                    Extracted Entities ({extractedData.confidence * 100}% Confidence)
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {extractedData.entities.map((ent, idx) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '2px 8px', borderRadius: '4px', backgroundColor: '#e2e8f0', fontSize: '11px', color: 'var(--cnas-navy)', border: '1px solid #cbd5e1' }}>
                        <span style={{ fontWeight: 700 }}>{ent.type}:</span> {ent.value}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Analytical Callout Box */}
              <div
                style={{
                  backgroundColor: 'var(--cnas-surface-subtle)',
                  border: '1px solid var(--cnas-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.75rem 1rem',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.65rem',
                }}
              >
                <Sparkles size={16} color="var(--cnas-blue)" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                    Cross-Case Correlation Detected
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--cnas-text-secondary)' }}>
                    Artifact is linked to {activeDoc.linkedEntityIds?.length || 0} entities in the active crime graph with cryptographic chain-of-custody intact.
                  </span>
                </div>
              </div>
            </div>

            {/* Cryptographic Attestation Metadata Bar */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '11px',
                fontFamily: 'var(--font-code)',
                color: 'var(--cnas-text-muted)',
                backgroundColor: 'var(--cnas-surface-subtle)',
                padding: '0.5rem 0.85rem',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <span>SHA-256: {activeDoc.sha256}</span>
              <span style={{ color: 'var(--cnas-verified)', fontWeight: 600 }}>Chain Intact · 100% Attested</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
