"""
Audit schemas for SIH26189.
Conforms to 02_DATABASE_SCHEMA.md (audit_logs table), 04_API_SPEC.md (Section 4.2),
and frontend contracts.ts.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AuditLogItem(BaseModel):
    """Single audit event item exposed via external contracts."""
    model_config = ConfigDict(from_attributes=True)

    audit_id: UUID
    actor: str = Field(..., description="Actor username or UUID string")
    action: str = Field(..., description="Action code, e.g. ENTITY_MERGE, EXPORT_REPORT")
    target_item: Optional[str] = Field(default=None, description="Masked target object identifier or detail")
    timestamp: datetime = Field(..., description="Timestamp of event occurrence")
    outcome: str = Field(default="SUCCESS", description="SUCCESS, DENIED, REJECTED, CONFIRMED")


class CaseAuditResponse(BaseModel):
    """Case-scoped operational audit trail response."""
    model_config = ConfigDict(from_attributes=True)

    audit_logs: List[AuditLogItem] = Field(default_factory=list)
    total: int = Field(ge=0, description="Total matching audit records")


class AuditFilterParams(BaseModel):
    """Query filters for case audit logs."""
    user_id: Optional[UUID] = None
    actor: Optional[str] = None
    action_code: Optional[str] = None
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditCreate(BaseModel):
    """Payload to record an immutable audit ledger entry."""
    actor_uuid: UUID
    action_code: str
    case_id: Optional[UUID] = None
    target_item: Optional[str] = None
    outcome: str = "SUCCESS"
