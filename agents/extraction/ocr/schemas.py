"""
Schemas for OCR Preprocessor and Document Text Extraction Engine.
"""

from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class OCRDocumentType(str, Enum):
    """Detected document representation."""
    DIGITAL_PDF = "DIGITAL_PDF"
    SCANNED_PDF = "SCANNED_PDF"
    MIXED_PDF = "MIXED_PDF"
    IMAGE_PNG = "IMAGE_PNG"
    IMAGE_JPEG = "IMAGE_JPEG"
    UNKNOWN = "UNKNOWN"


class OCRProcessingStatus(str, Enum):
    """Outcome status of the document parsing/OCR operation."""
    SUCCESS = "SUCCESS"
    EMPTY_DOCUMENT = "EMPTY_DOCUMENT"
    CORRUPTED_FILE = "CORRUPTED_FILE"
    PASSWORD_PROTECTED = "PASSWORD_PROTECTED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    OCR_ENGINE_FAILURE = "OCR_ENGINE_FAILURE"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"


class OCRPageResult(BaseModel):
    """Extracted text and provenance for a single page."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    page_number: int = Field(
        ...,
        ge=1,
        description="1-indexed page number within the document."
    )
    text: str = Field(
        ...,
        description="Clean UTF-8 text extracted from this page."
    )
    character_start: int = Field(
        ...,
        ge=0,
        description="Start character index of this page within the document's full_text."
    )
    character_end: int = Field(
        ...,
        ge=0,
        description="End character index of this page within the document's full_text."
    )
    is_ocr_applied: bool = Field(
        default=False,
        description="True if OCR was executed for this page; False if direct digital text extraction was used."
    )
    ocr_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for OCR text recognition if applicable."
    )


class OCRDocumentResult(BaseModel):
    """Canonical result emitted by the OCR preprocessor before handoff to Agent 1."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the processed document."
    )
    status: OCRProcessingStatus = Field(
        ...,
        description="Overall processing status."
    )
    detected_type: OCRDocumentType = Field(
        ...,
        description="Detected document type based on signature and page contents."
    )
    total_pages: int = Field(
        default=0,
        ge=0,
        description="Total count of processed pages."
    )
    pages: List[OCRPageResult] = Field(
        default_factory=list,
        description="Page-level text results and character boundaries."
    )
    full_text: str = Field(
        default="",
        description="Concatenated clean UTF-8 text across all pages ready for Agent 1 extraction."
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Detailed diagnostic error message when status is not SUCCESS."
    )


class DocumentValidationResult(BaseModel):
    """Validation outcome from security and magic byte inspection."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    is_valid: bool
    detected_mime: str
    detected_type: OCRDocumentType
    file_size_bytes: int
    sanitized_filename: str
    error_message: Optional[str] = None
