"""
Domain exceptions for Agent 1: Intelligence Extraction Engine.
"""

class ExtractionBaseError(Exception):
    """Base exception for all extraction errors."""
    pass


class SchemaValidationError(ExtractionBaseError):
    """Raised when extracted payload fails Pydantic or schema integrity constraints."""
    pass


class SourceSpanMismatchError(ExtractionBaseError):
    """Raised when extracted entity character offsets do not match the source text."""
    pass


class ReferentialIntegrityError(ExtractionBaseError):
    """Raised when relationship refers to non-existent entity temp_ids."""
    pass


class ProviderUnavailableError(ExtractionBaseError):
    """Raised when external AI provider is offline or unreachable."""
    pass


class PromptInjectionAttemptError(ExtractionBaseError):
    """Raised when a severe injection attempt is detected that cannot be safely processed."""
    pass
