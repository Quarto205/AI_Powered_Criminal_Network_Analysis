"""
Audit Repository for SIH26189.
Authoritative, append-only operational ledger access layer.
Enforces strict case boundary isolation, PII masking, token redaction,
and absolute immutability (updates and deletes are prohibited).
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.models.analytics import AuditLog
from backend.domain.errors import (
    CaseIsolationViolationError,
    ImmutableRecordViolationError,
)
from backend.domain.redaction import redact_sensitive_text

logger = logging.getLogger("backend.repositories.audit_repository")


class AuditRepository:
    """
    Append-only repository managing operational security and compliance audit logs.
    Guarantees:
    1. Append-only persistence: updates and deletions are strictly blocked.
    2. Case isolation: all retrieval queries require explicit case_id.
    3. Privacy defense: PII masking and secret/token redaction on write.
    """

    def __init__(self, session: Session):
        self.session = session

    def append_audit_event(
        self,
        actor_uuid: UUID,
        action_code: str,
        case_id: Optional[UUID] = None,
        target_item: Optional[str] = None,
        outcome: str = "SUCCESS",
    ) -> AuditLog:
        """
        Appends an immutable audit log entry.
        Applies PII and secret redaction to target_item before database write.
        """
        sanitized_target = redact_sensitive_text(target_item[:255] if target_item else None)

        audit_entry = AuditLog(
            audit_id=uuid4(),
            actor_uuid=actor_uuid,
            action_code=action_code.strip().upper(),
            case_id=case_id,
            target_item=sanitized_target,
            timestamp=datetime.now(timezone.utc),
            outcome=outcome.strip().upper(),
        )
        self.session.add(audit_entry)
        self.session.commit()
        self.session.refresh(audit_entry)
        return audit_entry

    def list_case_audit_logs(
        self,
        case_id: UUID,
        user_id: Optional[UUID] = None,
        action_code: Optional[str] = None,
        timestamp_start: Optional[datetime] = None,
        timestamp_end: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[AuditLog], int]:
        """
        Retrieves case-scoped audit logs matching query filters.
        Strictly enforces WHERE case_id = :case_id.
        Returns a tuple of (matching_logs, total_matching_count).
        """
        query = self.session.query(AuditLog).filter(AuditLog.case_id == case_id)

        if user_id:
            query = query.filter(AuditLog.actor_uuid == user_id)

        if action_code:
            query = query.filter(AuditLog.action_code == action_code.strip().upper())

        if timestamp_start:
            query = query.filter(AuditLog.timestamp >= timestamp_start)

        if timestamp_end:
            query = query.filter(AuditLog.timestamp <= timestamp_end)

        total = query.count()
        logs = (
            query.order_by(AuditLog.timestamp.desc(), AuditLog.audit_id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return logs, total

    def update_audit_log(self, *args, **kwargs) -> None:
        """Prohibited: audit records are strictly immutable and append-only."""
        raise ImmutableRecordViolationError("Audit records are strictly append-only; update operations are prohibited.")

    def delete_audit_log(self, *args, **kwargs) -> None:
        """Prohibited: audit records are strictly immutable and append-only."""
        raise ImmutableRecordViolationError("Audit records are strictly append-only; deletion operations are prohibited.")
