from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.evidence_analysis import ProvenanceSpan, RelationshipEndpointSummary

class RelationshipEvidenceCreate(BaseModel):
    """Payload to register new evidence supporting a relationship."""
    relationship_id: UUID
    source_ref: str = Field(..., description="The source document or chunk reference UUID/hash")
    support_type: str = Field(..., description="The type of evidence support, e.g. TEXT_EXTRACTION, TABULAR, CDR")
    
class RelationshipStateUpdate(BaseModel):
    """Payload to forcibly update relationship state (mostly for reviews/overrides)."""
    relationship_id: UUID
    status: str
    override_notes: Optional[str] = None

class EvidenceTraceItem(BaseModel):
    """Detailed item in the evidence trace."""
    evidence_id: UUID
    source_ref: str
    support_type: str
    provenance_spans: List[ProvenanceSpan] = Field(default_factory=list)

class EvidenceTraceResponse(BaseModel):
    """Authoritative API response detailing the provenance and confidence of a relationship."""
    model_config = ConfigDict(from_attributes=True)
    
    relationship_id: UUID
    case_id: UUID
    source_entity: RelationshipEndpointSummary
    target_entity: RelationshipEndpointSummary
    type: str
    status: str
    
    # Trace list
    evidence_items: List[EvidenceTraceItem] = Field(default_factory=list)
    
    # DS & Confidence Separation
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    entity_match_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    relationship_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    belief: float = Field(default=0.0, ge=0.0, le=1.0)
    disbelief: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty: float = Field(default=1.0, ge=0.0, le=1.0)
    conflict_mass: float = Field(default=0.0, ge=0.0, le=1.0)
    
    audit_events: List[Dict[str, Any]] = Field(default_factory=list, description="Historical audit actions related to this relationship")
    created_at: datetime
