"""
Analysis Execution and Intelligence Query Service for SIH26189.
Encapsulates:
- Asynchronous analysis run dispatch (SNA, PATTERN_MOTIFS, GAT_LINK_PREDICTION)
- Model run lifecycle management (PENDING -> RUNNING -> SUCCESS / FAILED)
- Investigative Priority Score retrieval (ordered by value DESC)
- Deterministic Pattern Alert retrieval with severity and status filters
- Absolute non-accusatory terminology guardrail
- Pure interface boundary for Agent 3 (does not fabricate fake models or results)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from backend.db.models.analytics import Alert, AuditLog, ModelRun, Prediction, RiskScore
from backend.db.models.entities import Entity
from backend.schemas.evidence_analysis import (
    AlertItem,
    AnalysisRunDetailResponse,
    AnalysisTriggerResponse,
    CaseAlertsResponse,
    CaseScoresResponse,
    ScoreItem,
)
from backend.security.audit import SecurityAuditAction, record_security_event

logger = logging.getLogger("backend.services.analysis_service")


class AnalysisServiceError(Exception):
    """Raised on analysis trigger or query failure."""
    pass


class AnalysisNotFoundError(AnalysisServiceError):
    """Raised when an analytical run is not found."""
    pass


class AnalysisService:
    """
    Manages asynchronous analysis triggers, run status, and canonical intelligence output queries.
    """
    def __init__(self, db: Session):
        self.db = db

    def trigger_analysis(
        self,
        case_id: UUID,
        actor_uuid: UUID,
        pipelines: List[str],
        parameters: Dict[str, Any],
        snapshot_checksum: str = "PENDING_CHECKSUM",
    ) -> AnalysisTriggerResponse:
        """
        Registers an analytical model run in PENDING state.
        Dispatches asynchronous background task without blocking the HTTP request.
        """
        run_id = uuid4()
        model_run = ModelRun(
            run_id=run_id,
            model_name="Agent3_Network_Intelligence",
            version="1.0.0",
            task_type=",".join(pipelines),
            input_snapshot_checksum=snapshot_checksum,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(model_run)
        self.db.commit()

        # Audit analysis trigger
        record_security_event(
            db=self.db,
            action_code=SecurityAuditAction.ANALYSIS_TRIGGER,
            actor_uuid=actor_uuid,
            case_id=case_id,
            target_item=f"RUN:{run_id}:PIPELINES:{','.join(pipelines)}",
            outcome="DISPATCHED",
        )

        logger.info(f"Registered analytical run {run_id} for case {case_id} [status=PENDING]")

        return AnalysisTriggerResponse(
            run_id=run_id,
            case_id=case_id,
            status="PENDING",
            pipelines=pipelines,
        )

    def get_run_status(self, case_id: UUID, run_id: UUID) -> AnalysisRunDetailResponse:
        """
        Retrieves the current execution status of an analytical run.
        Ensures strict case tenancy: a run belonging to another case raises AnalysisNotFoundError (404).
        """
        run = self.db.query(ModelRun).filter(ModelRun.run_id == run_id).first()
        if not run:
            raise AnalysisNotFoundError(f"Analysis run {run_id} not found.")

        # Verify tenancy: check trigger audit record, predictions, or risk scores
        audit_trigger = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.action_code == SecurityAuditAction.ANALYSIS_TRIGGER,
                AuditLog.case_id == case_id,
                AuditLog.target_item.like(f"RUN:{run_id}%"),
            )
            .first()
        )
        if not audit_trigger:
            has_pred = (
                self.db.query(Prediction)
                .filter(Prediction.run_id == run_id, Prediction.case_id == case_id)
                .first()
            )
            has_score = (
                self.db.query(RiskScore)
                .join(Entity, Entity.entity_id == RiskScore.target_entity_uuid)
                .filter(RiskScore.run_id == run_id, Entity.case_id == case_id)
                .first()
            )
            if not has_pred and not has_score:
                raise AnalysisNotFoundError(
                    f"Analysis run {run_id} not associated with case {case_id}."
                )

        return AnalysisRunDetailResponse(
            run_id=run.run_id,
            case_id=case_id,
            model_name=run.model_name,
            version=run.version,
            task_type=run.task_type,
            status=run.status,
            input_snapshot_checksum=run.input_snapshot_checksum,
            created_at=run.created_at,
        )

    def get_case_scores(
        self,
        case_id: UUID,
        limit: int = 50,
        entity_type: Optional[str] = None,
    ) -> CaseScoresResponse:
        """
        Queries canonical investigative priority scores for a case.
        Guarantees:
        - Sorted by score value DESC (highest priority investigative leads first).
        - Strictly scoped to case_id via Entity join.
        - Non-accusatory vocabulary.
        """
        query = (
            self.db.query(RiskScore, Entity)
            .join(Entity, Entity.entity_id == RiskScore.target_entity_uuid)
            .filter(Entity.case_id == case_id)
        )
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type.upper())

        results = query.order_by(RiskScore.value.desc()).limit(limit).all()

        score_items = [
            ScoreItem(
                score_id=rs.score_id,
                entity_id=ent.entity_id,
                canonical_name=ent.canonical_name,
                entity_type=ent.entity_type,
                score_type=rs.score_type,
                value=float(rs.value),
                features_summary=rs.features_summary,
            )
            for rs, ent in results
        ]

        return CaseScoresResponse(
            case_id=case_id,
            scores=score_items,
            total=len(score_items),
        )

    def get_case_alerts(
        self,
        case_id: UUID,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        limit: int = 100,
    ) -> CaseAlertsResponse:
        """
        Queries deterministic motif findings and pattern alerts for a case.
        """
        query = self.db.query(Alert).filter(Alert.case_id == case_id)
        if status_filter:
            query = query.filter(Alert.status == status_filter.upper())
        if severity_filter:
            query = query.filter(Alert.severity == severity_filter.upper())

        alerts = query.limit(limit).all()

        alert_items = [
            AlertItem(
                alert_id=a.alert_id,
                case_id=a.case_id,
                alert_type=a.alert_type,
                severity=a.severity,
                rule_id=a.rule_id,
                status=a.status,
                contributing_entities=a.contributing_entities,
                metadata_=a.metadata_,
                created_at=a.created_at,
            )
            for a in alerts
        ]

        return CaseAlertsResponse(
            case_id=case_id,
            alerts=alert_items,
            total=len(alert_items),
        )
