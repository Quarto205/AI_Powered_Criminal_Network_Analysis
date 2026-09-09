"""
Security and validation utilities for document parsing and OCR.
Guarantees magic byte inspection, path traversal prevention, and resource limit enforcement.
"""

import os
import re
from pathlib import Path
from typing import Tuple

from agents.extraction.ocr.exceptions import (
    PathTraversalError,
    ResourceLimitExceededError,
    UnsupportedFormatError,
)
from agents.extraction.ocr.schemas import (
    DocumentValidationResult,
    OCRDocumentType,
)

# Magic bytes signatures
SIGNATURE_PDF = b"%PDF-"
SIGNATURE_PNG = b"\x89PNG\r\n\x1a\n"
SIGNATURE_JPEG = b"\xFF\xD8\xFF"

# Default Resource Limits
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DEFAULT_MAX_PDF_PAGES = 100
DEFAULT_MAX_IMAGE_DIMENSION = 10000  # 10,000 px


def inspect_file_signature(data: bytes) -> Tuple[OCRDocumentType, str]:
    """
    Inspects leading bytes of a binary payload to detect true MIME type and document type.
    Never relies on file extensions.
    """
    if len(data) < 4:
        raise UnsupportedFormatError("File payload is empty or too short for signature inspection.")

    if data.startswith(SIGNATURE_PDF):
        return OCRDocumentType.DIGITAL_PDF, "application/pdf"
    elif data.startswith(SIGNATURE_PNG):
        return OCRDocumentType.IMAGE_PNG, "image/png"
    elif data.startswith(SIGNATURE_JPEG):
        return OCRDocumentType.IMAGE_JPEG, "image/jpeg"

    raise UnsupportedFormatError(
        f"File magic bytes do not match permitted document types (PDF, PNG, JPEG). First bytes: {data[:8]!r}"
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes raw user filename and rejects path traversal attempts.
    """
    if not filename:
        return "unnamed_document"

    # Detect directory traversal
    if ".." in filename or "/" in filename or "\\" in filename or "\x00" in filename:
        raise PathTraversalError(f"Potential directory traversal sequence detected in filename: '{filename}'")

    # Extract base name and strip dangerous characters
    base = os.path.basename(filename).strip()
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    if not clean or clean.startswith("."):
        return f"doc_{clean}" if clean else "unnamed_document"
    return clean


def validate_document_security(
    data: bytes,
    original_filename: str,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
) -> DocumentValidationResult:
    """
    Defensively validates file payload size, magic bytes signature, and filename sanity.
    """
    if len(data) == 0:
        return DocumentValidationResult(
            is_valid=False,
            detected_mime="application/octet-stream",
            detected_type=OCRDocumentType.UNKNOWN,
            file_size_bytes=0,
            sanitized_filename="empty",
            error_message="Document payload is empty (0 bytes).",
        )

    # 1. Enforce file size limit
    if len(data) > max_file_size:
        raise ResourceLimitExceededError(
            f"File size {len(data)} bytes exceeds maximum allowed limit {max_file_size} bytes."
        )

    # 2. Path sanitization
    clean_name = sanitize_filename(original_filename)

    # 3. Magic byte inspection
    try:
        doc_type, mime = inspect_file_signature(data)
    except UnsupportedFormatError as exc:
        return DocumentValidationResult(
            is_valid=False,
            detected_mime="application/octet-stream",
            detected_type=OCRDocumentType.UNKNOWN,
            file_size_bytes=len(data),
            sanitized_filename=clean_name,
            error_message=str(exc),
        )

    # 4. Check extension consistency if present
    ext = Path(clean_name).suffix.lower()
    if ext in [".pdf"] and mime != "application/pdf":
        raise UnsupportedFormatError(f"Extension '{ext}' does not match detected MIME type '{mime}'.")
    if ext in [".png"] and mime != "image/png":
        raise UnsupportedFormatError(f"Extension '{ext}' does not match detected MIME type '{mime}'.")
    if ext in [".jpg", ".jpeg"] and mime != "image/jpeg":
        raise UnsupportedFormatError(f"Extension '{ext}' does not match detected MIME type '{mime}'.")

    return DocumentValidationResult(
        is_valid=True,
        detected_mime=mime,
        detected_type=doc_type,
        file_size_bytes=len(data),
        sanitized_filename=clean_name,
        error_message=None,
    )
