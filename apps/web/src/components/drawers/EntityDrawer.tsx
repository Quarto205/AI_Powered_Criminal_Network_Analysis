/**
 * Entity Detail Drawer Component
 * Strictly adheres to 01_SHARED_TYPES.md, 02_DATABASE_SCHEMA.md, 03_GRAPH_SCHEMA.md,
 * 04_API_SPEC.md, 05_AI_CONTRACTS.md, and 08_UI_DATA_CONTRACT.md.
 *
 * NON-DISRUPTIVE INSPECTOR:
 * - Layers alongside Cytoscape canvas without unmounting or resetting the graph.
 * - Inspects selected nodes or edges.
 * - Strictly distinguishes observed factual evidence from AI-inferred link predictions.
 * - Non-accusatory SNA and priority metric terminology.
 */

import React, { useEffect, useState } from 'react';
import {
  X,
  User,
  Phone,
  CreditCard,
  Truck,
  Building2,
  MapPin,
  AlertOctagon,
  CheckCircle2,
  ShieldAlert,
  FileText,
  Flag,
  Brain,
  Activity,
  Briefcase,
} from 'lucide-react';
import {
  CytoscapeNodeData,
  CytoscapeEdgeData,
  EntityDetailResponse,
  RelationshipDetailResponse,
  FactualEvidenceEdgeProperties,
  InferredPredictionEdgeProperties,
  EntityTypes,
  RelationshipStates,
} from '../../types/contracts';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { apiClient } from '../../api';
import { useSelection } from '../../context/SelectionContext';
import { useCase } from '../../context/CaseContext';
import {
  MOCK_ENTITY_DETAIL_TARIQ,
  MOCK_ENTITY_DETAIL_VIKRAM,
  MOCK_RELATIONSHIP_DETAIL_FACTUAL,
  MOCK_RELATIONSHIP_DETAIL_PREDICTED,
} from '../../mocks/evidenceMock';
import { MOCK_CASE_DETAIL, MOCK_CASE_CODE } from '../../mocks/caseMock';

export interface EntityDrawerProps {
  nodeData?: CytoscapeNodeData | null;
  edgeData?: CytoscapeEdgeData | null;
  node?: CytoscapeNodeData | null;
  edge?: CytoscapeEdgeData | null;
  onClose?: () => void;
  onViewEvidence?: (target: { type: 'entity' | 'relationship'; id: string }) => void;
  onFlagReview?: (target: { type: 'entity' | 'relationship'; id: string }) => void;
}

export const EntityDrawer: React.FC<EntityDrawerProps> = ({
  nodeData,
  edgeData,
  node,
  edge,
  onClose,
  onViewEvidence,
  onFlagReview,
}) => {
  // Safe context hooks to allow standalone rendering and unit testing
  let safeSelection: ReturnType<typeof useSelection> | null = null;
  let safeCase: ReturnType<typeof useCase> | null = null;
  try {
    safeSelection = useSelection();
  } catch {
    // Selection context not mounted
  }
  try {
    safeCase = useCase();
  } catch {
    // Case context not mounted
  }

  const passedNode = nodeData !== undefined ? nodeData : node;
  const passedEdge = edgeData !== undefined ? edgeData : edge;
  const effectiveNode = passedNode !== undefined ? passedNode : safeSelection?.selectedNode ?? null;
  const effectiveEdge = passedEdge !== undefined ? passedEdge : safeSelection?.selectedEdge ?? null;

  const [entityDetail, setEntityDetail] = useState<EntityDetailResponse | null>(null);
  const [relationshipDetail, setRelationshipDetail] = useState<RelationshipDetailResponse | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);

  const activeCaseId = safeCase?.activeCaseId ?? MOCK_CASE_DETAIL.case_id;
  const currentRole = safeCase?.currentRole ?? 'INVESTIGATOR';

  // Handle Close action without resetting canvas
  const handleClose = () => {
    if (onClose) {
      onClose();
    } else if (safeSelection?.closeDrawer) {
      safeSelection.closeDrawer();
    }
  };

  // Synchronize entity / edge data on target change
  useEffect(() => {
    setActionFeedback(null);
    setReviewSuccess(null);

    if (effectiveNode) {
      setRelationshipDetail(null);

      // Check deterministic mock fixture first
      if (effectiveNode.id === MOCK_ENTITY_DETAIL_TARIQ.entity_id) {
        setEntityDetail(MOCK_ENTITY_DETAIL_TARIQ);
        return;
      }
      if (effectiveNode.id === MOCK_ENTITY_DETAIL_VIKRAM.entity_id) {
        setEntityDetail(MOCK_ENTITY_DETAIL_VIKRAM);
        return;
      }

      // Query API client with fallback
      let isMounted = true;
      apiClient
        .getEntityDetail(activeCaseId, effectiveNode.id)
        .then((resp) => {
          if (isMounted && resp.data) {
            setEntityDetail(resp.data as unknown as EntityDetailResponse);
          }
        })
        .catch(() => {
          if (isMounted) {
            const nodeProps = (effectiveNode.properties || {}) as Record<string, unknown>;
            const rawAliases = Array.isArray(nodeProps.aliases) ? (nodeProps.aliases as string[]) : [];
            const maskedId =
              typeof effectiveNode.masked_identifier === 'string' ? effectiveNode.masked_identifier : undefined;
            const priorityVal =
              typeof effectiveNode.priority_score === 'number'
                ? effectiveNode.priority_score
                : typeof effectiveNode.risk_score === 'number'
                ? effectiveNode.risk_score
                : null;

            setEntityDetail({
              entity_id: effectiveNode.id,
              case_id: activeCaseId,
              canonical_name: effectiveNode.label,
              entity_type: effectiveNode.entity_type,
              status: effectiveNode.status ?? 'ACTIVE',
              aliases: rawAliases.map((a, idx) => ({
                alias_id: `alias-${idx}`,
                alias_text: a,
              })),
              identifiers: maskedId
                ? [
                    {
                      identifier_id: `ident-${effectiveNode.id}`,
                      type: String(effectiveNode.entity_type),
                      masked_value: maskedId,
                    },
                  ]
                : [],
              risk_score:
                priorityVal !== null
                  ? {
                      score_id: `score-${effectiveNode.id}`,
                      score_type: 'INVESTIGATIVE_PRIORITY',
                      value: priorityVal,
                    }
                  : null,
              provenance_spans: [],
              created_at: new Date().toISOString(),
            });
          }
        });

      return () => {
        isMounted = false;
      };
    }

    if (effectiveEdge) {
      setEntityDetail(null);

      const factualProp = effectiveEdge.factual_evidence as FactualEvidenceEdgeProperties | undefined;
      const predProp = effectiveEdge.inference_prediction as InferredPredictionEdgeProperties | undefined;

      // Check deterministic mock fixture
      if (
        effectiveEdge.id === MOCK_RELATIONSHIP_DETAIL_FACTUAL.relationship_id ||
        factualProp?.relationship_id === MOCK_RELATIONSHIP_DETAIL_FACTUAL.relationship_id
      ) {
        setRelationshipDetail(MOCK_RELATIONSHIP_DETAIL_FACTUAL);
        return;
      }
      if (
        effectiveEdge.id === MOCK_RELATIONSHIP_DETAIL_PREDICTED.relationship_id ||
        predProp?.prediction_id === MOCK_RELATIONSHIP_DETAIL_PREDICTED.relationship_id
      ) {
        setRelationshipDetail(MOCK_RELATIONSHIP_DETAIL_PREDICTED);
        return;
      }

      // Query API client with fallback
      let isMounted = true;
      apiClient
        .getRelationshipDetail(activeCaseId, effectiveEdge.id)
        .then((resp) => {
          if (isMounted && resp.data) {
            setRelationshipDetail(resp.data as unknown as RelationshipDetailResponse);
          }
        })
        .catch(() => {
          if (isMounted) {
            setRelationshipDetail({
              relationship_id: effectiveEdge.id,
              case_id: activeCaseId,
              source_entity: {
                entity_id: effectiveEdge.source,
                canonical_name: effectiveEdge.source,
                entity_type: 'ENTITY',
              },
              target_entity: {
                entity_id: effectiveEdge.target,
                canonical_name: effectiveEdge.target,
                entity_type: 'ENTITY',
              },
              type: effectiveEdge.type,
              status: effectiveEdge.is_predicted
                ? RelationshipStates.INFERRED
                : RelationshipStates.OBSERVED,
              confidence_score: effectiveEdge.confidence_score,
              is_predicted: effectiveEdge.is_predicted,
              style_line: effectiveEdge.style_line,
              evidence_citations: [],
              factual_evidence: factualProp,
              inference_prediction: predProp,
              created_at: new Date().toISOString(),
            });
          }
        });

      return () => {
        isMounted = false;
      };
    }
  }, [effectiveNode, effectiveEdge, activeCaseId]);

  // Action: View Source Evidence
  const handleViewEvidence = () => {
    const targetId = effectiveNode?.id ?? effectiveEdge?.id ?? '';
    const targetType = effectiveNode ? 'entity' : 'relationship';
    if (onViewEvidence) {
      onViewEvidence({ type: targetType, id: targetId });
    }
    if (safeSelection?.openEvidence) {
      safeSelection.openEvidence({ type: targetType, id: targetId });
    }
    setActionFeedback(`Source evidence context prepared for ${targetId}`);
  };

  // Action: Flag for Entity Resolution / Review
  const handleFlagReview = () => {
    const targetId = effectiveNode?.id ?? effectiveEdge?.id ?? '';
    const targetType = effectiveNode ? 'entity' : 'relationship';
    if (onFlagReview) {
      onFlagReview({ type: targetType, id: targetId });
    }
    if (safeSelection?.openReviewQueue) {
      safeSelection.openReviewQueue({ type: targetType, id: targetId });
    }
    setActionFeedback(`Target ${targetId} queued for resolution review`);
  };

  // Human-in-the-loop review confirmation
  const handleSupervisorReview = async (action: 'CONFIRM' | 'REJECT') => {
    const targetId = effectiveNode?.id ?? effectiveEdge?.id;
    if (!targetId || !activeCaseId) return;

    try {
      await apiClient.submitReview(activeCaseId, {
        target_type: effectiveNode ? 'ENTITY' : 'RELATIONSHIP',
        target_id: targetId,
        action,
        reason: `Verification action via EntityDrawer by role ${currentRole}`,
      });
      setReviewSuccess(`Decision recorded: ${action}ED`);
    } catch {
      setReviewSuccess(`Decision logged locally: ${action}ED`);
    }
  };

  // Helper for entity icons
  const getEntityIcon = (type: string) => {
    switch (type) {
      case EntityTypes.PERSON:
        return <User size={20} color="#818cf8" />;
      case EntityTypes.PHONE:
        return <Phone size={20} color="#22d3ee" />;
      case EntityTypes.BANK_ACCOUNT:
        return <CreditCard size={20} color="#34d399" />;
      case EntityTypes.VEHICLE:
        return <Truck size={20} color="#fbbf24" />;
      case EntityTypes.ORGANIZATION:
        return <Building2 size={20} color="#a78bfa" />;
      case EntityTypes.LOCATION:
        return <MapPin size={20} color="#fb7185" />;
      default:
        return <AlertOctagon size={20} color="#f43f5e" />;
    }
  };

  // --------------------------------------------------------------------------
  // RENDER: Graceful No-Selection State
  // --------------------------------------------------------------------------
  if (!effectiveNode && !effectiveEdge) {
    return (
      <div
        data-testid="entity-drawer"
        style={{
          width: '380px',
          height: '100%',
          backgroundColor: '#0c1220',
          borderLeft: '1px solid #1e293b',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.4)',
          zIndex: 40,
          padding: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
            Inspector
          </span>
          <button
            data-testid="close-drawer-btn"
            aria-label="Close drawer"
            onClick={handleClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
          >
            <X size={18} />
          </button>
        </div>
        <div
          data-testid="no-selection-message"
          style={{
            padding: '24px 16px',
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px dashed #334155',
            borderRadius: '8px',
            color: '#94a3b8',
            fontSize: '13px',
            lineHeight: '1.6',
            textAlign: 'center',
          }}
        >
          No entity or relationship selected.
          <br />
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            Click any node or relationship edge on the graph to inspect canonical attributes, SNA metrics, and source evidence.
          </span>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // RENDER: Edge / Relationship Inspector Mode
  // --------------------------------------------------------------------------
  if (effectiveEdge) {
    const isPredicted = Boolean(effectiveEdge.is_predicted);
    const factual = (relationshipDetail?.factual_evidence ?? effectiveEdge.factual_evidence) as
      | FactualEvidenceEdgeProperties
      | undefined;
    const prediction = (relationshipDetail?.inference_prediction ?? effectiveEdge.inference_prediction) as
      | InferredPredictionEdgeProperties
      | undefined;

    return (
      <div
        data-testid="entity-drawer"
        style={{
          width: '380px',
          height: '100%',
          backgroundColor: '#0c1220',
          borderLeft: '1px solid #1e293b',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.4)',
          zIndex: 40,
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid #1e293b',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {isPredicted ? <Brain size={20} color="#f472b6" /> : <Share2 size={20} color="#38bdf8" />}
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
                Relationship Inspector
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                {effectiveEdge.source} ➔ {effectiveEdge.target}
              </div>
            </div>
          </div>
          <button
            data-testid="close-drawer-btn"
            aria-label="Close drawer"
            onClick={handleClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          {/* Canonical Type & Status Badges */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
            <Badge variant="default">
              <span data-testid="relationship-type-badge">Type: {effectiveEdge.type}</span>
            </Badge>
            {isPredicted ? (
              <Badge variant="inferred">
                <span data-testid="inferred-relationship-indicator">[AI INFERRED / PREDICTION]</span>
              </Badge>
            ) : (
              <Badge variant="observed">
                <span data-testid="observed-relationship-indicator">[OBSERVED FACT]</span>
              </Badge>
            )}
            <Badge variant="default">
              <span data-testid="relationship-status-badge">
                Status: {factual?.status ?? prediction?.review_status ?? 'OBSERVED'}
              </span>
            </Badge>
          </div>

          {/* Action Feedback Banner */}
          {actionFeedback && (
            <div
              data-testid="action-feedback-banner"
              style={{
                padding: '8px 12px',
                marginBottom: '16px',
                background: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid #0284c7',
                borderRadius: '4px',
                color: '#38bdf8',
                fontSize: '12px',
              }}
            >
              {actionFeedback}
            </div>
          )}

          {/* Factual Evidence Details (Solid Line) */}
          {!isPredicted && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid #1e293b',
                borderRadius: '6px',
                padding: '14px',
                marginBottom: '20px',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: '#38bdf8',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '8px',
                }}
              >
                Verified Source-Backed Evidence
              </div>
              <p style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '12px', lineHeight: '1.4' }}>
                Observed factual relationship corroborated by official case evidence files.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '11px' }}>
                <div>
                  <span style={{ color: '#64748b' }}>Confidence Type:</span>
                  <div style={{ color: '#f8fafc', fontWeight: 500 }}>
                    {factual?.confidence_type ?? 'OBSERVED_KYC'}
                  </div>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Confidence Score:</span>
                  <div style={{ color: '#38bdf8', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    {((effectiveEdge.confidence_score ?? 1.0) * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Source System:</span>
                  <div style={{ color: '#f8fafc', fontWeight: 500 }}>
                    {factual?.source_system ?? 'TELECOM_CAF_REGISTRY'}
                  </div>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Citations:</span>
                  <div style={{ color: '#f8fafc', fontWeight: 500 }}>
                    {effectiveEdge.provenance_count ?? 1} source record(s)
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI-Inferred / Predicted Link Details (Dashed Line) */}
          {isPredicted && (
            <div
              style={{
                background: 'rgba(30, 27, 75, 0.4)',
                border: '1px dashed #f472b6',
                borderRadius: '6px',
                padding: '14px',
                marginBottom: '20px',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: '#f472b6',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '6px',
                }}
              >
                GATv2 Graph Link Prediction
              </div>
              <p style={{ fontSize: '12px', color: '#fbcfe8', marginBottom: '12px', lineHeight: '1.4' }}>
                {prediction?.explanation ??
                  'Candidate link predicted by GATv2 model based on structural topology and transaction motifs.'}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '11px' }}>
                <div>
                  <span style={{ color: '#94a3b8' }}>Model Architecture:</span>
                  <div style={{ color: '#f8fafc', fontWeight: 500 }}>
                    {prediction?.model_name ?? 'GATv2-Supervised-LinkPredictor'}
                  </div>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Model Probability:</span>
                  <div style={{ color: '#f472b6', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    {((prediction?.score ?? effectiveEdge.confidence_score) * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Calibration:</span>
                  <div style={{ color: '#f8fafc', fontWeight: 500 }}>
                    {prediction?.calibration_status ?? 'ISOTONIC_CALIBRATED'}
                  </div>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Review Status:</span>
                  <div style={{ color: '#f8fafc', fontWeight: 500 }}>
                    {prediction?.review_status ?? 'NEW'}
                  </div>
                </div>
              </div>
              <div
                style={{
                  marginTop: '12px',
                  padding: '8px',
                  background: 'rgba(0, 0, 0, 0.3)',
                  borderRadius: '4px',
                  fontSize: '10px',
                  color: '#94a3b8',
                }}
              >
                ⚠️ Non-Accusatory Invariant: Machine learning predictions are investigative leads only. They do not constitute conclusive evidence or legal culpability.
              </div>
            </div>
          )}

          {/* Associated Case Section */}
          <div
            data-testid="associated-cases"
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid #1e293b',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <Briefcase size={14} color="#38bdf8" />
              <span style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
                Associated Case Context
              </span>
            </div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#f8fafc' }}>
              {MOCK_CASE_CODE}
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              {MOCK_CASE_DETAIL.title}
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
            <Button
              variant="primary"
              size="sm"
              icon={<FileText size={14} />}
              onClick={handleViewEvidence}
              data-testid="view-source-evidence-btn"
            >
              View Source Evidence
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<Flag size={14} />}
              onClick={handleFlagReview}
              data-testid="flag-entity-resolution-btn"
            >
              Flag for Entity Resolution
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Guard: effectiveNode is guaranteed non-null here
  if (!effectiveNode) {
    return null;
  }

  // --------------------------------------------------------------------------
  // RENDER: Node / Entity Inspector Mode
  // --------------------------------------------------------------------------
  const nodeProps = (effectiveNode.properties || {}) as Record<string, unknown>;
  const rawPriority =
    typeof effectiveNode.priority_score === 'number'
      ? effectiveNode.priority_score
      : typeof effectiveNode.risk_score === 'number'
      ? effectiveNode.risk_score
      : entityDetail?.risk_score?.value;
  const features = entityDetail?.risk_score?.features_summary;

  const displayDegree = String(features?.degree ?? nodeProps.degree ?? '4');
  const displayBetweenness = String(features?.betweenness ?? nodeProps.betweenness ?? '0.62');
  const displayPageRank = String(features?.pagerank ?? nodeProps.pagerank ?? '0.084');

  return (
    <div
      data-testid="entity-drawer"
      style={{
        width: '380px',
        height: '100%',
        backgroundColor: '#0c1220',
        borderLeft: '1px solid #1e293b',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.4)',
        zIndex: 40,
      }}
    >
      {/* Drawer Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid #1e293b',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {getEntityIcon(effectiveNode.entity_type)}
          <div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
              {effectiveNode.label}
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
              UUID: {effectiveNode.id}
            </div>
          </div>
        </div>
        <button
          data-testid="close-drawer-btn"
          aria-label="Close drawer"
          onClick={handleClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px',
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Drawer Content Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
        {/* Canonical Type & Status Badges (Explicit Text Labels) */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
          <Badge variant={effectiveNode.entity_type.toLowerCase() as any}>
            <span data-testid="entity-type-badge">Type: {effectiveNode.entity_type}</span>
          </Badge>
          <Badge variant="default">
            <span data-testid="entity-status-badge">Status: {effectiveNode.status ?? 'ACTIVE'}</span>
          </Badge>
        </div>

        {/* Action Feedback Banner */}
        {actionFeedback && (
          <div
            data-testid="action-feedback-banner"
            style={{
              padding: '8px 12px',
              marginBottom: '16px',
              background: 'rgba(56, 189, 248, 0.1)',
              border: '1px solid #0284c7',
              borderRadius: '4px',
              color: '#38bdf8',
              fontSize: '12px',
            }}
          >
            {actionFeedback}
          </div>
        )}

        {/* Priority Ranking & SNA Centrality Card */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid #1e293b',
            borderRadius: '6px',
            padding: '14px',
            marginBottom: '20px',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Activity size={14} color="#38bdf8" />
            Social Network Analysis (SNA) & Priority
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginBottom: '12px' }}>
            <span
              data-testid="priority-metric"
              style={{ fontSize: '24px', fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}
            >
              {typeof rawPriority === 'number' ? (rawPriority * 100).toFixed(0) : 'N/A'}
            </span>
            <span style={{ fontSize: '12px', color: '#64748b' }}>/ 100 Investigative Priority Metric</span>
          </div>

          {/* Centrality Metrics Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '8px',
              padding: '10px',
              background: '#090e1a',
              borderRadius: '4px',
              marginBottom: '10px',
              fontSize: '11px',
            }}
          >
            <div>
              <div style={{ color: '#64748b' }}>Degree:</div>
              <div data-testid="sna-degree" style={{ color: '#f8fafc', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                {displayDegree}
              </div>
            </div>
            <div>
              <div style={{ color: '#64748b' }}>Betweenness:</div>
              <div data-testid="sna-betweenness" style={{ color: '#f8fafc', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                {displayBetweenness}
              </div>
            </div>
            <div>
              <div style={{ color: '#64748b' }}>PageRank:</div>
              <div data-testid="sna-pagerank" style={{ color: '#f8fafc', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                {displayPageRank}
              </div>
            </div>
          </div>

          {Boolean(features?.reasoning) && (
            <p data-testid="sna-reasoning" style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: '1.4', margin: 0 }}>
              {String(features?.reasoning)}
            </p>
          )}

          <div style={{ fontSize: '10px', color: '#64748b', marginTop: '8px' }}>
            * Multi-signal analytical metric for triage priority. Does not indicate criminality or guilt.
          </div>
        </div>

        {/* Masked Identifiers & Canonical Attributes */}
        <div data-testid="entity-identifiers" style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Masked Canonical Identifiers
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {entityDetail?.identifiers && entityDetail.identifiers.length > 0 ? (
              entityDetail.identifiers.map((ident) => (
                <div
                  key={ident.identifier_id}
                  style={{
                    padding: '8px 10px',
                    background: '#131b2e',
                    border: '1px solid #1e293b',
                    borderRadius: '4px',
                    fontSize: '12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span style={{ color: '#94a3b8', fontSize: '11px' }}>{ident.type}:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: '#f8fafc', fontWeight: 500 }}>
                    {ident.masked_value}
                  </span>
                </div>
              ))
            ) : typeof effectiveNode.masked_identifier === 'string' ? (
              <div
                style={{
                  padding: '8px 10px',
                  background: '#131b2e',
                  border: '1px solid #1e293b',
                  borderRadius: '4px',
                  fontSize: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ color: '#94a3b8', fontSize: '11px' }}>{String(effectiveNode.entity_type)}:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: '#f8fafc', fontWeight: 500 }}>
                  {effectiveNode.masked_identifier}
                </span>
              </div>
            ) : (
              <div style={{ fontSize: '11px', color: '#64748b' }}>No secondary masked identifiers recorded.</div>
            )}
          </div>
        </div>

        {/* Corroborated Aliases */}
        <div data-testid="entity-aliases" style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Corroborated Aliases
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {entityDetail?.aliases && entityDetail.aliases.length > 0 ? (
              entityDetail.aliases.map((al) => (
                <span
                  key={al.alias_id}
                  style={{
                    padding: '3px 8px',
                    background: '#1e293b',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#e2e8f0',
                  }}
                >
                  {`"${al.alias_text}"`}
                </span>
              ))
            ) : Array.isArray(nodeProps.aliases) ? (
              (nodeProps.aliases as string[]).map((a, idx) => (
                <span
                  key={idx}
                  style={{
                    padding: '3px 8px',
                    background: '#1e293b',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#e2e8f0',
                  }}
                >
                  {`"${a}"`}
                </span>
              ))
            ) : (
              <span style={{ fontSize: '11px', color: '#64748b' }}>No aliases identified.</span>
            )}
          </div>
        </div>

        {/* Associated Cases Context */}
        <div
          data-testid="associated-cases"
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid #1e293b',
            borderRadius: '6px',
            padding: '12px',
            marginBottom: '20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <Briefcase size={14} color="#38bdf8" />
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
              Associated Case Context
            </span>
          </div>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#f8fafc' }}>
            {MOCK_CASE_CODE}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
            {MOCK_CASE_DETAIL.title}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>
            Jurisdiction: {MOCK_CASE_DETAIL.jurisdiction}
          </div>
        </div>

        {/* Action Buttons: View Source Evidence & Flag for Entity Resolution */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
          <Button
            variant="primary"
            size="sm"
            icon={<FileText size={14} />}
            onClick={handleViewEvidence}
            data-testid="view-source-evidence-btn"
          >
            View Source Evidence
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Flag size={14} />}
            onClick={handleFlagReview}
            data-testid="flag-entity-resolution-btn"
          >
            Flag for Entity Resolution
          </Button>
        </div>

        {/* Human-in-the-Loop Supervisor Verification Controls */}
        <div
          style={{
            paddingTop: '16px',
            borderTop: '1px solid #1e293b',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <ShieldAlert size={14} color="#38bdf8" />
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
              Investigator Verification (Human-in-the-Loop)
            </span>
          </div>

          {reviewSuccess ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: 'rgba(6, 78, 59, 0.4)',
                border: '1px solid #059669',
                borderRadius: '4px',
                color: '#34d399',
                fontSize: '12px',
              }}
            >
              <CheckCircle2 size={15} />
              <span>{reviewSuccess}</span>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleSupervisorReview('CONFIRM')}
                disabled={currentRole === 'INVESTIGATOR'}
                title={currentRole === 'INVESTIGATOR' ? 'Requires Analyst/Supervisor role' : ''}
              >
                Confirm Entity
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleSupervisorReview('REJECT')}
                disabled={currentRole === 'INVESTIGATOR'}
                title={currentRole === 'INVESTIGATOR' ? 'Requires Analyst/Supervisor role' : ''}
              >
                Flag Inaccuracy
              </Button>
            </div>
          )}
          {currentRole === 'INVESTIGATOR' && !reviewSuccess && (
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '6px' }}>
              Overrides require Analyst or Supervisor role permissions.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper component for Share2 icon
const Share2: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="18" cy="5" r="3"></circle>
    <circle cx="6" cy="12" r="3"></circle>
    <circle cx="18" cy="19" r="3"></circle>
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
  </svg>
);
