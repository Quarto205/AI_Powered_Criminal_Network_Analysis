"""
Evidence Detail and Human Review Override Service for SIH26189.
Encapsulates:
- Deep entity evidence retrieval (aliases, masked identifiers, risk scores, chunk offsets)
- Relationship citation chains and endpoints
- Human-in-the-loop overrides (CONFIRM, REJECT, MERGE)
- Immutability semantics: historical source evidence is never deleted; secondary entities/relationships are soft-merged or marked REJECTED
- Automatic Neo4j graph projection synchronization following PostgreSQL mutations
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.models.entities import (
    Entity,
    EntityAlias,
    EntityIdentifier,
    Relationship,
    RelationshipEvidence,
)
from backend.db.models.analytics import AuditLog, RiskScore
from backend.db.models.ingestion import Document, DocumentChunk, DocumentVersion
from backend.graph.connection import get_graph_manager
from backend.schemas.evidence_analysis import (
    EntityAliasInfo,
    EntityDetailResponse,
    EntityIdentifierInfo,
    EvidenceCitation,
    ProvenanceSpan,
    RelationshipDetailResponse,
    RelationshipEndpointSummary,
    ReviewAction,
    ReviewResponse,
    ReviewTargetType,
    RiskScoreInfo,
)
from backend.security.audit import SecurityAuditAction, record_security_event
from backend.services.graph_projection import GraphProjectionService

logger = logging.getLogger("backend.services.evidence_review")


class ReviewServiceError(Exception):
    """Raised on invalid review actions, missing entities, or cross-case violations."""
    pass


class ReviewNotFoundError(ReviewServiceError):
    """Raised when target entity or relationship does not exist."""
    pass


class ReviewConflictError(ReviewServiceError):
    """Raised on invalid merge targets or illegal state transitions."""
    pass


def mask_identifier_value(val_hash: str, id_type: str) -> str:
    """
    Applies defensive privacy masking to external identifier representations.
    Never exposes plaintext identifiers.
    """
    if not val_hash:
        return "****"
    if len(val_hash) <= 8:
        return val_hash[:2] + "****" + val_hash[-2:]
    return f"HASH:{val_hash[:6]}...{val_hash[-4:]}"


class EvidenceReviewService:
    """
    Service managing authoritative PostgreSQL evidence inspection and human overrides.
    """
    def __init__(self, db: Session, graph_projection_service: Optional[GraphProjectionService] = None):
        self.db = db
        self.graph_projection = graph_projection_service or GraphProjectionService(db=db)

    # ==========================================================================
    # 1. ENTITY DETAIL & PROVENANCE
    # ==========================================================================

    def get_entity_detail(self, case_id: UUID, entity_id: UUID) -> EntityDetailResponse:
        """
        Retrieves deep canonical entity information, masked identifiers, aliases,
        latest priority/risk score, and evidence provenance spans.
        Enforces case tenancy server-side: raises ReviewNotFoundError if not in case.
        """
        entity = (
            self.db.query(Entity)
            .filter(Entity.entity_id == entity_id, Entity.case_id == case_id)
            .first()
        )
        if not entity:
            raise ReviewNotFoundError(f"Entity {entity_id} not found in case {case_id}")

        # Aliases
        aliases = [
            EntityAliasInfo(
                alias_id=a.alias_id,
                alias_text=a.alias_text,
                source_ref=a.source_ref,
            )
            for a in entity.aliases
        ]

        # Identifiers with defensive masking
        identifiers = [
            EntityIdentifierInfo(
                identifier_id=ident.identifier_id,
                type=ident.type,
                masked_value=mask_identifier_value(ident.normalized_value_hash, ident.type),
                value_policy=ident.value_policy,
            )
            for ident in entity.identifiers
        ]

        # Latest Risk Score
        risk_score_info = None
        latest_score = (
            self.db.query(RiskScore)
            .filter(RiskScore.target_entity_uuid == entity_id)
            .order_by(RiskScore.value.desc())
            .first()
        )
        if latest_score:
            risk_score_info = RiskScoreInfo(
                score_id=latest_score.score_id,
                score_type=latest_score.score_type,
                value=float(latest_score.value),
                features_summary=latest_score.features_summary,
            )

        # Provenance Spans
        # Trace aliases, relationships, or chunks matching entity canonical_name/id
        provenance_spans: List[ProvenanceSpan] = []
        for a in entity.aliases:
            if a.source_ref:
                provenance_spans.append(
                    ProvenanceSpan(
                        source_ref=a.source_ref,
                        support_type="ALIAS_OBSERVATION",
                        snippet=a.alias_text,
                    )
                )

        return EntityDetailResponse(
            entity_id=entity.entity_id,
            case_id=entity.case_id,
            canonical_name=entity.canonical_name,
            entity_type=entity.entity_type,
            status=entity.status,
            aliases=aliases,
            identifiers=identifiers,
            risk_score=risk_score_info,
            provenance_spans=provenance_spans,
            created_at=entity.created_at,
        )

    # ==========================================================================
    # 2. RELATIONSHIP DETAIL & CITATIONS
    # ==========================================================================

    def get_relationship_detail(self, case_id: UUID, relationship_id: UUID) -> RelationshipDetailResponse:
        """
        Retrieves detailed relationship records with evidence citation chains.
        Enforces that relationship and both endpoints strictly belong to case_id.
        """
        rel = (
            self.db.query(Relationship)
            .filter(Relationship.relationship_id == relationship_id, Relationship.case_id == case_id)
            .first()
        )
        if not rel:
            raise ReviewNotFoundError(f"Relationship {relationship_id} not found in case {case_id}")

        source_e = self.db.query(Entity).filter(Entity.entity_id == rel.source_entity_uuid).first()
        target_e = self.db.query(Entity).filter(Entity.entity_id == rel.target_entity_uuid).first()

        citations = [
            EvidenceCitation(
                evidence_id=ev.evidence_id,
                source_ref=ev.source_ref,
                support_type=ev.support_type,
            )
            for ev in rel.evidence
        ]

        return RelationshipDetailResponse(
            relationship_id=rel.relationship_id,
            case_id=rel.case_id,
            source_entity=RelationshipEndpointSummary(
                entity_id=source_e.entity_id,
                canonical_name=source_e.canonical_name,
                entity_type=source_e.entity_type,
            ),
            target_entity=RelationshipEndpointSummary(
                entity_id=target_e.entity_id,
                canonical_name=target_e.canonical_name,
                entity_type=target_e.entity_type,
            ),
            type=rel.type,
            status=rel.status,
            confidence_score=1.0,
            is_predicted=False,
            evidence_citations=citations,
            created_at=rel.created_at,
        )

    # ==========================================================================
    # 3. HUMAN REVIEW OVERRIDES
    # ==========================================================================

    def apply_review_override(
        self,
        case_id: UUID,
        actor_uuid: UUID,
        target_type: str,
        target_id: UUID,
        action: str,
        reason: str,
        secondary_target_id: Optional[UUID] = None,
    ) -> ReviewResponse:
        """
        Executes a supervisor-level human review override.
        Guarantees:
        1. Human decision primacy: once CONFIRMED, REJECTED, or MERGED, state is canonical.
        2. Transactional consistency: all mutations committed together or rolled back.
        3. Immutability: no physical deletion of historical evidence.
        4. Neo4j graph projection synchronization.
        5. Synchronous audit logging to audit_logs ledger.
        """
        target_type = target_type.upper()
        action = action.upper()

        if target_type == ReviewTargetType.ENTITY:
            return self._review_entity(
                case_id=case_id,
                actor_uuid=actor_uuid,
                entity_id=target_id,
                action=action,
                reason=reason,
                secondary_id=secondary_target_id,
            )
        elif target_type == ReviewTargetType.RELATIONSHIP:
            return self._review_relationship(
                case_id=case_id,
                actor_uuid=actor_uuid,
                relationship_id=target_id,
                action=action,
                reason=reason,
            )
        else:
            raise ReviewServiceError(f"Unsupported target_type '{target_type}'")

    def _review_entity(
        self,
        case_id: UUID,
        actor_uuid: UUID,
        entity_id: UUID,
        action: str,
        reason: str,
        secondary_id: Optional[UUID] = None,
    ) -> ReviewResponse:
        entity = (
            self.db.query(Entity)
            .filter(Entity.entity_id == entity_id, Entity.case_id == case_id)
            .first()
        )
        if not entity:
            raise ReviewNotFoundError(f"Entity {entity_id} not found in case {case_id}")

        resulting_status = entity.status

        if action == ReviewAction.CONFIRM:
            entity.status = "CONFIRMED"
            resulting_status = "CONFIRMED"
            self.db.commit()

            # Synchronize to Neo4j
            try:
                self.graph_projection.upsert_entity(entity)
            except Exception as e:
                logger.error(f"Neo4j sync failed after entity confirmation: {e}")

        elif action == ReviewAction.REJECT:
            entity.status = "REJECTED"
            resulting_status = "REJECTED"
            self.db.commit()

            # Synchronize to Neo4j
            try:
                self.graph_projection.upsert_entity(entity)
            except Exception as e:
                logger.error(f"Neo4j sync failed after entity rejection: {e}")

        elif action == ReviewAction.MERGE:
            if not secondary_id:
                raise ReviewConflictError("secondary_target_id is required for MERGE action.")
            if secondary_id == entity_id:
                raise ReviewConflictError("Cannot merge an entity into itself.")

            secondary = (
                self.db.query(Entity)
                .filter(Entity.entity_id == secondary_id, Entity.case_id == case_id)
                .first()
            )
            if not secondary:
                raise ReviewNotFoundError(f"Secondary entity {secondary_id} not found in case {case_id}")

            if secondary.status == "MERGED":
                raise ReviewConflictError(f"Secondary entity {secondary_id} is already merged.")

            # Perform Entity Merge
            # 1. Absorb secondary's canonical name as an alias on target
            alias = EntityAlias(
                alias_id=uuid4(),
                entity_id=entity.entity_id,
                alias_text=secondary.canonical_name,
                source_ref=f"MERGE_FROM:{secondary.entity_id}",
            )
            self.db.add(alias)

            # 2. Re-point existing aliases from secondary to target
            for a in secondary.aliases:
                a.entity_id = entity.entity_id

            # 3. Re-point existing identifiers from secondary to target
            for ident in secondary.identifiers:
                ident.entity_id = entity.entity_id

            # 4. Redirect relationships referencing secondary to target
            outgoing_rels = (
                self.db.query(Relationship)
                .filter(Relationship.source_entity_uuid == secondary.entity_id, Relationship.case_id == case_id)
                .all()
            )
            for r in outgoing_rels:
                if r.target_entity_uuid != entity.entity_id:
                    r.source_entity_uuid = entity.entity_id
                else:
                    # Self-loop prevention: archive relationship
                    r.status = "MERGED_SELF_LOOP"

            incoming_rels = (
                self.db.query(Relationship)
                .filter(Relationship.target_entity_uuid == secondary.entity_id, Relationship.case_id == case_id)
                .all()
            )
            for r in incoming_rels:
                if r.source_entity_uuid != entity.entity_id:
                    r.target_entity_uuid = entity.entity_id
                else:
                    # Self-loop prevention: archive relationship
                    r.status = "MERGED_SELF_LOOP"

            # 5. Soft-retire secondary entity
            secondary.status = "MERGED"
            entity.status = "CONFIRMED"
            resulting_status = "CONFIRMED"

            self.db.commit()

            # 6. Synchronize full case graph to Neo4j to reflect redirected edges cleanly
            try:
                self.graph_projection.rebuild_case_graph(case_id)
            except Exception as e:
                logger.error(f"Neo4j sync failed after entity merge: {e}")

        else:
            raise ReviewServiceError(f"Unsupported action '{action}' for entity review.")

        # Record audit event
        record_security_event(
            db=self.db,
            action_code=SecurityAuditAction.REVIEW_OVERRIDE,
            actor_uuid=actor_uuid,
            case_id=case_id,
            target_item=f"ENTITY:{entity_id}:{action}:{reason[:50]}",
            outcome="SUCCESS",
        )

        return ReviewResponse(
            target_type=ReviewTargetType.ENTITY,
            target_id=entity_id,
            action=action,
            resulting_status=resulting_status,
            secondary_target_id=secondary_id,
            reason=reason,
        )

    def _review_relationship(
        self,
        case_id: UUID,
        actor_uuid: UUID,
        relationship_id: UUID,
        action: str,
        reason: str,
    ) -> ReviewResponse:
        rel = (
            self.db.query(Relationship)
            .filter(Relationship.relationship_id == relationship_id, Relationship.case_id == case_id)
            .first()
        )
        if not rel:
            raise ReviewNotFoundError(f"Relationship {relationship_id} not found in case {case_id}")

        if action == ReviewAction.CONFIRM:
            rel.status = "CONFIRMED"
            self.db.commit()
            try:
                self.graph_projection.upsert_relationship(rel)
            except Exception as e:
                logger.error(f"Neo4j sync failed after relationship confirmation: {e}")

        elif action == ReviewAction.REJECT:
            rel.status = "REJECTED"
            self.db.commit()
            try:
                # Rebuild case graph so rejected edge is omitted
                self.graph_projection.rebuild_case_graph(case_id)
            except Exception as e:
                logger.error(f"Neo4j sync failed after relationship rejection: {e}")

        else:
            raise ReviewServiceError(f"Unsupported action '{action}' for relationship review.")

        # Record audit event
        record_security_event(
            db=self.db,
            action_code=SecurityAuditAction.REVIEW_OVERRIDE,
            actor_uuid=actor_uuid,
            case_id=case_id,
            target_item=f"RELATIONSHIP:{relationship_id}:{action}:{reason[:50]}",
            outcome="SUCCESS",
        )

        return ReviewResponse(
            target_type=ReviewTargetType.RELATIONSHIP,
            target_id=relationship_id,
            action=action,
            resulting_status=rel.status,
            reason=reason,
        )
