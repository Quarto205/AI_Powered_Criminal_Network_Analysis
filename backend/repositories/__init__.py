"""
Repositories package for SIH26189 backend.
Authoritative data access and domain operations layer.
"""

from backend.repositories.audit_repository import AuditRepository
from backend.repositories.document_repository import (
    CaseIsolationViolationError,
    DocumentNotFoundError,
    DocumentRepository,
    DocumentRepositoryError,
    DuplicateDocumentError,
)
from backend.repositories.evidence_repository import (
    EvidenceRepository,
    parse_character_span,
)
from backend.repositories.export_repository import ExportRepository
from backend.repositories.review_repository import ReviewRepository
from backend.repositories.storage import (
    BaseDocumentStorage,
    InMemoryDocumentStorage,
    StorageError,
    StorageNotFoundError,
)

__all__ = [
    # Domain Repositories
    "EvidenceRepository",
    "ReviewRepository",
    "AuditRepository",
    "ExportRepository",
    "DocumentRepository",
    "parse_character_span",
    # Storage
    "BaseDocumentStorage",
    "InMemoryDocumentStorage",
    # Errors
    "CaseIsolationViolationError",
    "DocumentNotFoundError",
    "DocumentRepositoryError",
    "DuplicateDocumentError",
    "StorageError",
    "StorageNotFoundError",
]
