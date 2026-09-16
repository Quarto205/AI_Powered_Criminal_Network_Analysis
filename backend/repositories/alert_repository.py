"""
Alert Repository for SIH26189.
Authoritative data access layer for persisting pattern detection alerts.
Enforces case boundaries and deterministic deduplication to ensure idempotent execution.
"""

from typing import List, Optional, Any, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB

from backend.db.models.analytics import Alert
from backend.domain.errors import CaseIsolationViolationError


class AlertRepository:
    """
    Manages persistence and deduplication of analytical pattern alerts.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_alert_by_id(self, case_id: UUID, alert_id: UUID) -> Optional[Alert]:
        """
        Retrieves a single alert strictly scoped to case_id.
        """
        return (
            self.session.query(Alert)
            .filter(Alert.case_id == case_id, Alert.alert_id == alert_id)
            .first()
        )

    def list_case_alerts(self, case_id: UUID, limit: int = 100, offset: int = 0) -> List[Alert]:
        """
        Lists alerts within the specified case boundary.
        """
        return (
            self.session.query(Alert)
            .filter(Alert.case_id == case_id)
            .order_by(Alert.created_at.desc(), Alert.alert_id)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def _check_duplicate(
        self, case_id: UUID, rule_id: str, fingerprint: str
    ) -> bool:
        """
        Checks if an alert with the same exact fingerprint already exists for this case/rule.
        """
        existing = (
            self.session.query(Alert.alert_id)
            .filter(
                Alert.case_id == case_id,
                Alert.rule_id == rule_id,
                Alert.metadata_['fingerprint'].astext == fingerprint
            )
            .first()
        )
        return existing is not None

    def save_alerts_idempotent(self, case_id: UUID, alert_candidates: List[Dict[str, Any]]) -> List[Alert]:
        """
        Persists new alerts. Silently skips duplicates based on the deterministic fingerprint.
        alert_candidates should be dictionaries containing the required fields.
        """
        new_alerts = []
        for cand in alert_candidates:
            rule_id = cand["rule_id"]
            metadata = cand.get("metadata_", {})
            fingerprint = metadata.get("fingerprint")

            if not fingerprint:
                raise ValueError("Alert candidate is missing a deterministic fingerprint in metadata_.")

            if self._check_duplicate(case_id, rule_id, fingerprint):
                continue

            alert = Alert(
                case_id=case_id,
                alert_type=cand["alert_type"],
                severity=cand["severity"],
                rule_id=rule_id,
                contributing_entities=cand["contributing_entities"],
                status=cand.get("status", "NEW"),
                metadata_=metadata,
            )
            self.session.add(alert)
            new_alerts.append(alert)

        if new_alerts:
            self.session.commit()
            for a in new_alerts:
                self.session.refresh(a)

        return new_alerts
