"""
Pydantic Schemas for Evidence Detail, Human Review Overrides, and Analysis APIs.
Conforms strictly to 01_SHARED_TYPES.md, 04_API_SPEC.md, 05_AI_CONTRACTS.md, and 08_UI_DATA_CONTRACT.md.
Enforces non-accusatory terminology: Priority Ranking, Risk Score, Investigative Lead, Pattern Alert.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==============================================================================
# 1. EVIDENCE & PROVENANCE SCHEMAS
# ==============================================================================

class ProvenanceSpan(BaseModel):
    """Specific textual source span and location origin."""
    model_config = ConfigDict(from_attributes=True)

    chunk_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    file_name: Optional[str] = None
    version_hash: Optional[str] = None
    page_number: Optional[int] = None
    character_start: Optional[int] = None
    character_end: Optional[int] = None
    source_ref: str
    support_type: str
    snippet: Optional[str] = None


class EntityAliasInfo(BaseModel):
    """Observed alias name."""
    model_config = ConfigDict(from_attributes=True)

    alias_id: UUID
    alias_text: str
    source_ref: Optional[str] = None


class EntityIdentifierInfo(BaseModel):
    """Masked identifier attribute."""
    model_config = ConfigDict(from_attributes=True)

    identifier_id: UUID
    type: str
    masked_value: str
    value_policy: Optional[str] = None


class RiskScoreInfo(BaseModel):
    """Prioritization score summary (Investigative Lead / Priority Ranking)."""
    model_config = ConfigDict(from_attributes=True)

    score_id: UUID
    score_type: str = Field(..., description="e.g. PRIORITY_RANKING, ANOMALY_SCORE")
    value: float = Field(..., ge=0.0, le=1.0, description="Priority ranking metric")
    features_summary: Optional[Dict[str, Any]] = None


class EntityDetailResponse(BaseModel):
    """Detailed canonical entity record with evidence provenance."""
    model_config = ConfigDict(from_attributes=True)

    entity_id: UUID
    case_id: UUID
    canonical_name: str
    entity_type: str
    status: str
    aliases: List[EntityAliasInfo] = Field(default_factory=list)
    identifiers: List[EntityIdentifierInfo] = Field(default_factory=list)
    risk_score: Optional[RiskScoreInfo] = None
    provenance_spans: List[ProvenanceSpan] = Field(default_factory=list)
    created_at: datetime


class EvidenceCitation(BaseModel):
    """Citation chain for relationship evidence."""
    model_config = ConfigDict(from_attributes=True)

    evidence_id: UUID
    source_ref: str
    support_type: str


class RelationshipEndpointSummary(BaseModel):
    """Summary of entity endpoint for relationship detail."""
    model_config = ConfigDict(from_attributes=True)

    entity_id: UUID
    canonical_name: str
    entity_type: str


class RelationshipDetailResponse(BaseModel):
    """Detailed canonical relationship record with citations."""
    model_config = ConfigDict(from_attributes=True)

    relationship_id: UUID
    case_id: UUID
    source_entity: RelationshipEndpointSummary
    target_entity: RelationshipEndpointSummary
    type: str
    status: str
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    is_predicted: bool = False
    evidence_citations: List[EvidenceCitation] = Field(default_factory=list)
    created_at: datetime


class EvidenceDetailResponse(BaseModel):
    """Detailed evidence record with provenance offsets and document source."""
    model_config = ConfigDict(from_attributes=True)

    evidence_id: UUID
    case_id: UUID
    relationship_id: Optional[UUID] = None
    source_ref: str
    support_type: str
    document_id: Optional[UUID] = None
    chunk_id: Optional[UUID] = None
    file_name: Optional[str] = None
    version_hash: Optional[str] = None
    page_number: Optional[int] = None
    character_start: Optional[int] = None
    character_end: Optional[int] = None
    snippet: Optional[str] = None
    created_at: Optional[datetime] = None


# ==============================================================================
# 2. HUMAN REVIEW OVERRIDE SCHEMAS
# ==============================================================================

class ReviewTargetType:
    ENTITY_RESOLUTION = "ENTITY_RESOLUTION"
    PREDICTION = "PREDICTION"
    EXTRACTION = "EXTRACTION"
    ENTITY = "ENTITY"
    RELATIONSHIP = "RELATIONSHIP"


class ReviewAction:
    CONFIRM = "CONFIRM"
    REJECT = "REJECT"
    MERGE = "MERGE"


class ReviewRequest(BaseModel):
    """Investigator / Supervisor override mutation request."""
    target_id: UUID = Field(..., description="UUID of entity, prediction, extraction, or relationship")
    target_type: str = Field(
        ...,
        description="ENTITY_RESOLUTION, PREDICTION, EXTRACTION, ENTITY, or RELATIONSHIP",
    )
    action: str = Field(..., description="CONFIRM, REJECT, or MERGE")
    secondary_target_id: Optional[UUID] = Field(
        default=None,
        description="For MERGE: the secondary entity UUID being absorbed into target_id",
    )
    reason: Optional[str] = Field(default=None, max_length=1000, description="Investigative justification")
    override_notes: Optional[str] = Field(default=None, max_length=1000, description="Canonical override notes per 04_API_SPEC.md")

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, v: str) -> str:
        val = v.strip().upper()
        allowed = {
            ReviewTargetType.ENTITY_RESOLUTION,
            ReviewTargetType.PREDICTION,
            ReviewTargetType.EXTRACTION,
            ReviewTargetType.ENTITY,
            ReviewTargetType.RELATIONSHIP,
        }
        if val not in allowed:
            raise ValueError(f"Invalid target_type '{v}'. Must be one of: {sorted(list(allowed))}")
        return val

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        val = v.strip().upper()
        if val not in (ReviewAction.CONFIRM, ReviewAction.REJECT, ReviewAction.MERGE):
            raise ValueError(f"Invalid action '{v}'. Must be CONFIRM, REJECT, or MERGE.")
        return val

    @model_validator(mode="before")
    @classmethod
    def reconcile_justification_inputs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            reason = data.get("reason")
            notes = data.get("override_notes")
            if reason and not notes:
                data["override_notes"] = reason
            elif notes and not reason:
                data["reason"] = notes
        return data

    @model_validator(mode="after")
    def validate_justification_present(self) -> "ReviewRequest":
        if not self.reason and not self.override_notes:
            raise ValueError("Either 'reason' or 'override_notes' must be provided as justification.")
        if self.reason and not self.override_notes:
            self.override_notes = self.reason
        elif self.override_notes and not self.reason:
            self.reason = self.override_notes
        return self


class ReviewResponse(BaseModel):
    """Receipt returned upon successful review override."""
    review_id: UUID = Field(default_factory=uuid4)
    target_type: str
    target_id: UUID
    action: str
    resulting_status: str = "REVIEWED"
    status: Optional[str] = None
    secondary_target_id: Optional[UUID] = None
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""
    override_notes: Optional[str] = None

    @model_validator(mode="after")
    def sync_fields(self) -> "ReviewResponse":
        if not self.status and self.resulting_status:
            self.status = self.resulting_status
        elif not self.resulting_status and self.status:
            self.resulting_status = self.status
        if not self.override_notes and self.reason:
            self.override_notes = self.reason
        elif not self.reason and self.override_notes:
            self.reason = self.override_notes
        return self


# ==============================================================================
# 3. ANALYSIS & INTELLIGENCE SCHEMAS
# ==============================================================================

class AnalysisPipelines:
    SNA = "SNA"
    PATTERN_MOTIFS = "PATTERN_MOTIFS"
    GAT_LINK_PREDICTION = "GAT_LINK_PREDICTION"
    ALL = [SNA, PATTERN_MOTIFS, GAT_LINK_PREDICTION]


class AnalysisParameters(BaseModel):
    """Optional tuning parameters for analysis pipelines."""
    time_window_days: int = Field(default=90, ge=1, le=3650)
    min_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class AnalysisTriggerRequest(BaseModel):
    """Request payload to dispatch asynchronous analysis."""
    pipelines: List[str] = Field(
        default_factory=lambda: [AnalysisPipelines.SNA, AnalysisPipelines.PATTERN_MOTIFS],
        description="List of analytical pipelines to execute",
    )
    parameters: AnalysisParameters = Field(default_factory=AnalysisParameters)

    @field_validator("pipelines")
    @classmethod
    def validate_pipelines(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one analysis pipeline must be specified.")
        for p in v:
            if p.upper() not in AnalysisPipelines.ALL:
                raise ValueError(f"Unknown pipeline '{p}'. Allowed: {AnalysisPipelines.ALL}")
        return [p.upper() for p in v]


class AnalysisTriggerResponse(BaseModel):
    """Immediate receipt returned upon async analysis dispatch (HTTP 202 Accepted)."""
    run_id: UUID
    case_id: UUID
    status: str = "PENDING"
    pipelines: List[str]
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalysisRunDetailResponse(BaseModel):
    """Execution status and metadata of an analytical run."""
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    case_id: Optional[UUID] = None
    model_name: str
    version: str
    task_type: str
    status: str
    input_snapshot_checksum: str
    created_at: datetime


class ScoreItem(BaseModel):
    """Prioritization score item for case entity."""
    score_id: UUID
    entity_id: UUID
    canonical_name: str
    entity_type: str
    score_type: str
    value: float
    features_summary: Optional[Dict[str, Any]] = None


class CaseScoresResponse(BaseModel):
    """Collection of case investigative priority scores."""
    case_id: UUID
    scores: List[ScoreItem] = Field(default_factory=list)
    total: int = Field(ge=0)


class AlertItem(BaseModel):
    """Pattern finding / motif alert."""
    alert_id: UUID
    case_id: UUID
    alert_type: str
    severity: str
    rule_id: str
    status: str
    contributing_entities: Any


class CaseAlertsResponse(BaseModel):
    """Collection of case pattern alerts."""
    case_id: UUID
    alerts: List[AlertItem] = Field(default_factory=list)
    total: int = Field(ge=0)


class AlertFilterParams(BaseModel):
    """Optional query filters for alerts."""
    severity: Optional[str] = None
    status: Optional[str] = None
