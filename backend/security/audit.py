"""
Security audit logging service for SIH26189.
Records security-relevant events directly to the immutable audit_logs database ledger.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from backend.db.models.analytics import AuditLog

logger = logging.getLogger("security.audit")


class SecurityAuditAction:
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILURE = "AUTH_LOGIN_FAILURE"
    CASE_ACCESS_DENIED = "CASE_ACCESS_DENIED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    GRAPH_REBUILD = "GRAPH_REBUILD"
    REVIEW_OVERRIDE = "REVIEW_OVERRIDE"
    ANALYSIS_TRIGGER = "ANALYSIS_TRIGGER"


def record_security_event(
    db: Optional[Session],
    action_code: str,
    actor_uuid: Optional[UUID] = None,
    case_id: Optional[UUID] = None,
    target_item: Optional[str] = None,
    outcome: str = "DENIED",
) -> Optional[AuditLog]:
    """
    Records a security event.
    If actor_uuid is a valid UUID and db session is provided, persists an immutable row
    to the PostgreSQL audit_logs table.
    If actor_uuid is None (e.g. unknown username during login attempt), safely logs to the
    secure application security logger to prevent foreign key integrity violations without
    inventing fake user records.
    Never stores plaintext passwords, tokens, or sensitive credentials.
    """
    sanitized_target = target_item[:255] if target_item else None
    timestamp = datetime.now(timezone.utc)

    # Always log to structured security log stream
    logger.info(
        f"SECURITY_EVENT: action={action_code} actor={actor_uuid} case={case_id} "
        f"target={sanitized_target} outcome={outcome} timestamp={timestamp.isoformat()}"
    )

    if db is None:
        return None

    # Database audit_logs table requires actor_uuid (FK to users.user_id).
    # If actor_uuid is not available (e.g. unknown user authentication failure),
    # we do not attempt DB insertion to respect referential integrity.
    if actor_uuid is None:
        return None

    try:
        log_entry = AuditLog(
            audit_id=uuid4(),
            actor_uuid=actor_uuid,
            action_code=action_code,
            case_id=case_id,
            target_item=sanitized_target,
            timestamp=timestamp,
            outcome=outcome,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist security audit log entry: {str(e)}")
        # Raise error to prevent silent failure of security-critical auditing where required
        raise
