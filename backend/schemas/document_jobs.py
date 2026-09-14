"""
Canonical Document Processing & Task Job Schemas for SIH26189.
Defines document lifecycle states, background worker task requests,
results, and repository entity records conforming to 01_SHARED_TYPES.md,
02_DATABASE_SCHEMA.md, and 06_WORKFLOWS.md.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from agents.extraction.ocr.schemas import OCRDocumentResult
from agents.extraction.schemas import ExtractionJobResponse


class DocumentState(str, Enum):
    """
    Canonical document ingestion lifecycle states.
    Conforms to 01_SHARED_TYPES.md (Section 1.3) and 06_WORKFLOWS.md (Section 6).
    Progression: RECEIVED -> VALIDATED -> PROCESSING -> EXTRACTED -> REVIEW_REQUIRED -> ACCEPTED / REJECTED
    Failure: FAILED
    """
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class DocumentTaskRequest(BaseModel):
    """
    Payload for document task processing executed by the Document Task Pipeline.
    Encapsulates case boundary, document identifier, storage reference, and caller identity.
    """
    model_config = ConfigDict(frozen=True)

    job_id: UUID = Field(default_factory=uuid4, description="Unique identifier for worker task execution")
    document_id: UUID = Field(default_factory=uuid4, description="Target document identifier")
    case_id: UUID = Field(..., description="Mandatory case tenant boundary")
    filename: str = Field(..., min_length=1, description="Original uploaded filename (subject to sanitization)")
    storage_key: Optional[str] = Field(None, description="Storage key in document storage abstraction")
    caller_user_id: Optional[UUID] = Field(None, description="Requesting user UUID for authorization check")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Auxiliary task metadata")


class DocumentTaskResult(BaseModel):
    """
    Result returned upon completion or controlled failure of the Document Task Pipeline.
    Preserves exact OCR and Agent 1 artifacts, provenance, and state transitions.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    job_id: UUID
    document_id: UUID
    case_id: UUID
    status: DocumentState
    detected_type: Optional[str] = None
    total_pages: int = 0
    full_text: Optional[str] = None
    ocr_result: Optional[OCRDocumentResult] = None
    extraction_result: Optional[ExtractionJobResponse] = None
    error_message: Optional[str] = None
    error_category: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class DocumentRecord(BaseModel):
    """
    Transactional document entity record matching PostgreSQL documents table
    defined in 02_DATABASE_SCHEMA.md (Section 2.1).
    """
    document_id: UUID
    case_id: UUID
    file_type: str
    file_hash: str
    storage_key: str
    filename: str
    status: DocumentState = DocumentState.RECEIVED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extraction_job_id: Optional[UUID] = None
    error_message: Optional[str] = None
