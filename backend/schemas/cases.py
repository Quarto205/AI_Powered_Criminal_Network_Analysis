"""
Pydantic schemas for Case Management.
Conforms strictly to 04_API_SPEC.md (Section 4.2), 02_DATABASE_SCHEMA.md,
and Section 21-42 of the task contract.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    """Payload for creating a new investigation case."""
    case_code: str = Field(..., min_length=3, max_length=50, description="Unique case code identifier")
    title: str = Field(..., min_length=3, max_length=255, description="Case title")
    description: Optional[str] = Field(default=None, description="Detailed case background")
    jurisdiction: str = Field(..., min_length=2, max_length=100, description="Jurisdictional boundary")


class CaseCreateResponse(BaseModel):
    """Response payload upon successful case creation."""
    case_id: UUID
    case_code: str
    title: str
    status: str
    jurisdiction: str
    created_at: datetime
    created_by: UUID


class CaseUpdateRequest(BaseModel):
    """Payload for updating case attributes."""
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = None
    jurisdiction: Optional[str] = Field(default=None, min_length=2, max_length=100)
    status: Optional[str] = Field(
        default=None,
        description="Allowed statuses: ACTIVE, ARCHIVED, CLOSED, PENDING_REVIEW",
    )


class CaseDetailResponse(BaseModel):
    """Detailed case summary including aggregate document and entity counts."""
    case_id: UUID
    case_code: str
    title: str
    description: Optional[str] = None
    status: str
    jurisdiction: str
    created_by: UUID
    created_at: datetime
    document_count: int = 0
    entity_count: int = 0


class CaseListItem(BaseModel):
    """Summary item for authorized case listings."""
    case_id: UUID
    case_code: str
    title: str
    status: str
    jurisdiction: str
    member_role: str
    created_at: datetime


class CaseListResponse(BaseModel):
    """List of cases where the requesting user has active membership."""
    cases: List[CaseListItem]
    total: int
    limit: int
    offset: int


class CaseMemberAddRequest(BaseModel):
    """Payload for adding or updating case membership."""
    user_id: UUID = Field(..., description="Target user UUID")
    role_in_case: str = Field(
        ...,
        description="Role in case: INVESTIGATOR, ANALYST, or SUPERVISOR",
    )


class CaseMemberItem(BaseModel):
    """Sanitized member information within a case."""
    user_id: UUID
    username: str
    email: str
    role_in_case: str
