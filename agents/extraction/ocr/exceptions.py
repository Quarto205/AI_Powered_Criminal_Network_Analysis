"""
Domain exceptions for OCR Preprocessor and Document Text Extraction Engine.
"""

class OCRError(Exception):
    """Base exception for all OCR and document parsing errors."""
    pass


class UnsupportedFormatError(OCRError):
    """Raised when file format is not supported or does not match permitted types."""
    pass


class CorruptedFileError(OCRError):
    """Raised when binary file payload is corrupted or structurally unreadable."""
    pass


class PasswordProtectedError(OCRError):
    """Raised when a document is password-protected or encrypted."""
    pass


class EmptyDocumentError(OCRError):
    """Raised when document contains no extractable text or renderable pages."""
    pass


class OCREngineFailureError(OCRError):
    """Raised when underlying OCR engine fails to process image content."""
    pass


class ResourceLimitExceededError(OCRError):
    """Raised when file size, page count, or dimensions exceed security limits."""
    pass


class PathTraversalError(OCRError):
    """Raised when a filename or path contains dangerous directory traversal patterns."""
    pass
