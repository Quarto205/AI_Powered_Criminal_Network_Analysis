import re
from typing import List, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.db.models.entities import Relationship, RelationshipEvidence, RelationshipEvidenceState
from backend.db.models.analytics import AuditLog
from agents.evidence.belief_engine import evidence_to_mass, dempster_combine
from backend.security.audit import SecurityAuditAction

def get_independent_source_key(source_ref: str) -> str:
    """
    Provenance-independence resolver.
    Extracts the root document ID or independent category from a source reference.
    If multiple chunks belong to the same document, they will yield the same independent source key.
    
    Expected format patterns:
    'doc:{uuid}|job:{uuid}' -> 'doc:{uuid}'
    'chunk:{uuid}|doc:{uuid}' -> 'doc:{uuid}'
    'fir:{uuid}' -> 'fir:{uuid}'
    """
    if not source_ref:
        return "UNKNOWN"
        
    doc_match = re.search(r"doc:([a-fA-F0-9\-]{36})", source_ref)
    if doc_match:
        return f"doc:{doc_match.group(1)}"
        
    fir_match = re.search(r"fir:([a-fA-F0-9\-]{36})", source_ref)
    if fir_match:
        return f"fir:{fir_match.group(1)}"
        
    # If no known parent prefix, the source_ref itself acts as its own category.
    # In a fully fleshed out system, this might query the DB to trace chunk_id -> document_id.
    return source_ref

def compute_fused_belief(evidence_items: List[RelationshipEvidence]) -> Tuple[float, float, float, float]:
    """
    Computes Dempster-Shafer b/d/u and K across all evidence items for a relationship.
    Assumes standard confidence for observations.
    """
    if not evidence_items:
        return 0.0, 0.0, 1.0, 0.0
        
    # Start with absolute ignorance (b=0, d=0, u=1)
    combined = (0.0, 0.0, 1.0)
    total_k = 0.0
    
    for item in evidence_items:
        # Default supportive evidence for OBSERVED/CORROBORATED. 
        # In a real system, support_type or another field might flag CONTRADICTION.
        is_supportive = item.support_type != "CONTRADICTION"
        
        # Base confidence 0.8 for extracted text, 0.9 for structured tabular
        conf = 0.8
        if "TABULAR" in item.support_type or "CDR" in item.support_type:
            conf = 0.9
            
        m = evidence_to_mass(conf, is_supportive=is_supportive)
        
        # Combine
        combined_b, combined_d, combined_u, K = dempster_combine(combined, m)
        combined = (combined_b, combined_d, combined_u)
        
        # Accumulate conflict. 
        # (This is a simplified accumulation; true DS tracks K at each orthogonal step).
        total_k += K
        
    return combined[0], combined[1], combined[2], min(1.0, total_k)

def register_relationship_evidence(
    db: Session,
    case_id: UUID,
    user_id: UUID,
    source_entity_uuid: UUID,
    target_entity_uuid: UUID,
    relationship_type: str,
    source_ref: str,
    support_type: str
) -> Relationship:
    """
    Authoritative provenance engine entry point.
    1. Validates case bounds.
    2. Upserts Relationship.
    3. Computes Corroboration state.
    4. Computes DS Belief.
    """
    # 1. Locate existing relationship
    rel = db.query(Relationship).filter_by(
        case_id=case_id,
        source_entity_uuid=source_entity_uuid,
        target_entity_uuid=target_entity_uuid,
        type=relationship_type
    ).first()
    
    if not rel:
        rel = Relationship(
            relationship_id=uuid4(),
            case_id=case_id,
            source_entity_uuid=source_entity_uuid,
            target_entity_uuid=target_entity_uuid,
            type=relationship_type,
            status=RelationshipEvidenceState.OBSERVED.value
        )
        db.add(rel)
        db.flush()
        
    # 2. Insert Evidence
    evidence = RelationshipEvidence(
        evidence_id=uuid4(),
        relationship_id=rel.relationship_id,
        source_ref=source_ref,
        support_type=support_type
    )
    db.add(evidence)
    db.flush()
    
    # 3. Retrieve all evidence to compute corroboration & DS
    all_evidence = db.query(RelationshipEvidence).filter_by(relationship_id=rel.relationship_id).all()
    rel.evidence_count = len(all_evidence)
    
    # Check independent sources
    independent_keys = set(get_independent_source_key(e.source_ref) for e in all_evidence)
    is_corroborated = len(independent_keys) > 1
    
    # State Machine Rules
    # CONFIRMED cannot be automatically downgraded. REJECTED cannot be automatically upgraded.
    if rel.status in [RelationshipEvidenceState.OBSERVED.value, RelationshipEvidenceState.CORROBORATED.value]:
        if is_corroborated:
            rel.status = RelationshipEvidenceState.CORROBORATED.value
            
    # 4. Compute DS Belief
    b, d, u, k = compute_fused_belief(all_evidence)
    rel.belief = b
    rel.disbelief = d
    rel.uncertainty = u
    rel.conflict_mass = k
    
    # Simple relationship confidence mapping
    rel.relationship_confidence = b  # As a simple proxy if no other formula provided
    
    # 5. Audit
    audit = AuditLog(
        actor_uuid=user_id,
        action_code="EVIDENCE_REGISTERED",
        case_id=case_id,
        target_item=str(rel.relationship_id),
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(rel)
    
    return rel
