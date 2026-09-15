"""
Agent 2 Phase 3: Entity Resolution (ER) & Threshold-Gated Merging Engine.
Implements:
- Pure-Python deterministic string matching algorithms (Jaro-Winkler, Levenshtein, normalized text)
- Centralized decision logic and threshold evaluator (AUTO_MERGE > 0.85, REVIEW_REQUIRED 0.50-0.85, CREATE_NEW < 0.50)
- Tier 1 deterministic identifier matching against entity_identifiers
- Tier 2 heuristic name & alias matching against entities and entity_aliases
- Bounded candidate retrieval strictly scoped to case_id
- Collision detection and quarantined review candidate handling
- Transactional resolution and staging of Agent 1 extraction payloads
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload

from agents.extraction.schemas import ExtractionJobResponse, ExtractedEntity, ExtractedRelationship
from backend.db.models.entities import (
    Entity,
    EntityAlias,
    EntityIdentifier,
    Relationship,
    RelationshipEvidence,
    RelationshipEvidenceState,
    hash_identifier,
    mask_identifier,
    normalize_identifier,
)
from backend.schemas.document_jobs import DocumentState
from backend.security.audit import SecurityAuditAction, record_security_event

logger = logging.getLogger("sih26189.agents.evidence.resolution")

SUPPORT_TYPE_AGENT1_EXTRACTION = "AGENT1_EXTRACTION"


# ==============================================================================
# 1. ENUMS & THRESHOLDS
# ==============================================================================

class EntityMatchDecision(str, Enum):
    """Canonical decision outcomes for entity resolution mentions."""
    AUTO_MERGE = "AUTO_MERGE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CREATE_NEW = "CREATE_NEW"
    COLLISION = "COLLISION"
    REJECT = "REJECT"


class EntityResolutionThresholds:
    """
    Centralized threshold configuration for entity resolution.
    Strictly enforces boundary conditions:
    - AUTO_MERGE: match_confidence > 0.85
    - REVIEW_REQUIRED: 0.50 <= match_confidence <= 0.85
    - CREATE_NEW: match_confidence < 0.50
    """
    AUTO_MERGE_THRESHOLD: float = 0.85
    REVIEW_REQUIRED_THRESHOLD: float = 0.50

    @classmethod
    def evaluate(cls, confidence: float) -> EntityMatchDecision:
        if confidence > cls.AUTO_MERGE_THRESHOLD:
            return EntityMatchDecision.AUTO_MERGE
        elif confidence >= cls.REVIEW_REQUIRED_THRESHOLD:
            return EntityMatchDecision.REVIEW_REQUIRED
        else:
            return EntityMatchDecision.CREATE_NEW


# ==============================================================================
# 2. STRUCTURED DECISION SCHEMAS
# ==============================================================================

class EntityResolutionResult(BaseModel):
    """Structured decision output produced for every resolved mention."""
    model_config = ConfigDict(frozen=True)

    decision: EntityMatchDecision
    matched_entity_id: Optional[UUID] = None
    candidate_entity_id: Optional[UUID] = None
    match_confidence: float
    match_method: str  # DETERMINISTIC_IDENTIFIER, EXACT_ALIAS, HEURISTIC_SIMILARITY, NONE
    reasons: List[str] = Field(default_factory=list)
    case_id: UUID
    mention_ref: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResolutionBatchResult(BaseModel):
    """Aggregate result of executing entity resolution over an extraction payload."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    document_id: UUID
    case_id: UUID
    extraction_job_id: UUID
    entity_mappings: Dict[str, UUID]  # temp_id -> canonical entity_id
    decisions: List[EntityResolutionResult]
    auto_merge_count: int
    review_required_count: int
    create_new_count: int
    collision_count: int
    recommended_doc_state: DocumentState


# ==============================================================================
# 3. PURE STRING MATCHING ALGORITHMS (Deterministic & Reproducible)
# ==============================================================================

def normalize_name_string(s: str) -> str:
    """
    Normalizes candidate and mention strings for heuristic matching.
    Converts to lower case, collapses whitespace, and removes standard punctuation.
    """
    if not s:
        return ""
    clean = s.strip().lower()
    clean = re.sub(r"['\"`]", "", clean)
    clean = re.sub(r"[.,\-_\/()]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes exact Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = list(range(len(s2) + 1))
    v1 = [0] * (len(s2) + 1)

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0 = list(v1)

    return v0[len(s2)]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Computes normalized Levenshtein similarity: 1.0 - (dist / max_len)."""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return max(0.0, 1.0 - (dist / max_len))


def jaro_similarity(s1: str, s2: str) -> float:
    """Computes Jaro string similarity in range [0.0, 1.0]."""
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_distance = max(len1, len2) // 2 - 1
    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    return (
        (matches / len1) + (matches / len2) + ((matches - transpositions / 2) / matches)
    ) / 3.0


def jaro_winkler_similarity(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """Computes Jaro-Winkler string similarity in range [0.0, 1.0]."""
    jaro = jaro_similarity(s1, s2)
    if jaro < 0.7:
        return jaro

    prefix = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            prefix += 1
        else:
            break
        if prefix == 4:
            break

    return jaro + (prefix * prefix_weight * (1.0 - jaro))


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Computes a deterministic, reproducible similarity score in [0.0, 1.0]
    between two names or aliases.
    Handles capitalization, punctuation, and minor spelling differences.
    Guards against over-merging initials or very short strings.
    """
    if not name1 or not name2:
        return 0.0

    if name1 == name2:
        return 1.0

    norm1 = normalize_name_string(name1)
    norm2 = normalize_name_string(name2)

    if norm1 == norm2:
        # Exact normalized match
        return 1.0

    if not norm1 or not norm2:
        return 0.0

    # Short string / initials defense: never auto-merge very short strings
    min_len = min(len(norm1), len(norm2))
    if min_len <= 3:
        # Cap similarity at 0.85 so short tokens / initials always route to REVIEW_REQUIRED
        jw_raw = jaro_winkler_similarity(norm1, norm2)
        return min(jw_raw, 0.85)

    jw = jaro_winkler_similarity(norm1, norm2)
    lev = levenshtein_similarity(norm1, norm2)

    # If Levenshtein is very high (e.g. 1 char typo out of 10+ characters), favor the higher metric
    if lev >= 0.88:
        score = max(jw, lev)
    else:
        # Composite score
        score = 0.5 * jw + 0.5 * lev

    return round(score, 4)


# ==============================================================================
# 4. RESOLUTION ENGINE (Tier 1 + Tier 2 + Thresholds)
# ==============================================================================

class EntityResolutionEngine:
    """
    Core Entity Resolution Engine.
    Executes Tier 1 deterministic identifier matching and Tier 2 heuristic name/alias matching
    under strict server-side case isolation.
    """

    @staticmethod
    def resolve_deterministic_identifier(
        db_session: Session,
        case_id: UUID,
        entity_type: str,
        raw_identifier: str,
        mention_ref: str = "",
    ) -> Optional[EntityResolutionResult]:
        """
        Tier 1: Performs exact lookup on normalized identifier hash within the specified case.
        Returns None if no matching identifier is found.
        """
        norm_val = normalize_identifier(entity_type, raw_identifier)
        if not norm_val:
            return None

        val_hash = hash_identifier(norm_val)

        # SQL Query strictly scoped to case_id
        matching_rows = (
            db_session.query(Entity)
            .join(EntityIdentifier, Entity.entity_id == EntityIdentifier.entity_id)
            .filter(
                Entity.case_id == case_id,
                EntityIdentifier.normalized_value_hash == val_hash,
                Entity.status.notin_(["REJECTED", "MERGED"]),
            )
            .all()
        )

        unique_entities = {e.entity_id: e for e in matching_rows}

        if len(unique_entities) == 1:
            matched_entity = next(iter(unique_entities.values()))
            return EntityResolutionResult(
                decision=EntityMatchDecision.AUTO_MERGE,
                matched_entity_id=matched_entity.entity_id,
                candidate_entity_id=matched_entity.entity_id,
                match_confidence=1.0,
                match_method="DETERMINISTIC_IDENTIFIER",
                reasons=[f"Exact normalized hash match for {entity_type} identifier"],
                case_id=case_id,
                mention_ref=mention_ref,
            )

        if len(unique_entities) > 1:
            first_entity = next(iter(unique_entities.values()))
            return EntityResolutionResult(
                decision=EntityMatchDecision.COLLISION,
                matched_entity_id=None,
                candidate_entity_id=first_entity.entity_id,
                match_confidence=1.0,
                match_method="DETERMINISTIC_IDENTIFIER_COLLISION",
                reasons=[f"Collision: multiple canonical entities in case share {entity_type} hash {val_hash[:8]}..."],
                case_id=case_id,
                mention_ref=mention_ref,
            )

        return None

    @staticmethod
    def resolve_heuristic_match(
        db_session: Session,
        case_id: UUID,
        entity_type: str,
        mention_text: str,
        mention_ref: str = "",
    ) -> EntityResolutionResult:
        """
        Tier 2: Performs bounded candidate retrieval and heuristic name/alias comparison
        strictly within the specified case.
        """
        # Bounded candidate retrieval: only active entities of the same type in the same case
        candidates = (
            db_session.query(Entity)
            .options(joinedload(Entity.aliases))
            .filter(
                Entity.case_id == case_id,
                Entity.entity_type == entity_type,
                Entity.status.notin_(["REJECTED", "MERGED"]),
            )
            .limit(100)
            .all()
        )

        if not candidates:
            return EntityResolutionResult(
                decision=EntityMatchDecision.CREATE_NEW,
                matched_entity_id=None,
                candidate_entity_id=None,
                match_confidence=0.0,
                match_method="NONE",
                reasons=["No candidate entities of matching type found in case"],
                case_id=case_id,
                mention_ref=mention_ref,
            )

        scored_candidates: List[Tuple[Entity, float, str]] = []

        for candidate in candidates:
            # 1. Compare with canonical name
            best_sim = calculate_name_similarity(mention_text, candidate.canonical_name)
            matched_alias = candidate.canonical_name

            # 2. Compare with existing aliases
            for alias in candidate.aliases:
                sim = calculate_name_similarity(mention_text, alias.alias_text)
                if sim > best_sim:
                    best_sim = sim
                    matched_alias = alias.alias_text

            scored_candidates.append((candidate, best_sim, matched_alias))

        # Sort by confidence descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate, best_score, matched_term = scored_candidates[0]

        # Check for ambiguous collision (multiple candidates with equal high score > 0.85)
        if len(scored_candidates) > 1:
            second_candidate, second_score, _ = scored_candidates[1]
            if best_score > EntityResolutionThresholds.AUTO_MERGE_THRESHOLD and second_score > EntityResolutionThresholds.AUTO_MERGE_THRESHOLD and abs(best_score - second_score) < 0.02:
                return EntityResolutionResult(
                    decision=EntityMatchDecision.COLLISION,
                    matched_entity_id=None,
                    candidate_entity_id=best_candidate.entity_id,
                    match_confidence=best_score,
                    match_method="HEURISTIC_COLLISION",
                    reasons=[f"Multiple candidate entities in case tie with high similarity ({best_score:.4f} vs {second_score:.4f})"],
                    case_id=case_id,
                    mention_ref=mention_ref,
                )

        decision = EntityResolutionThresholds.evaluate(best_score)
        matched_id = best_candidate.entity_id if decision == EntityMatchDecision.AUTO_MERGE else None
        candidate_id = best_candidate.entity_id if decision in (EntityMatchDecision.AUTO_MERGE, EntityMatchDecision.REVIEW_REQUIRED) else None

        reason = (
            f"High confidence similarity ({best_score:.4f}) to candidate '{matched_term}'"
            if decision == EntityMatchDecision.AUTO_MERGE
            else f"Ambiguous similarity ({best_score:.4f}) to candidate '{matched_term}'"
            if decision == EntityMatchDecision.REVIEW_REQUIRED
            else f"Low similarity ({best_score:.4f}); no credible match"
        )

        return EntityResolutionResult(
            decision=decision,
            matched_entity_id=matched_id,
            candidate_entity_id=candidate_id,
            match_confidence=best_score,
            match_method="HEURISTIC_SIMILARITY",
            reasons=[reason],
            case_id=case_id,
            mention_ref=mention_ref,
        )

    @classmethod
    def match_mention(
        cls,
        db_session: Session,
        case_id: UUID,
        mention: ExtractedEntity,
        mention_ref: str = "",
    ) -> EntityResolutionResult:
        """
        Dispatches mention resolution through Tier 1 (deterministic) or Tier 2 (heuristic).
        """
        entity_type = mention.entity_type.value
        extracted_text = mention.extracted_text

        # Tier 1: Stable external identifiers
        if entity_type in ("PHONE", "BANK_ACCOUNT", "VEHICLE"):
            t1_result = cls.resolve_deterministic_identifier(
                db_session=db_session,
                case_id=case_id,
                entity_type=entity_type,
                raw_identifier=extracted_text,
                mention_ref=mention_ref,
            )
            if t1_result is not None:
                return t1_result

        # Tier 2: Heuristic string similarity
        return cls.resolve_heuristic_match(
            db_session=db_session,
            case_id=case_id,
            entity_type=entity_type,
            mention_text=extracted_text,
            mention_ref=mention_ref,
        )


# ==============================================================================
# 5. BATCH PAYLOAD STAGING & ORCHESTRATION
# ==============================================================================

def resolve_and_stage_payload(
    db_session: Session,
    payload: ExtractionJobResponse,
    case_id: UUID,
    document_id: UUID,
    actor_id: Optional[UUID] = None,
) -> ResolutionBatchResult:
    """
    Executes Entity Resolution across all extracted entities in an Agent 1 payload.
    Maps mentions to existing canonical entities, creates new entities, or quarantines
    ambiguous candidates, and stages relationships between resolved entities.
    Executes within the caller's database transaction.
    """
    temp_id_to_uuid: Dict[str, UUID] = {}
    decisions: List[EntityResolutionResult] = []
    auto_merge_cnt = 0
    review_required_cnt = 0
    create_new_cnt = 0
    collision_cnt = 0

    # 1. Resolve Mentions
    for mention in payload.extracted_entities:
        mention_ref = f"doc:{document_id}|job:{payload.extraction_job_id}|mention:{mention.temp_id}"
        resolution = EntityResolutionEngine.match_mention(
            db_session=db_session,
            case_id=case_id,
            mention=mention,
            mention_ref=mention_ref,
        )
        decisions.append(resolution)

        entity_type_str = mention.entity_type.value
        raw_text = mention.extracted_text
        clean_name = raw_text[:255]

        # Case A: AUTO_MERGE
        if resolution.decision == EntityMatchDecision.AUTO_MERGE:
            auto_merge_cnt += 1
            canonical_uuid = resolution.matched_entity_id
            temp_id_to_uuid[mention.temp_id] = canonical_uuid

            # Absorb mention as an alias if not already present
            existing_alias = (
                db_session.query(EntityAlias)
                .filter(EntityAlias.entity_id == canonical_uuid, EntityAlias.alias_text == clean_name)
                .first()
            )
            if not existing_alias:
                alias_record = EntityAlias(
                    alias_id=uuid4(),
                    entity_id=canonical_uuid,
                    alias_text=clean_name,
                    source_ref=mention_ref,
                )
                db_session.add(alias_record)

            # If mention is an identifier, ensure identifier is linked
            if entity_type_str in ("PHONE", "BANK_ACCOUNT", "VEHICLE"):
                norm_val = normalize_identifier(entity_type_str, raw_text)
                if norm_val:
                    val_hash = hash_identifier(norm_val)
                    existing_ident = (
                        db_session.query(EntityIdentifier)
                        .filter(
                            EntityIdentifier.entity_id == canonical_uuid,
                            EntityIdentifier.type == entity_type_str,
                            EntityIdentifier.normalized_value_hash == val_hash,
                        )
                        .first()
                    )
                    if not existing_ident:
                        ident_record = EntityIdentifier(
                            identifier_id=uuid4(),
                            entity_id=canonical_uuid,
                            type=entity_type_str,
                            normalized_value_hash=val_hash,
                            value_policy=mask_identifier(entity_type_str, norm_val),
                        )
                        db_session.add(ident_record)

            # Audit auto-merge
            record_security_event(
                db=db_session,
                action_code=SecurityAuditAction.ER_AUTO_MERGE,
                actor_uuid=actor_id,
                case_id=case_id,
                target_item=f"MERGE:target={canonical_uuid}|conf={resolution.match_confidence:.4f}|method={resolution.match_method}"[:255],
                outcome="SUCCESS",
            )

        # Case B: REVIEW_REQUIRED or COLLISION
        elif resolution.decision in (EntityMatchDecision.REVIEW_REQUIRED, EntityMatchDecision.COLLISION):
            if resolution.decision == EntityMatchDecision.COLLISION:
                collision_cnt += 1
                audit_action = SecurityAuditAction.ER_COLLISION
            else:
                review_required_cnt += 1
                audit_action = SecurityAuditAction.ER_REVIEW_REQUIRED

            # Create quarantined review candidate entity
            candidate_uuid = uuid4()
            temp_id_to_uuid[mention.temp_id] = candidate_uuid

            review_entity = Entity(
                entity_id=candidate_uuid,
                case_id=case_id,
                entity_type=entity_type_str,
                canonical_name=clean_name,
                status="REVIEW_REQUIRED",
            )
            db_session.add(review_entity)

            # Provenance alias linking candidate entity and score
            cand_ref = f"{mention_ref}|candidate:{resolution.candidate_entity_id}|conf:{resolution.match_confidence:.4f}"
            alias_record = EntityAlias(
                alias_id=uuid4(),
                entity_id=candidate_uuid,
                alias_text=clean_name,
                source_ref=cand_ref[:255],
            )
            db_session.add(alias_record)

            # Link identifier if applicable
            if entity_type_str in ("PHONE", "BANK_ACCOUNT", "VEHICLE"):
                norm_val = normalize_identifier(entity_type_str, raw_text)
                if norm_val:
                    val_hash = hash_identifier(norm_val)
                    ident_record = EntityIdentifier(
                        identifier_id=uuid4(),
                        entity_id=candidate_uuid,
                        type=entity_type_str,
                        normalized_value_hash=val_hash,
                        value_policy=mask_identifier(entity_type_str, norm_val),
                    )
                    db_session.add(ident_record)

            record_security_event(
                db=db_session,
                action_code=audit_action,
                actor_uuid=actor_id,
                case_id=case_id,
                target_item=f"REVIEW:entity={candidate_uuid}|cand={resolution.candidate_entity_id}|conf={resolution.match_confidence:.4f}"[:255],
                outcome="REVIEW_REQUIRED",
            )

        # Case C: CREATE_NEW
        else:
            create_new_cnt += 1
            new_entity_uuid = uuid4()
            temp_id_to_uuid[mention.temp_id] = new_entity_uuid

            new_entity = Entity(
                entity_id=new_entity_uuid,
                case_id=case_id,
                entity_type=entity_type_str,
                canonical_name=clean_name,
                status="ACTIVE",
            )
            db_session.add(new_entity)

            alias_record = EntityAlias(
                alias_id=uuid4(),
                entity_id=new_entity_uuid,
                alias_text=clean_name,
                source_ref=mention_ref,
            )
            db_session.add(alias_record)

            if entity_type_str in ("PHONE", "BANK_ACCOUNT", "VEHICLE"):
                norm_val = normalize_identifier(entity_type_str, raw_text)
                if norm_val:
                    val_hash = hash_identifier(norm_val)
                    ident_record = EntityIdentifier(
                        identifier_id=uuid4(),
                        entity_id=new_entity_uuid,
                        type=entity_type_str,
                        normalized_value_hash=val_hash,
                        value_policy=mask_identifier(entity_type_str, norm_val),
                    )
                    db_session.add(ident_record)

            record_security_event(
                db=db_session,
                action_code=SecurityAuditAction.ER_NEW_ENTITY_CREATED,
                actor_uuid=actor_id,
                case_id=case_id,
                target_item=f"NEW_ENTITY:{new_entity_uuid}|type={entity_type_str}"[:255],
                outcome="SUCCESS",
            )

    # 2. Stage Relationships between Resolved Entities
    for rel in payload.extracted_relationships:
        source_uuid = temp_id_to_uuid.get(rel.source_temp_id)
        target_uuid = temp_id_to_uuid.get(rel.target_temp_id)

        if not source_uuid or not target_uuid:
            logger.warning("Skipping relationship with unknown endpoint: %s -> %s", rel.source_temp_id, rel.target_temp_id)
            continue

        # Prevent self-loop on auto-merged endpoints
        if source_uuid == target_uuid:
            logger.info("Skipping self-loop relationship on entity %s", source_uuid)
            continue

        rel_uuid = uuid4()
        rel_record = Relationship(
            relationship_id=rel_uuid,
            case_id=case_id,
            source_entity_uuid=source_uuid,
            target_entity_uuid=target_uuid,
            type=rel.type[:50],
            status=RelationshipEvidenceState.OBSERVED.value,
        )
        db_session.add(rel_record)

        evidence_record = RelationshipEvidence(
            evidence_id=uuid4(),
            relationship_id=rel_uuid,
            source_ref=f"doc:{document_id}|job:{payload.extraction_job_id}",
            support_type=SUPPORT_TYPE_AGENT1_EXTRACTION,
        )
        db_session.add(evidence_record)

    # 3. Determine Recommended Document Lifecycle State
    if review_required_cnt > 0 or collision_cnt > 0:
        recommended_state = DocumentState.REVIEW_REQUIRED
    else:
        recommended_state = DocumentState.ACCEPTED

    return ResolutionBatchResult(
        document_id=document_id,
        case_id=case_id,
        extraction_job_id=payload.extraction_job_id,
        entity_mappings=temp_id_to_uuid,
        decisions=decisions,
        auto_merge_count=auto_merge_cnt,
        review_required_count=review_required_cnt,
        create_new_count=create_new_cnt,
        collision_count=collision_cnt,
        recommended_doc_state=recommended_state,
    )
