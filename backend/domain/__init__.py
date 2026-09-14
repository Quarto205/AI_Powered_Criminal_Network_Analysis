"""
Domain package for SIH26189.
Exports business exceptions and domain security logic.
"""

from backend.domain.errors import (
    CaseIsolationViolationError,
    DomainError,
    DuplicateMergeError,
    EntityNotFoundError,
    ImmutableRecordViolationError,
    InvalidReviewActionError,
    RelationshipNotFoundError,
)
from backend.domain.redaction import redact_sensitive_text

__all__ = [
    "DomainError",
    "CaseIsolationViolationError",
    "ImmutableRecordViolationError",
    "EntityNotFoundError",
    "RelationshipNotFoundError",
    "DuplicateMergeError",
    "InvalidReviewActionError",
    "redact_sensitive_text",
]
