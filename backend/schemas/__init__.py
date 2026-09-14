"""
Backend schemas package for SIH26189.
Exports domain DTOs, API envelopes, and audit/export contracts.
"""

from backend.schemas.audit import (
    AuditCreate,
    AuditFilterParams,
    AuditLogItem,
    CaseAuditResponse,
)
from backend.schemas.document_jobs import (
    DocumentRecord,
    DocumentState,
    DocumentTaskRequest,
    DocumentTaskResult,
)
from backend.schemas.envelope import (
    ApiErrorDetail,
    ApiErrorResponse,
    ApiResponse,
    ApiSuccessResponse,
    ErrorCodes,
    envelope_error,
    envelope_success,
)
from backend.schemas.evidence_analysis import (
    AlertFilterParams,
    AlertItem,
    CaseAlertsResponse,
    EntityAliasInfo,
    EntityDetailResponse,
    EntityIdentifierInfo,
    EvidenceCitation,
    EvidenceDetailResponse,
    ProvenanceSpan,
    RelationshipDetailResponse,
    RelationshipEndpointSummary,
    ReviewAction,
    ReviewRequest,
    ReviewResponse,
    ReviewTargetType,
    RiskScoreInfo,
)
from backend.schemas.export import (
    ExportCreate,
    ExportFormat,
    ExportRequest,
    ExportResponse,
)

__all__ = [
    # Envelopes
    "ApiResponse",
    "ApiSuccessResponse",
    "ApiErrorResponse",
    "ApiErrorDetail",
    "ErrorCodes",
    "envelope_success",
    "envelope_error",
    # Documents
    "DocumentRecord",
    "DocumentState",
    "DocumentTaskRequest",
    "DocumentTaskResult",
    # Evidence & Review
    "EvidenceDetailResponse",
    "EvidenceCitation",
    "ProvenanceSpan",
    "EntityDetailResponse",
    "EntityAliasInfo",
    "EntityIdentifierInfo",
    "RelationshipDetailResponse",
    "RelationshipEndpointSummary",
    "ReviewRequest",
    "ReviewResponse",
    "ReviewTargetType",
    "ReviewAction",
    "RiskScoreInfo",
    "AlertItem",
    "CaseAlertsResponse",
    "AlertFilterParams",
    # Audit
    "AuditLogItem",
    "CaseAuditResponse",
    "AuditFilterParams",
    "AuditCreate",
    # Export
    "ExportFormat",
    "ExportRequest",
    "ExportResponse",
    "ExportCreate",
]
