"""
OCR Preprocessor and Document Text Extraction Package.
"""

from agents.extraction.ocr.exceptions import (
    CorruptedFileError,
    EmptyDocumentError,
    OCREngineFailureError,
    OCRError,
    PasswordProtectedError,
    PathTraversalError,
    ResourceLimitExceededError,
    UnsupportedFormatError,
)
from agents.extraction.ocr.preprocessor import OCRPreprocessor, clean_utf8_text
from agents.extraction.ocr.providers import (
    MockOCRProvider,
    OCRProvider,
    PaddleOCRAdapter,
)
from agents.extraction.ocr.schemas import (
    DocumentValidationResult,
    OCRDocumentResult,
    OCRDocumentType,
    OCRPageResult,
    OCRProcessingStatus,
)
from agents.extraction.ocr.security import (
    DEFAULT_MAX_FILE_SIZE,
    DEFAULT_MAX_IMAGE_DIMENSION,
    DEFAULT_MAX_PDF_PAGES,
    inspect_file_signature,
    sanitize_filename,
    validate_document_security,
)

__all__ = [
    "OCRPreprocessor",
    "clean_utf8_text",
    "OCRProvider",
    "MockOCRProvider",
    "PaddleOCRAdapter",
    "OCRDocumentType",
    "OCRProcessingStatus",
    "OCRPageResult",
    "OCRDocumentResult",
    "DocumentValidationResult",
    "OCRError",
    "UnsupportedFormatError",
    "CorruptedFileError",
    "PasswordProtectedError",
    "EmptyDocumentError",
    "OCREngineFailureError",
    "ResourceLimitExceededError",
    "PathTraversalError",
    "validate_document_security",
    "inspect_file_signature",
    "sanitize_filename",
    "DEFAULT_MAX_FILE_SIZE",
    "DEFAULT_MAX_PDF_PAGES",
    "DEFAULT_MAX_IMAGE_DIMENSION",
]
