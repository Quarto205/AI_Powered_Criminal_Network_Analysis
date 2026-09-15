from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.db.models.entities import Relationship, RelationshipEvidenceState
from backend.db.models.analytics import AuditLog
from backend.security.audit import SecurityAuditAction

def soft_delete_relationship(
    db: Session,
    relationship_id: UUID,
    user_id: UUID,
    reason: str
) -> Relationship:
    """
    Flags a relationship as REJECTED without physically deleting the evidence rows
    or the source documents, preserving historical provenance.
    """
    rel = db.query(Relationship).filter_by(relationship_id=relationship_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
        
    # We must ensure the relationship is not already INFERRED, though policy allows rejecting them.
    # CONFIRMED relationships CAN be rejected by an investigator.
    
    old_status = rel.status
    rel.status = RelationshipEvidenceState.REJECTED.value
    
    # Generate audit trail
    audit = AuditLog(
        actor_uuid=user_id,
        action_code=SecurityAuditAction.RELATIONSHIP_REJECTED if hasattr(SecurityAuditAction, 'RELATIONSHIP_REJECTED') else "RELATIONSHIP_REJECTED",
        case_id=rel.case_id,
        target_item=str(rel.relationship_id),
        outcome="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(rel)
    
    return rel
