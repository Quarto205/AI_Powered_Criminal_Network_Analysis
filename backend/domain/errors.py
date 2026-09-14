"""
Domain exceptions for SIH26189.
Encapsulates business rule violations, case boundary breaches,
and immutability constraints.
"""


class DomainError(Exception):
    """Base exception for all domain logic violations."""
    pass


class CaseIsolationViolationError(DomainError):
    """Raised when an operation attempts to read or mutate data across case boundaries."""
    pass


class ImmutableRecordViolationError(DomainError):
    """Raised when an operation attempts to update or delete append-only immutable records."""
    pass


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist in the specified case."""
    pass


class RelationshipNotFoundError(DomainError):
    """Raised when a requested relationship does not exist in the specified case."""
    pass


class DuplicateMergeError(DomainError):
    """Raised when an entity merge target is already merged or invalid."""
    pass


class InvalidReviewActionError(DomainError):
    """Raised when a review override request specifies an illegal state transition."""
    pass
