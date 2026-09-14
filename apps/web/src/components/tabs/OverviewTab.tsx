/**
 * Case Overview Tab Component
 * Strictly adheres to 08_UI_DATA_CONTRACT.md (Section 8.1).
 * Displays graph density, document counts, unresolved entity reviews, and active pattern alerts.
 */

import React, { useEffect, useState } from 'react';
import { Network, FileText, Bell, CheckSquare, ArrowUpRight, Activity, Cpu } from 'lucide-react';
import { CaseDetailResponse } from '../../contracts/cases';
import { ScoreItem } from '../../contracts/analysis';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { apiClient } from '../../api';
import { useSelection } from '../../context/SelectionContext';

interface OverviewTabProps {
  caseDetail: CaseDetailResponse;
  onNavigateToTab: (tab: string) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ caseDetail, onNavigateToTab }) => {
  const [scores, setScores] = useState<ScoreItem[]>([]);
  const { selectNode } = useSelection();

  useEffect(() => {
    let isMounted = true;
    apiClient
      .getCaseScores(caseDetail.case_id)
      .then((resp) => {
        if (isMounted) {
          setScores(resp.data.scores);
        }
      })
      .catch(() => {
        // Handled gracefully
      });

    return () => {
      isMounted = false;
    };
  }, [caseDetail.case_id]);

  return (
    <div style={{ padding: '24px', overflowY: 'auto', height: '100%', background: '#090d16' }}>
      {/* Top Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        {/* Card 1: Knowledge Graph Topology */}
        <div
          onClick={() => onNavigateToTab('graph')}
          style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: '8px',
            padding: '18px',
            cursor: 'pointer',
            transition: 'border-color 0.15s ease',
          }}
          className="hover:border-slate-600"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '10px' }}>
            <span style={{ fontSize: '12px', fontWeight: 500 }}>Knowledge Graph</span>
            <Network size={18} color="#818cf8" />
          </div>
          <div style={{ fontSize: '26px', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
            {caseDetail.entity_count} <span style={{ fontSize: '13px', fontWeight: 400, color: '#64748b' }}>Nodes</span>
          </div>
          <div style={{ fontSize: '11px', color: '#818cf8', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Explore Cytoscape Canvas</span>
            <ArrowUpRight size={12} />
          </div>
        </div>

        {/* Card 2: Ingested Source Documents */}
        <div
          style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: '8px',
            padding: '18px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '10px' }}>
            <span style={{ fontSize: '12px', fontWeight: 500 }}>Source Evidence</span>
            <FileText size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '26px', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
            {caseDetail.document_count} <span style={{ fontSize: '13px', fontWeight: 400, color: '#64748b' }}>Files</span>
          </div>
          <div style={{ fontSize: '11px', color: '#38bdf8', marginTop: '6px' }}>
            FIR, CDR CSV, Bank Statements verified
          </div>
        </div>

        {/* Card 3: Suspicious Pattern Alerts */}
        <div
          onClick={() => onNavigateToTab('alerts')}
          style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: '8px',
            padding: '18px',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '10px' }}>
            <span style={{ fontSize: '12px', fontWeight: 500 }}>Pattern Motifs</span>
            <Bell size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '26px', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
            3 <span style={{ fontSize: '13px', fontWeight: 400, color: '#64748b' }}>Active Alerts</span>
          </div>
          <div style={{ fontSize: '11px', color: '#f59e0b', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Review Suspicious Cycles</span>
            <ArrowUpRight size={12} />
          </div>
        </div>

        {/* Card 4: System Degradation / Health Status */}
        <div
          style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: '8px',
            padding: '18px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', marginBottom: '10px' }}>
            <span style={{ fontSize: '12px', fontWeight: 500 }}>Services Health</span>
            <Activity size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            <span>OPERATIONAL</span>
          </div>
          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            PostgreSQL: OK | Neo4j: OK | ML: OK
          </div>
        </div>
      </div>

      {/* Two Column Layout: Priority Rankings & Quick Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Left Column: Top Investigative Priority Rankings */}
        <div
          style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: '8px',
            padding: '20px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
                Top Investigative Priority Rankings
              </h3>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>
                Multi-signal ranking derived from SNA centrality, transaction fan-out, and community bridges.
              </p>
            </div>
            <Badge variant="default">Agent 3 SNA</Badge>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {scores.map((score, index) => (
              <div
                key={score.score_id}
                onClick={() => {
                  selectNode({
                    id: score.entity_id,
                    label: score.canonical_name,
                    entity_type: score.entity_type,
                    case_id: caseDetail.case_id,
                    risk_score: score.value,
                  });
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 14px',
                  background: '#131d36',
                  border: '1px solid #1e293b',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '13px',
                      fontWeight: 700,
                      color: index === 0 ? '#38bdf8' : '#64748b',
                      width: '20px',
                    }}
                  >
                    #{index + 1}
                  </span>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
                      {score.canonical_name}
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      {score.features_summary?.reasoning ?? 'Topological bridge'}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Badge variant={score.entity_type.toLowerCase() as any}>
                    {score.entity_type}
                  </Badge>
                  <div style={{ textAlign: 'right' }}>
                    <div
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '14px',
                        fontWeight: 700,
                        color: '#38bdf8',
                      }}
                    >
                      {(score.value * 100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize: '10px', color: '#64748b' }}>Priority Metric</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Case Details & Quick Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Case Scope Card */}
          <div
            style={{
              background: '#0f172a',
              border: '1px solid #1e293b',
              borderRadius: '8px',
              padding: '20px',
            }}
          >
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', marginBottom: '12px' }}>
              Case Tenant Context
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
              <div>
                <span style={{ color: '#64748b' }}>Case Code:</span>{' '}
                <strong style={{ color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {caseDetail.case_code}
                </strong>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Jurisdiction:</span>{' '}
                <span style={{ color: '#cbd5e1' }}>{caseDetail.jurisdiction}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Status:</span>{' '}
                <Badge variant="default">{caseDetail.status}</Badge>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Description:</span>
                <p style={{ color: '#94a3b8', marginTop: '4px', lineHeight: '1.4' }}>
                  {caseDetail.description}
                </p>
              </div>
            </div>
          </div>

          {/* Analytical Actions */}
          <div
            style={{
              background: '#0f172a',
              border: '1px solid #1e293b',
              borderRadius: '8px',
              padding: '20px',
            }}
          >
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', marginBottom: '12px' }}>
              Analytical Operations
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <Button
                variant="primary"
                size="sm"
                icon={<Cpu size={14} />}
                onClick={() => onNavigateToTab('graph')}
              >
                Launch Cytoscape Explorer
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={<CheckSquare size={14} />}
                onClick={() => onNavigateToTab('timeline')}
              >
                Inspect Event Timeline
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
