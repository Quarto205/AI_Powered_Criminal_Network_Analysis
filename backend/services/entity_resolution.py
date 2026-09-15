"""
Entity Resolution Service for SIH26189.
Orchestrates Phase 3 Entity Resolution, threshold evaluation, review candidate management,
server-side case isolation, and background graph projection.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from agents.evidence.resolution import (
    EntityResolutionEngine,
    EntityResolutionResult,
    ResolutionBatchResult,
    resolve_and_stage_payload,
)
from agents.extraction.schemas import ExtractionJobResponse
from backend.db.models.entities import Entity, EntityAlias, EntityIdentifier
from backend.db.models.identity import Case, CaseMember
from backend.schemas.evidence_analysis import ReviewAction, ReviewResponse, ReviewTargetType
from backend.services.evidence_review import EvidenceReviewService
from backend.services.graph_projection import GraphProjectionService

logger = logging.getLogger("sih26189.backend.services.entity_resolution")


class EntityResolutionService:
    """
    Service layer for case-scoped entity resolution, review workflows,
    and threshold-gated merges.
    """

    def __init__(
        self,
        db: Session,
        graph_projection: Optional[GraphProjectionService] = None,
        review_service: Optional[EvidenceReviewService] = None,
    ):
        self.db = db
        self.graph_projection = graph_projection or GraphProjectionService(db=db)
        self.review_service = review_service or EvidenceReviewService(
            db=db,
            graph_projection_service=self.graph_projection,
        )

    def verify_case_access(self, case_id: UUID, user_id: Optional[UUID] = None) -> Case:
        """
        Verifies that the case exists and is active.
        If user_id is supplied, verifies active case membership.
        Returns 404 Not Found to prevent case enumeration.
        """
        case = self.db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        if user_id:
            membership = (
                self.db.query(CaseMember)
                .filter(CaseMember.case_id == case_id, CaseMember.user_id == user_id)
                .first()
            )
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resource not found.",
                )

        return case

    def stage_and_resolve(
        self,
        case_id: UUID,
        document_id: UUID,
        payload: ExtractionJobResponse,
        actor_id: Optional[UUID] = None,
    ) -> ResolutionBatchResult:
        """
        Executes Phase 3 Entity Resolution on an Agent 1 payload within a database transaction.
        Enforces case isolation and triggers background graph sync.
        """
        self.verify_case_access(case_id=case_id, user_id=actor_id)

        result = resolve_and_stage_payload(
            db_session=self.db,
            payload=payload,
            case_id=case_id,
            document_id=document_id,
            actor_id=actor_id,
        )

        # Trigger graph projection rebuild if canonical entities were added/merged
        if result.auto_merge_count > 0 or result.create_new_count > 0:
            try:
                self.graph_projection.rebuild_case_graph(case_id=case_id)
            except Exception as e:
                logger.warning(
                    "Graph projection trigger failed for case %s (non-blocking): %s",
                    case_id,
                    e,
                )

        return result

    def get_review_candidates(self, case_id: UUID, user_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all entities in the case currently quarantined in REVIEW_REQUIRED state,
        including provenance citations and candidate match info.
        """
        self.verify_case_access(case_id=case_id, user_id=user_id)

        review_entities = (
            self.db.query(Entity)
            .filter(Entity.case_id == case_id, Entity.status == "REVIEW_REQUIRED")
            .all()
        )

        candidates_out = []
        for e in review_entities:
            alias = self.db.query(EntityAlias).filter(EntityAlias.entity_id == e.entity_id).first()
            candidates_out.append({
                "entity_id": str(e.entity_id),
                "case_id": str(e.case_id),
                "entity_type": e.entity_type,
                "canonical_name": e.canonical_name,
                "status": e.status,
                "provenance_ref": alias.source_ref if alias else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            })

        return candidates_out

    def approve_merge(
        self,
        case_id: UUID,
        primary_entity_id: UUID,
        secondary_entity_id: UUID,
        actor_uuid: UUID,
        reason: str = "Approved merge override",
    ) -> ReviewResponse:
        """
        Supervisory approval of an entity merge.
        Integrates directly with EvidenceReviewService.
        """
        self.verify_case_access(case_id=case_id, user_id=actor_uuid)
        return self.review_service.apply_review_override(
            case_id=case_id,
            actor_uuid=actor_uuid,
            target_type=ReviewTargetType.ENTITY,
            target_id=primary_entity_id,
            action=ReviewAction.MERGE,
            reason=reason,
            secondary_target_id=secondary_entity_id,
        )

    def reject_entity(
        self,
        case_id: UUID,
        entity_id: UUID,
        actor_uuid: UUID,
        reason: str = "Rejected entity candidate",
    ) -> ReviewResponse:
        """
        Supervisory rejection of an entity candidate.
        """
        self.verify_case_access(case_id=case_id, user_id=actor_uuid)
        return self.review_service.apply_review_override(
            case_id=case_id,
            actor_uuid=actor_uuid,
            target_type=ReviewTargetType.ENTITY,
            target_id=entity_id,
            action=ReviewAction.REJECT,
            reason=reason,
        )

    def confirm_entity(
        self,
        case_id: UUID,
        entity_id: UUID,
        actor_uuid: UUID,
        reason: str = "Confirmed standalone entity",
    ) -> ReviewResponse:
        """
        Supervisory confirmation of an entity as standalone/active.
        """
        self.verify_case_access(case_id=case_id, user_id=actor_uuid)
        return self.review_service.apply_review_override(
            case_id=case_id,
            actor_uuid=actor_uuid,
            target_type=ReviewTargetType.ENTITY,
            target_id=entity_id,
            action=ReviewAction.CONFIRM,
            reason=reason,
        )
