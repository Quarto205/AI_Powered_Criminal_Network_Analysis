"""
Security and authentication package for SIH26189.
"""

from backend.security.password import dummy_verify, hash_password, verify_password
from backend.security.tokens import (
    TokenClaimsError,
    TokenExpiredError,
    TokenSecurityError,
    TokenTamperedError,
    create_access_token,
    decode_access_token,
)
from backend.security.rbac import (
    INVESTIGATOR_PERMISSIONS,
    ANALYST_PERMISSIONS,
    SUPERVISOR_PERMISSIONS,
    Permissions,
    SystemRoles,
    get_permissions_for_roles,
    has_permission,
)
from backend.security.audit import SecurityAuditAction, record_security_event
from backend.security.redaction import (
    SensitiveDataFilter,
    apply_logging_redaction,
    redact_sensitive_text,
)

__all__ = [
    "hash_password",
    "verify_password",
    "dummy_verify",
    "create_access_token",
    "decode_access_token",
    "TokenSecurityError",
    "TokenExpiredError",
    "TokenTamperedError",
    "TokenClaimsError",
    "Permissions",
    "SystemRoles",
    "INVESTIGATOR_PERMISSIONS",
    "ANALYST_PERMISSIONS",
    "SUPERVISOR_PERMISSIONS",
    "get_permissions_for_roles",
    "has_permission",
    "SecurityAuditAction",
    "record_security_event",
    "SensitiveDataFilter",
    "redact_sensitive_text",
    "apply_logging_redaction",
]
