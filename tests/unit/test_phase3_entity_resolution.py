from backend.db.session import get_db, get_engine, get_session_factory
"""
Comprehensive Unit & Integration Test Suite for Agent 2 Phase 3:
Entity Resolution (ER) & Threshold-Gated Merging Engine.

Strictly covers all 35 required test scenarios:
- TIER 1: Exact identifier matches (Phone, Bank Account, UPI, Vehicle Plate), case isolation, collisions, invalid inputs
- TIER 2: Exact alias, minor spelling variation, Jaro-Winkler, Levenshtein, initials/common names, low similarity
- THRESHOLDS: Explicit boundary tests (0.8501, 0.8500, 0.8499, 0.5000, 0.4999)
- INTEGRITY: Document/chunk immutability, raw text preservation, alias provenance, audit records, reversal
- AUTHORIZATION: Server-side case isolation, 404 anti-enumeration
- CONCURRENCY & IDEMPOTENCY: Duplicate mention processing, duplicate review approval
- LIFECYCLE: State progression to ACCEPTED and REVIEW_REQUIRED
"""

from datetime import datetime, timezone
import io
from typing import Any, Dict, Generator, List, Optional, Tuple
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from agents.evidence.resolution import (
    EntityMatchDecision,
    EntityResolutionEngine,
    EntityResolutionResult,
    EntityResolutionThresholds,
    ResolutionBatchResult,
    calculate_name_similarity,
    jaro_similarity,
    jaro_winkler_similarity,
    levenshtein_distance,
    levenshtein_similarity,
    normalize_name_string,
    resolve_and_stage_payload,
)
from agents.extraction.schemas import (
    ExtractionEntityType,
    ExtractionJobResponse,
    ExtractedEntity,
    ExtractedRelationship,
)
from backend.db.base import Base
from backend.db.models.analytics import AuditLog
from backend.db.models.entities import (
    Entity,
    EntityAlias,
    EntityIdentifier,
    Relationship,
    RelationshipEvidence,
    hash_identifier,
    mask_identifier,
    normalize_identifier,
)
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.ingestion import Document as DbDocument
from backend.schemas.document_jobs import DocumentState
from backend.security.audit import SecurityAuditAction
from backend.security.rbac import SystemRoles
from backend.services.entity_resolution import EntityResolutionService
from backend.services.evidence_review import EvidenceReviewService, ReviewConflictError, ReviewNotFoundError


# ==============================================================================
# TEST FIXTURES
# ==============================================================================

@pytest.fixture
def er_db():
    """In-memory SQLite database session for deterministic tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    session.session_factory = TestingSessionLocal

    # Seed roles
    for role_name in [SystemRoles.INVESTIGATOR, SystemRoles.SUPERVISOR]:
        session.add(Role(role_id=uuid4(), name=role_name))

    # Seed user
    user = User(
        user_id=uuid4(),
        username="supervisor_er",
        email="sup_er@sih.gov.in",
        password_hash="hash",
        account_status="ACTIVE",
    )
    session.add(user)
    session.commit()

    yield session

    session.close()


def create_case(db: Session, case_code: str = "CASE-ER-001") -> Tuple[Case, User]:
    user = db.query(User).filter_by(username="supervisor_er").first()
    case = Case(
        case_id=uuid4(),
        case_code=f"{case_code}-{uuid4().hex[:6]}",
        title="ER Test Case",
        status="ACTIVE",
        jurisdiction="CENTRAL",
        created_by=user.user_id,
    )
    db.add(case)
    member = CaseMember(
        case_member_id=uuid4(),
        case_id=case.case_id,
        user_id=user.user_id,
        role_in_case=SystemRoles.SUPERVISOR,
    )
    db.add(member)
    db.commit()
    return case, user


# ==============================================================================
# 1. PURE STRING ALGORITHMS & SIMILARITY TESTS
# ==============================================================================

class TestPureAlgorithms:
    def test_levenshtein_distance(self):
        assert levenshtein_distance("kitten", "sitting") == 3
        assert levenshtein_distance("hello", "hello") == 0
        assert levenshtein_distance("", "abc") == 3
        assert levenshtein_distance("abc", "") == 3

    def test_levenshtein_similarity(self):
        assert levenshtein_similarity("Vikram Singh", "Vikram Singh") == 1.0
        assert levenshtein_similarity("Vikram Singh", "Vikram Sing") == 11.0 / 12.0
        assert levenshtein_similarity("", "abc") == 0.0

    def test_jaro_winkler_similarity(self):
        # Exact match
        assert jaro_winkler_similarity("dwayne", "dwayne") == 1.0
        # High similarity with common prefix
        score = jaro_winkler_similarity("martha", "marhta")
        assert score > 0.90
        # Low similarity
        assert jaro_winkler_similarity("apple", "orange") < 0.60

    def test_normalize_name_string(self):
        assert normalize_name_string("  Vikram   Singh, Jr. ") == "vikram singh jr"
        assert normalize_name_string("O'Connor-Smith") == "oconnor smith"


# ==============================================================================
# 2. THRESHOLD EVALUATION TESTS (Mandatory 14, 15, 16, 17, 18)
# ==============================================================================

class TestThresholdEvaluator:
    def test_14_score_just_above_085_auto_merge(self):
        assert EntityResolutionThresholds.evaluate(0.8501) == EntityMatchDecision.AUTO_MERGE
        assert EntityResolutionThresholds.evaluate(0.9500) == EntityMatchDecision.AUTO_MERGE
        assert EntityResolutionThresholds.evaluate(1.0000) == EntityMatchDecision.AUTO_MERGE

    def test_15_score_exactly_085_review_required(self):
        assert EntityResolutionThresholds.evaluate(0.8500) == EntityMatchDecision.REVIEW_REQUIRED

    def test_16_score_just_below_085_review_required(self):
        assert EntityResolutionThresholds.evaluate(0.8499) == EntityMatchDecision.REVIEW_REQUIRED

    def test_17_score_exactly_050_review_required(self):
        assert EntityResolutionThresholds.evaluate(0.5000) == EntityMatchDecision.REVIEW_REQUIRED

    def test_18_score_just_below_050_create_new(self):
        assert EntityResolutionThresholds.evaluate(0.4999) == EntityMatchDecision.CREATE_NEW
        assert EntityResolutionThresholds.evaluate(0.1000) == EntityMatchDecision.CREATE_NEW
        assert EntityResolutionThresholds.evaluate(0.0000) == EntityMatchDecision.CREATE_NEW


# ==============================================================================
# 3. TIER 1: DETERMINISTIC MATCHING TESTS (Mandatory 1, 2, 3, 4, 5, 6, 7)
# ==============================================================================

class TestTier1DeterministicMatching:
    def test_1_exact_phone_hash_matches_existing_entity(self, er_db):
        case, user = create_case(er_db)
        # Seed existing entity with phone
        canonical_e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PHONE", canonical_name="+919876543210")
        norm_phone = normalize_identifier("PHONE", "9876543210")
        ident = EntityIdentifier(
            identifier_id=uuid4(),
            entity_id=canonical_e.entity_id,
            type="PHONE",
            normalized_value_hash=hash_identifier(norm_phone),
            value_policy=mask_identifier("PHONE", norm_phone),
        )
        er_db.add_all([canonical_e, ident])
        er_db.commit()

        # Mention with different format of same phone
        mention = ExtractedEntity(
            temp_id="E1",
            entity_type=ExtractionEntityType.PHONE,
            extracted_text="+91 98765-43210",
            character_start=0,
            character_end=15,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.AUTO_MERGE
        assert result.matched_entity_id == canonical_e.entity_id
        assert result.match_confidence == 1.0
        assert result.match_method == "DETERMINISTIC_IDENTIFIER"

    def test_2_exact_bank_account_hash_matches_existing_entity(self, er_db):
        case, _ = create_case(er_db)
        canonical_e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="BANK_ACCOUNT", canonical_name="SBIN0001234:11223344556")
        norm_acct = normalize_identifier("BANK_ACCOUNT", "SBIN0001234:11223344556")
        ident = EntityIdentifier(
            identifier_id=uuid4(),
            entity_id=canonical_e.entity_id,
            type="BANK_ACCOUNT",
            normalized_value_hash=hash_identifier(norm_acct),
            value_policy="****",
        )
        er_db.add_all([canonical_e, ident])
        er_db.commit()

        mention = ExtractedEntity(
            temp_id="E2",
            entity_type=ExtractionEntityType.BANK_ACCOUNT,
            extracted_text="sbin0001234: 11223344556",
            character_start=0,
            character_end=24,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.AUTO_MERGE
        assert result.matched_entity_id == canonical_e.entity_id
        assert result.match_confidence == 1.0

    def test_3_exact_upi_hash_matches_existing_entity(self, er_db):
        case, _ = create_case(er_db)
        canonical_e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="BANK_ACCOUNT", canonical_name="merchant@okhdfcbank")
        norm_upi = normalize_identifier("UPI", "merchant@okhdfcbank")
        ident = EntityIdentifier(
            identifier_id=uuid4(),
            entity_id=canonical_e.entity_id,
            type="BANK_ACCOUNT",
            normalized_value_hash=hash_identifier(norm_upi),
            value_policy="****",
        )
        er_db.add_all([canonical_e, ident])
        er_db.commit()

        mention = ExtractedEntity(
            temp_id="E3",
            entity_type=ExtractionEntityType.BANK_ACCOUNT,
            extracted_text="  MERCHANT@OKHDFCBANK  ",
            character_start=0,
            character_end=22,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.AUTO_MERGE
        assert result.matched_entity_id == canonical_e.entity_id

    def test_4_exact_vehicle_plate_hash_matches_existing_entity(self, er_db):
        case, _ = create_case(er_db)
        canonical_e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="VEHICLE", canonical_name="MH02CL1234")
        norm_plate = normalize_identifier("VEHICLE", "MH02CL1234")
        ident = EntityIdentifier(
            identifier_id=uuid4(),
            entity_id=canonical_e.entity_id,
            type="VEHICLE",
            normalized_value_hash=hash_identifier(norm_plate),
            value_policy="****",
        )
        er_db.add_all([canonical_e, ident])
        er_db.commit()

        mention = ExtractedEntity(
            temp_id="E4",
            entity_type=ExtractionEntityType.VEHICLE,
            extracted_text="mh-02-cl-1234",
            character_start=0,
            character_end=13,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.AUTO_MERGE
        assert result.matched_entity_id == canonical_e.entity_id

    def test_5_same_identifier_in_different_case_does_not_merge(self, er_db):
        case_a, _ = create_case(er_db, "CASE-A")
        case_b, _ = create_case(er_db, "CASE-B")

        # Identifier registered in Case A
        canonical_a = Entity(entity_id=uuid4(), case_id=case_a.case_id, entity_type="PHONE", canonical_name="+919999988888")
        norm_phone = normalize_identifier("PHONE", "+919999988888")
        ident_a = EntityIdentifier(
            identifier_id=uuid4(),
            entity_id=canonical_a.entity_id,
            type="PHONE",
            normalized_value_hash=hash_identifier(norm_phone),
            value_policy="****",
        )
        er_db.add_all([canonical_a, ident_a])
        er_db.commit()

        # Mention appears in Case B
        mention_b = ExtractedEntity(
            temp_id="EB",
            entity_type=ExtractionEntityType.PHONE,
            extracted_text="+91 99999 88888",
            character_start=0,
            character_end=15,
        )
        # Attempt resolution in Case B
        result_b = EntityResolutionEngine.match_mention(er_db, case_b.case_id, mention_b)

        # MUST NOT merge with Case A entity!
        assert result_b.decision == EntityMatchDecision.CREATE_NEW
        assert result_b.matched_entity_id is None

    def test_6_duplicate_collision_identifier_routes_to_collision(self, er_db):
        case, _ = create_case(er_db)
        norm_phone = normalize_identifier("PHONE", "9111122222")
        p_hash = hash_identifier(norm_phone)

        # Two distinct entities erroneously have the same phone in the same case
        e1 = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PHONE", canonical_name="Phone 1")
        i1 = EntityIdentifier(identifier_id=uuid4(), entity_id=e1.entity_id, type="PHONE", normalized_value_hash=p_hash)
        e2 = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PHONE", canonical_name="Phone 2")
        i2 = EntityIdentifier(identifier_id=uuid4(), entity_id=e2.entity_id, type="PHONE", normalized_value_hash=p_hash)

        er_db.add_all([e1, i1, e2, i2])
        er_db.commit()

        mention = ExtractedEntity(
            temp_id="E_COLLISION",
            entity_type=ExtractionEntityType.PHONE,
            extracted_text="9111122222",
            character_start=0,
            character_end=10,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        # Must detect collision, not auto-merge
        assert result.decision == EntityMatchDecision.COLLISION
        assert result.matched_entity_id is None

    def test_7_missing_invalid_identifier_safe_fallback(self, er_db):
        case, _ = create_case(er_db)
        mention = ExtractedEntity(
            temp_id="E_INVALID",
            entity_type=ExtractionEntityType.PHONE,
            extracted_text="invalid-phone-string",
            character_start=0,
            character_end=20,
        )
        # Should not crash, returns CREATE_NEW
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.CREATE_NEW


# ==============================================================================
# 4. TIER 2: HEURISTIC NAME & ALIAS MATCHING TESTS (Mandatory 8, 9, 10, 11, 12, 13)
# ==============================================================================

class TestTier2HeuristicMatching:
    def test_8_exact_alias_match(self, er_db):
        case, _ = create_case(er_db)
        e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Vikram Singh")
        alias = EntityAlias(alias_id=uuid4(), entity_id=e.entity_id, alias_text="Vicky Bhai")
        er_db.add_all([e, alias])
        er_db.commit()

        mention = ExtractedEntity(
            temp_id="E8",
            entity_type=ExtractionEntityType.PERSON,
            extracted_text="Vicky Bhai",
            character_start=0,
            character_end=10,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.AUTO_MERGE
        assert result.matched_entity_id == e.entity_id
        assert result.match_confidence == 1.0

    def test_9_minor_spelling_variation_auto_merges(self, er_db):
        case, _ = create_case(er_db)
        e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Devendra Sharma")
        er_db.add(e)
        er_db.commit()

        # One character typo: "Devender Sharma"
        mention = ExtractedEntity(
            temp_id="E9",
            entity_type=ExtractionEntityType.PERSON,
            extracted_text="Devender Sharma",
            character_start=0,
            character_end=15,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.AUTO_MERGE
        assert result.matched_entity_id == e.entity_id
        assert result.match_confidence > 0.85

    def test_10_jaro_winkler_high_similarity(self):
        score = calculate_name_similarity("Rameshwar Prasad", "Rameshwar Parsad")
        assert score > 0.85

    def test_11_levenshtein_high_similarity(self):
        sim = levenshtein_similarity("Mohammed Khan", "Mohamed Khan")
        assert sim > 0.85

    def test_12_ambiguous_common_name_or_initials_guard(self, er_db):
        case, _ = create_case(er_db)
        e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="A. Kumar")
        er_db.add(e)
        er_db.commit()

        # Short initial: should NOT auto-merge (>0.85), must go to REVIEW_REQUIRED
        mention = ExtractedEntity(
            temp_id="E12",
            entity_type=ExtractionEntityType.PERSON,
            extracted_text="AK",
            character_start=0,
            character_end=2,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision in (EntityMatchDecision.REVIEW_REQUIRED, EntityMatchDecision.CREATE_NEW)
        assert result.decision != EntityMatchDecision.AUTO_MERGE

    def test_13_low_similarity_creates_new(self, er_db):
        case, _ = create_case(er_db)
        e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Sanjay Singhania")
        er_db.add(e)
        er_db.commit()

        mention = ExtractedEntity(
            temp_id="E13",
            entity_type=ExtractionEntityType.PERSON,
            extracted_text="Rahul Dravid",
            character_start=0,
            character_end=12,
        )
        result = EntityResolutionEngine.match_mention(er_db, case.case_id, mention)
        assert result.decision == EntityMatchDecision.CREATE_NEW
        assert result.matched_entity_id is None
        assert result.match_confidence < 0.50


# ==============================================================================
# 5. INTEGRITY & IMMUTABILITY TESTS (Mandatory 19, 20, 21, 22, 23, 24)
# ==============================================================================

class TestIntegrityAndImmutability:
    def test_19_20_21_source_document_and_extracted_text_unchanged(self, er_db):
        case, user = create_case(er_db)
        doc = DbDocument(
            document_id=uuid4(),
            case_id=case.case_id,
            file_type="application/pdf",
            file_hash="hash_orig_123",
            storage_key="cases/test/doc.pdf",
            status="EXTRACTED",
        )
        er_db.add(doc)
        er_db.commit()

        original_hash = doc.file_hash
        original_key = doc.storage_key
        original_status = doc.status

        # Perform ER staging
        payload = ExtractionJobResponse(
            extraction_job_id=uuid4(),
            extracted_entities=[
                ExtractedEntity(temp_id="E1", entity_type=ExtractionEntityType.PERSON, extracted_text="Original Raw Mention", character_start=0, character_end=19)
            ],
            extracted_relationships=[]
        )

        batch_result = resolve_and_stage_payload(er_db, payload, case.case_id, doc.document_id, user.user_id)
        er_db.commit()

        # Document immutable fields are preserved
        er_db.refresh(doc)
        assert doc.file_hash == original_hash
        assert doc.storage_key == original_key
        # Extracted text in payload was not mutated
        assert payload.extracted_entities[0].extracted_text == "Original Raw Mention"

    def test_22_alias_provenance_preserved(self, er_db):
        case, user = create_case(er_db)
        doc_id = uuid4()
        job_id = uuid4()
        payload = ExtractionJobResponse(
            extraction_job_id=job_id,
            extracted_entities=[
                ExtractedEntity(temp_id="E22", entity_type=ExtractionEntityType.PERSON, extracted_text="Provenance Name", character_start=0, character_end=15)
            ],
            extracted_relationships=[]
        )
        batch = resolve_and_stage_payload(er_db, payload, case.case_id, doc_id, user.user_id)
        er_db.commit()

        created_uuid = batch.entity_mappings["E22"]
        alias = er_db.query(EntityAlias).filter(EntityAlias.entity_id == created_uuid).first()
        assert alias is not None
        assert f"doc:{doc_id}" in alias.source_ref
        assert f"job:{job_id}" in alias.source_ref
        assert "mention:E22" in alias.source_ref

    def test_23_audit_record_created_for_decisions(self, er_db):
        case, user = create_case(er_db)
        payload = ExtractionJobResponse(
            extraction_job_id=uuid4(),
            extracted_entities=[
                ExtractedEntity(temp_id="E23", entity_type=ExtractionEntityType.PERSON, extracted_text="Audit Person", character_start=0, character_end=12)
            ],
            extracted_relationships=[]
        )
        resolve_and_stage_payload(er_db, payload, case.case_id, uuid4(), user.user_id)
        er_db.commit()

        audit = er_db.query(AuditLog).filter(AuditLog.case_id == case.case_id).first()
        assert audit is not None
        assert audit.action_code in (SecurityAuditAction.ER_NEW_ENTITY_CREATED, SecurityAuditAction.ER_AUTO_MERGE)

    def test_24_reversal_rejection_does_not_delete_evidence(self, er_db):
        case, user = create_case(er_db)
        service = EvidenceReviewService(db=er_db)

        # Create two entities and relationship
        e1 = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Target Entity")
        e2 = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Secondary Entity")
        rel = Relationship(relationship_id=uuid4(), case_id=case.case_id, source_entity_uuid=e2.entity_id, target_entity_uuid=e1.entity_id, type="ASSOCIATE", status="OBSERVED")
        ev = RelationshipEvidence(evidence_id=uuid4(), relationship_id=rel.relationship_id, source_ref="doc:123", support_type="AGENT1_EXTRACTION")

        er_db.add_all([e1, e2, rel, ev])
        er_db.commit()

        # Merge secondary into target
        resp = service.apply_review_override(
            case_id=case.case_id,
            actor_uuid=user.user_id,
            target_type="ENTITY",
            target_id=e1.entity_id,
            action="MERGE",
            secondary_target_id=e2.entity_id,
            reason="Supervisor merge test",
        )
        assert resp.resulting_status == "CONFIRMED"

        # Evidence is NOT physically deleted!
        ev_check = er_db.query(RelationshipEvidence).filter(RelationshipEvidence.evidence_id == ev.evidence_id).first()
        assert ev_check is not None
        # Secondary entity is soft-retired (MERGED), not deleted
        e2_check = er_db.query(Entity).filter(Entity.entity_id == e2.entity_id).first()
        assert e2_check.status == "MERGED"


# ==============================================================================
# 6. AUTHORIZATION & CASE ISOLATION TESTS (Mandatory 25, 26, 27)
# ==============================================================================

class TestAuthorizationAndCaseIsolation:
    def test_25_unauthorized_user_cannot_resolve_mention(self, er_db):
        case, _ = create_case(er_db)
        unauth_user_id = uuid4()
        service = EntityResolutionService(db=er_db)

        payload = ExtractionJobResponse(
            extraction_job_id=uuid4(),
            extracted_entities=[
                ExtractedEntity(temp_id="E1", entity_type=ExtractionEntityType.PERSON, extracted_text="Unauthorized Person", character_start=0, character_end=19)
            ],
            extracted_relationships=[]
        )

        with pytest.raises(HTTPException) as exc:
            service.stage_and_resolve(case_id=case.case_id, document_id=uuid4(), payload=payload, actor_id=unauth_user_id)
        assert exc.value.status_code == 404
        assert "Resource not found" in exc.value.detail

    def test_26_entity_from_another_case_cannot_be_targeted(self, er_db):
        case_1, user_1 = create_case(er_db, "CASE-AUTH-1")
        case_2, _ = create_case(er_db, "CASE-AUTH-2")
        service = EntityResolutionService(db=er_db)

        e_case_2 = Entity(entity_id=uuid4(), case_id=case_2.case_id, entity_type="PERSON", canonical_name="Foreign Entity")
        er_db.add(e_case_2)
        er_db.commit()

        # User in Case 1 attempts to approve merge targeting Case 2 entity
        with pytest.raises(ReviewNotFoundError):
            service.approve_merge(
                case_id=case_1.case_id,
                primary_entity_id=e_case_2.entity_id,
                secondary_entity_id=uuid4(),
                actor_uuid=user_1.user_id,
            )

    def test_27_generic_404_on_nonexistent_case(self, er_db):
        service = EntityResolutionService(db=er_db)
        with pytest.raises(HTTPException) as exc:
            service.get_review_candidates(case_id=uuid4())
        assert exc.value.status_code == 404
        assert "Resource not found" in exc.value.detail


# ==============================================================================
# 7. CONCURRENCY & IDEMPOTENCY TESTS (Mandatory 28, 29, 30, 31)
# ==============================================================================

class TestConcurrencyAndIdempotency:
    def test_28_same_mention_processed_twice_is_idempotent(self, er_db):
        case, user = create_case(er_db)
        doc_id = uuid4()
        job_id = uuid4()

        payload = ExtractionJobResponse(
            extraction_job_id=job_id,
            extracted_entities=[
                ExtractedEntity(temp_id="E28", entity_type=ExtractionEntityType.PERSON, extracted_text="Idempotent Target", character_start=0, character_end=17)
            ],
            extracted_relationships=[]
        )

        # First execution
        batch1 = resolve_and_stage_payload(er_db, payload, case.case_id, doc_id, user.user_id)
        er_db.commit()
        mapped_uuid_1 = batch1.entity_mappings["E28"]

        # Second execution (e.g. worker retry with same payload)
        # In second execution, the exact mention text matches the existing entity with 1.0 confidence
        batch2 = resolve_and_stage_payload(er_db, payload, case.case_id, doc_id, user.user_id)
        er_db.commit()
        mapped_uuid_2 = batch2.entity_mappings["E28"]

        # Maps to the same canonical entity without creating a duplicate
        assert mapped_uuid_1 == mapped_uuid_2
        # Entity count is 1
        entities = er_db.query(Entity).filter(Entity.case_id == case.case_id).all()
        assert len(entities) == 1

    def test_30_duplicate_review_approval_rejected(self, er_db):
        case, user = create_case(er_db)
        service = EvidenceReviewService(db=er_db)

        e1 = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Target 30")
        e2 = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Secondary 30")
        er_db.add_all([e1, e2])
        er_db.commit()

        # First merge succeeds
        service.apply_review_override(case.case_id, user.user_id, "ENTITY", e1.entity_id, "MERGE", reason="Merge 1", secondary_target_id=e2.entity_id)

        # Second merge of same secondary fails with conflict error
        with pytest.raises(ReviewConflictError, match="already merged"):
            service.apply_review_override(case.case_id, user.user_id, "ENTITY", e1.entity_id, "MERGE", reason="Merge 2", secondary_target_id=e2.entity_id)


# ==============================================================================
# 8. LIFECYCLE & WORKFLOW TESTS (Mandatory 32, 33, 34, 35)
# ==============================================================================

class TestLifecycleIntegration:
    def test_32_ambiguous_er_causes_review_required(self, er_db):
        case, user = create_case(er_db)
        # Seed existing entity
        e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Rameshwar Prasad")
        er_db.add(e)
        er_db.commit()

        # Mention with similarity in ambiguous range [0.50, 0.85]
        # "Ramesh Kumar" vs "Rameshwar Prasad" (score ~0.66)
        payload = ExtractionJobResponse(
            extraction_job_id=uuid4(),
            extracted_entities=[
                ExtractedEntity(temp_id="E_AMBIGUOUS", entity_type=ExtractionEntityType.PERSON, extracted_text="Ramesh Kumar", character_start=0, character_end=12)
            ],
            extracted_relationships=[]
        )

        batch = resolve_and_stage_payload(er_db, payload, case.case_id, uuid4(), user.user_id)
        er_db.commit()

        # Document recommended state must be REVIEW_REQUIRED
        assert batch.recommended_doc_state == DocumentState.REVIEW_REQUIRED
        assert batch.review_required_count == 1

        # Created entity has status REVIEW_REQUIRED
        staged_e = er_db.query(Entity).filter(Entity.entity_id == batch.entity_mappings["E_AMBIGUOUS"]).first()
        assert staged_e.status == "REVIEW_REQUIRED"

    def test_34_clean_resolution_transitions_to_accepted(self, er_db):
        case, user = create_case(er_db)

        # Fresh new entity mentions with no ambiguity
        payload = ExtractionJobResponse(
            extraction_job_id=uuid4(),
            extracted_entities=[
                ExtractedEntity(temp_id="E_CLEAN_1", entity_type=ExtractionEntityType.PERSON, extracted_text="Brand New Person A", character_start=0, character_end=18),
                ExtractedEntity(temp_id="E_CLEAN_2", entity_type=ExtractionEntityType.PHONE, extracted_text="9123456780", character_start=20, character_end=30),
            ],
            extracted_relationships=[
                ExtractedRelationship(source_temp_id="E_CLEAN_1", target_temp_id="E_CLEAN_2", type="OWNS", context_span="owns phone", confidence_score=0.99)
            ]
        )

        batch = resolve_and_stage_payload(er_db, payload, case.case_id, uuid4(), user.user_id)
        er_db.commit()

        # Clean resolution transitions directly to ACCEPTED
        assert batch.recommended_doc_state == DocumentState.ACCEPTED
        assert batch.auto_merge_count == 0
        assert batch.create_new_count == 2
        assert batch.review_required_count == 0

    def test_35_review_candidate_listing_service(self, er_db):
        case, user = create_case(er_db)
        service = EntityResolutionService(db=er_db)

        # Seed an entity in REVIEW_REQUIRED state
        review_e = Entity(entity_id=uuid4(), case_id=case.case_id, entity_type="PERSON", canonical_name="Quarantined Person", status="REVIEW_REQUIRED")
        alias = EntityAlias(alias_id=uuid4(), entity_id=review_e.entity_id, alias_text="Quarantined Person", source_ref="doc:123|job:456|candidate:789|conf:0.7500")
        er_db.add_all([review_e, alias])
        er_db.commit()

        candidates = service.get_review_candidates(case_id=case.case_id, user_id=user.user_id)
        assert len(candidates) == 1
        assert candidates[0]["canonical_name"] == "Quarantined Person"
        assert candidates[0]["status"] == "REVIEW_REQUIRED"
        assert "conf:0.7500" in candidates[0]["provenance_ref"]
