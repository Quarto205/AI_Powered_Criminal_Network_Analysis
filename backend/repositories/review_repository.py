"""
Review and Entity Resolution Repository for SIH26189.
Manages human-in-the-loop overrides, entity merge confirmations, and merge rejections.
Enforces strict case boundaries, raw source immutability, transactional safety,
and automatic audit recording.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.db.models.analytics import AuditLog
from backend.db.models.entities import Entity, EntityAlias, EntityIdentifier, Relationship
from backend.domain.errors import (
    CaseIsolationViolationError,
    DuplicateMergeError,
    EntityNotFoundError,
    InvalidReviewActionError,
    RelationshipNotFoundError,
)
from backend.domain.redaction import redact_sensitive_text
from backend.schemas.evidence_analysis import (
    ReviewAction,
    ReviewRequest,
    ReviewResponse,
    ReviewTargetType,
)

logger = logging.getLogger("backend.repositories.review_repository")


class ReviewRepository:
    """
    Authoritative repository executing human review overrides and entity merges.
    Guarantees:
    1. Strict case isolation for all operations.
    2. Zero mutation of raw documents, document chunks, or historical evidence.
    3. Transaction-safe atomic execution (rollback on any failure).
    4. Synchronous append-only audit trail logging.
    """

    def __init__(self, session: Session):
        self.session = session

    def confirm_entity_merge(
        self,
        case_id: UUID,
        target_entity_id: UUID,
        secondary_entity_id: UUID,
        actor_uuid: UUID,
        reason: Optional[str] = None,
        override_notes: Optional[str] = None,
    ) -> ReviewResponse:
        """
        Confirms merging secondary_entity into target_entity.
        - Verifies both entities belong to case_id.
        - Appends secondary's canonical name as an alias on target (preventing duplicates).
        - Re-points secondary's aliases and identifiers to target entity.
        - Re-points relationships and archives self-loops.
        - Marks secondary entity status as 'MERGED'.
        - Raw source artifacts/chunks remain untouched.
        - Records audit event atomically.
        """
        justification = override_notes or reason or "Entity merge confirmed by human reviewer"

        if target_entity_id == secondary_entity_id:
            raise DuplicateMergeError("Cannot merge an entity into itself.")

        # 1. Look up target entity within case
        target = (
            self.session.query(Entity)
            .filter(Entity.entity_id == target_entity_id, Entity.case_id == case_id)
            .first()
        )
        if not target:
            raise EntityNotFoundError(f"Target entity {target_entity_id} not found in case {case_id}.")

        # 2. Look up secondary entity within case
        secondary = (
            self.session.query(Entity)
            .filter(Entity.entity_id == secondary_entity_id, Entity.case_id == case_id)
            .first()
        )
        if not secondary:
            raise EntityNotFoundError(f"Secondary entity {secondary_entity_id} not found in case {case_id}.")

        if secondary.status == "MERGED":
            raise DuplicateMergeError(f"Secondary entity {secondary_entity_id} is already merged.")

        try:
            # 3. Absorb secondary's canonical name as an alias on target (prevent duplicate)
            existing_alias_texts = {
                a.alias_text.strip().lower()
                for a in self.session.query(EntityAlias).filter(EntityAlias.entity_id == target_entity_id).all()
            }
            if secondary.canonical_name.strip().lower() not in existing_alias_texts:
                new_alias = EntityAlias(
                    alias_id=uuid4(),
                    entity_id=target_entity_id,
                    alias_text=secondary.canonical_name,
                    source_ref=f"MERGE_FROM:{secondary_entity_id}",
                )
                self.session.add(new_alias)
                existing_alias_texts.add(secondary.canonical_name.strip().lower())

            # 4. Re-point secondary's existing aliases to target (deduplicating)
            for alias in secondary.aliases:
                if alias.alias_text.strip().lower() not in existing_alias_texts:
                    alias.entity_id = target_entity_id
                    existing_alias_texts.add(alias.alias_text.strip().lower())
                else:
                    # Duplicate alias text already on target, delete secondary's duplicate alias record
                    self.session.delete(alias)

            # 5. Re-point identifiers from secondary to target
            for ident in secondary.identifiers:
                ident.entity_id = target_entity_id

            # 6. Re-point outgoing relationships
            outgoing_rels = (
                self.session.query(Relationship)
                .filter(
                    Relationship.source_entity_uuid == secondary_entity_id,
                    Relationship.case_id == case_id,
                )
                .all()
            )
            for r in outgoing_rels:
                if r.target_entity_uuid == target_entity_id:
                    r.status = "MERGED_SELF_LOOP"
                else:
                    r.source_entity_uuid = target_entity_id

            # 7. Re-point incoming relationships
            incoming_rels = (
                self.session.query(Relationship)
                .filter(
                    Relationship.target_entity_uuid == secondary_entity_id,
                    Relationship.case_id == case_id,
                )
                .all()
            )
            for r in incoming_rels:
                if r.source_entity_uuid == target_entity_id:
                    r.status = "MERGED_SELF_LOOP"
                else:
                    r.target_entity_uuid = target_entity_id

            # 8. Mark secondary entity as MERGED
            secondary.status = "MERGED"

            # 9. Record atomic audit entry
            sanitized_target = redact_sensitive_text(f"MERGE: {secondary_entity_id} INTO {target_entity_id}")
            audit = AuditLog(
                audit_id=uuid4(),
                actor_uuid=actor_uuid,
                action_code="ENTITY_MERGE",
                case_id=case_id,
                target_item=sanitized_target,
                timestamp=datetime.now(timezone.utc),
                outcome="CONFIRMED",
            )
            self.session.add(audit)

            self.session.commit()

            return ReviewResponse(
                review_id=uuid4(),
                target_type=ReviewTargetType.ENTITY_RESOLUTION,
                target_id=target_entity_id,
                action=ReviewAction.CONFIRM,
                resulting_status="CONFIRMED",
                status="CONFIRMED",
                secondary_target_id=secondary_entity_id,
                applied_at=datetime.now(timezone.utc),
                reason=justification,
                override_notes=justification,
            )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Entity merge failed: {str(e)}")
            raise

    def reject_entity_merge(
        self,
        case_id: UUID,
        target_entity_id: UUID,
        secondary_entity_id: UUID,
        actor_uuid: UUID,
        reason: Optional[str] = None,
        override_notes: Optional[str] = None,
    ) -> ReviewResponse:
        """
        Rejects proposed entity merge.
        - Verifies both entities belong to case_id.
        - Preserves both entities as distinct domain objects.
        - Does NOT absorb aliases or re-point relationships.
        - Raw evidence remains unchanged.
        - Records audit entry with REJECTED outcome.
        """
        justification = override_notes or reason or "Entity merge rejected by human reviewer"

        target = (
            self.session.query(Entity)
            .filter(Entity.entity_id == target_entity_id, Entity.case_id == case_id)
            .first()
        )
        if not target:
            raise EntityNotFoundError(f"Target entity {target_entity_id} not found in case {case_id}.")

        secondary = (
            self.session.query(Entity)
            .filter(Entity.entity_id == secondary_entity_id, Entity.case_id == case_id)
            .first()
        )
        if not secondary:
            raise EntityNotFoundError(f"Secondary entity {secondary_entity_id} not found in case {case_id}.")

        try:
            sanitized_target = redact_sensitive_text(f"REJECT_MERGE: {secondary_entity_id} WITH {target_entity_id}")
            audit = AuditLog(
                audit_id=uuid4(),
                actor_uuid=actor_uuid,
                action_code="ENTITY_MERGE_REJECT",
                case_id=case_id,
                target_item=sanitized_target,
                timestamp=datetime.now(timezone.utc),
                outcome="REJECTED",
            )
            self.session.add(audit)
            self.session.commit()

            return ReviewResponse(
                review_id=uuid4(),
                target_type=ReviewTargetType.ENTITY_RESOLUTION,
                target_id=target_entity_id,
                action=ReviewAction.REJECT,
                resulting_status="REJECTED",
                status="REJECTED",
                secondary_target_id=secondary_entity_id,
                applied_at=datetime.now(timezone.utc),
                reason=justification,
                override_notes=justification,
            )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Entity merge reject failed: {str(e)}")
            raise

    def record_review_override(
        self,
        case_id: UUID,
        actor_uuid: UUID,
        review_req: ReviewRequest,
    ) -> ReviewResponse:
        """
        Dispatches a generic ReviewRequest under case isolation.
        Handles ENTITY_RESOLUTION, ENTITY, and RELATIONSHIP overrides.
        """
        target_type = review_req.target_type.upper()
        action = review_req.action.upper()
        justification = review_req.override_notes or review_req.reason or "Review override applied"

        # 1. Entity resolution merge/reject flow
        if target_type == ReviewTargetType.ENTITY_RESOLUTION or action == ReviewAction.MERGE:
            if not review_req.secondary_target_id:
                raise InvalidReviewActionError("secondary_target_id is required for entity resolution review.")
            if action in (ReviewAction.CONFIRM, ReviewAction.MERGE):
                return self.confirm_entity_merge(
                    case_id=case_id,
                    target_entity_id=review_req.target_id,
                    secondary_entity_id=review_req.secondary_target_id,
                    actor_uuid=actor_uuid,
                    reason=justification,
                    override_notes=justification,
                )
            elif action == ReviewAction.REJECT:
                return self.reject_entity_merge(
                    case_id=case_id,
                    target_entity_id=review_req.target_id,
                    secondary_entity_id=review_req.secondary_target_id,
                    actor_uuid=actor_uuid,
                    reason=justification,
                    override_notes=justification,
                )
            else:
                raise InvalidReviewActionError(f"Unsupported action '{action}' for entity resolution.")

        # 2. Entity status override
        elif target_type in (ReviewTargetType.ENTITY,):
            entity = (
                self.session.query(Entity)
                .filter(Entity.entity_id == review_req.target_id, Entity.case_id == case_id)
                .first()
            )
            if not entity:
                raise EntityNotFoundError(f"Entity {review_req.target_id} not found in case {case_id}.")

            resulting_status = "CONFIRMED" if action == ReviewAction.CONFIRM else "REJECTED"
            entity.status = resulting_status

            sanitized_target = redact_sensitive_text(f"ENTITY: {review_req.target_id} -> {resulting_status}")
            audit = AuditLog(
                audit_id=uuid4(),
                actor_uuid=actor_uuid,
                action_code="ENTITY_REVIEW",
                case_id=case_id,
                target_item=sanitized_target,
                timestamp=datetime.now(timezone.utc),
                outcome=resulting_status,
            )
            self.session.add(audit)
            self.session.commit()

            return ReviewResponse(
                review_id=uuid4(),
                target_type=target_type,
                target_id=review_req.target_id,
                action=action,
                resulting_status=resulting_status,
                status=resulting_status,
                applied_at=datetime.now(timezone.utc),
                reason=justification,
                override_notes=justification,
            )

        # 3. Relationship status override
        elif target_type in (ReviewTargetType.RELATIONSHIP,):
            rel = (
                self.session.query(Relationship)
                .filter(Relationship.relationship_id == review_req.target_id, Relationship.case_id == case_id)
                .first()
            )
            if not rel:
                raise RelationshipNotFoundError(f"Relationship {review_req.target_id} not found in case {case_id}.")

            resulting_status = "CONFIRMED" if action == ReviewAction.CONFIRM else "REJECTED"
            rel.status = resulting_status

            sanitized_target = redact_sensitive_text(f"RELATIONSHIP: {review_req.target_id} -> {resulting_status}")
            audit = AuditLog(
                audit_id=uuid4(),
                actor_uuid=actor_uuid,
                action_code="RELATIONSHIP_REVIEW",
                case_id=case_id,
                target_item=sanitized_target,
                timestamp=datetime.now(timezone.utc),
                outcome=resulting_status,
            )
            self.session.add(audit)
            self.session.commit()

            return ReviewResponse(
                review_id=uuid4(),
                target_type=target_type,
                target_id=review_req.target_id,
                action=action,
                resulting_status=resulting_status,
                status=resulting_status,
                applied_at=datetime.now(timezone.utc),
                reason=justification,
                override_notes=justification,
            )

        else:
            # For predictions/extractions or generic targets
            resulting_status = "CONFIRMED" if action == ReviewAction.CONFIRM else "REJECTED"
            sanitized_target = redact_sensitive_text(f"{target_type}: {review_req.target_id} -> {resulting_status}")
            audit = AuditLog(
                audit_id=uuid4(),
                actor_uuid=actor_uuid,
                action_code="REVIEW_OVERRIDE",
                case_id=case_id,
                target_item=sanitized_target,
                timestamp=datetime.now(timezone.utc),
                outcome=resulting_status,
            )
            self.session.add(audit)
            self.session.commit()

            return ReviewResponse(
                review_id=uuid4(),
                target_type=target_type,
                target_id=review_req.target_id,
                action=action,
                resulting_status=resulting_status,
                status=resulting_status,
                applied_at=datetime.now(timezone.utc),
                reason=justification,
                override_notes=justification,
            )
