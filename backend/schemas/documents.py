"""
Document API Request and Response Schemas for SIH26189.
Strictly adheres to:
- 01_SHARED_TYPES.md (Section 1.3 Document ingestion lifecycle)
- 02_DATABASE_SCHEMA.md (Domain B: Documents, Versions, Chunks)
- 04_API_SPEC.md (Section 4.2 Document endpoints)
- Step 3/4 canonical envelope, UUID-v4, snake_case standards.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.document_jobs import DocumentState


class DocumentUploadData(BaseModel):
    """Payload data returned on successful document intake (HTTP 202 Accepted)."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID = Field(..., description="Unique UUID-v4 of the created document")
    job_id: UUID = Field(..., description="Unique UUID-v4 of the async background worker task")
    case_id: UUID = Field(..., description="Case tenant boundary")
    file_name: str = Field(..., description="Sanitized original document filename")
    file_type: str = Field(..., description="Detected canonical MIME type (e.g. application/pdf)")
    file_hash: str = Field(..., description="Canonical SHA-256 hash of binary content")
    status: str = Field(default=DocumentState.RECEIVED.value, description="Initial lifecycle state")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentSummary(BaseModel):
    """Summary representation for document listing."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    case_id: UUID
    file_name: Optional[str] = None
    file_type: str
    file_hash: str
    status: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    """Paginated collection of case documents."""
    items: List[DocumentSummary] = Field(default_factory=list)
    total: int = Field(ge=0)
    limit: int = Field(gt=0, le=200)
    offset: int = Field(ge=0)


class DocumentVersionInfo(BaseModel):
    """Metadata summary of a document version."""
    model_config = ConfigDict(from_attributes=True)

    version_id: UUID
    version_hash: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class DocumentDetailResponse(BaseModel):
    """Full detail metadata for a single document entity."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    case_id: UUID
    file_name: Optional[str] = None
    file_type: str
    file_hash: str
    storage_key: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    latest_version: Optional[DocumentVersionInfo] = None
    chunk_count: int = Field(default=0, ge=0)
    error_category: Optional[str] = None
    error_message: Optional[str] = None


class DocumentChunkItem(BaseModel):
    """Individual chunk and provenance span metadata."""
    model_config = ConfigDict(from_attributes=True)

    chunk_id: UUID
    version_id: UUID
    page_number: Optional[int] = None
    character_span: Optional[str] = None
    text_hash: str
    storage_ref: str


class DocumentChunkListResponse(BaseModel):
    """Deterministic, ordered sequence of document chunks."""
    items: List[DocumentChunkItem] = Field(default_factory=list)
    total: int = Field(ge=0)


class DocumentArchiveResponse(BaseModel):
    """Response payload upon soft-deleting/archiving a document."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    case_id: UUID
    status: str = Field(default=DocumentState.REJECTED.value)
    archived_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
