"""
Unit tests for Dev B Part 2 Domain Repositories and Pydantic DTOs.
Verifies:
1. Evidence Repository: case-scoped retrieval, cross-case blocking, provenance offsets, source immutability.
2. Review Repository: entity merge confirmation, alias deduplication, relationship redirection, source immutability, merge rejection, cross-case rejection, self-merge blocking.
3. Audit Repository: append-only ledger, case-scoped listing, cross-case blocking, immutability (prohibited updates/deletes), PII masking, token/secret redaction.
4. Export Repository: case-scoped ledger creation, artifact ref & hash preservation, cross-case access blocking.
5. DTO Validation: ReviewRequest validation, canonical & legacy target_types, action validation, symmetric reason/override_notes reconciliation, ApiResponse envelope validation.
"""

from datetime import datetime, timezone
import pytest
from uuid import UUID, uuid4
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.base import Base
from backend.db.models.identity import Case, User
from backend.db.models.entities import (
    Entity,
    EntityAlias,
    EntityIdentifier,
    Relationship,
    RelationshipEvidence,
)
from backend.db.models.ingestion import Document, DocumentChunk, DocumentVersion
from backend.db.models.analytics import AuditLog, Export
from backend.domain.errors import (
    CaseIsolationViolationError,
    DuplicateMergeError,
    EntityNotFoundError,
    ImmutableRecordViolationError,
    InvalidReviewActionError,
)
from backend.domain.redaction import redact_sensitive_text
from backend.repositories.evidence_repository import EvidenceRepository, parse_character_span
from backend.repositories.review_repository import ReviewRepository
from backend.repositories.audit_repository import AuditRepository
from backend.repositories.export_repository import ExportRepository
from backend.schemas.envelope import (
    ApiResponse,
    ApiSuccessResponse,
    ApiErrorResponse,
    envelope_success,
    envelope_error,
)
from backend.schemas.evidence_analysis import (
    ReviewAction,
    ReviewRequest,
    ReviewResponse,
    ReviewTargetType,
)
from backend.schemas.audit import (
    AuditCreate,
    AuditFilterParams,
    AuditLogItem,
    CaseAuditResponse,
)
from backend.schemas.export import (
    ExportCreate,
    ExportRequest,
    ExportResponse,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def db_engine():
    """Isolated SQLite in-memory test database with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Isolated database session per test with automatic rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = session_factory()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def test_data(db_session: Session):
    """Sets up two isolated cases (Case A and Case B) with entities and evidence."""
    # User
    user = User(
        user_id=uuid4(),
        email="analyst@agency.gov",
        username="analyst_1",
        password_hash="argon2_test_hash",
        account_status="ACTIVE",
    )
    db_session.add(user)

    # Case A
    case_a = Case(
        case_id=uuid4(),
        case_code="CASE-ALPHA-01",
        title="Operation Alpha",
        status="ACTIVE",
        jurisdiction="CENTRAL",
        created_by=user.user_id,
    )
    # Case B
    case_b = Case(
        case_id=uuid4(),
        case_code="CASE-BRAVO-02",
        title="Operation Bravo",
        status="ACTIVE",
        jurisdiction="NORTH",
        created_by=user.user_id,
    )
    db_session.add_all([case_a, case_b])

    # Entities in Case A
    entity_a1 = Entity(
        entity_id=uuid4(),
        case_id=case_a.case_id,
        entity_type="PERSON",
        canonical_name="Vikram Singh",
        status="ACTIVE",
    )
    entity_a2 = Entity(
        entity_id=uuid4(),
        case_id=case_a.case_id,
        entity_type="PERSON",
        canonical_name="V. Singh (Alias Candidate)",
        status="ACTIVE",
    )
    # Entity in Case B
    entity_b1 = Entity(
        entity_id=uuid4(),
        case_id=case_b.case_id,
        entity_type="PERSON",
        canonical_name="Rohan Verma",
        status="ACTIVE",
    )
    db_session.add_all([entity_a1, entity_a2, entity_b1])

    # Identifiers
    id_a2 = EntityIdentifier(
        identifier_id=uuid4(),
        entity_id=entity_a2.entity_id,
        type="PHONE_NUMBER",
        normalized_value_hash="hash_phone_9999",
        value_policy="RESTRICTED",
    )
    db_session.add(id_a2)

    # Relationship in Case A
    rel_a = Relationship(
        relationship_id=uuid4(),
        case_id=case_a.case_id,
        source_entity_uuid=entity_a1.entity_id,
        target_entity_uuid=entity_a2.entity_id,
        type="COMMUNICATED_WITH",
        status="OBSERVED",
    )
    # Relationship in Case B
    rel_b = Relationship(
        relationship_id=uuid4(),
        case_id=case_b.case_id,
        source_entity_uuid=entity_b1.entity_id,
        target_entity_uuid=entity_b1.entity_id,
        type="OWNS",
        status="OBSERVED",
    )
    db_session.add_all([rel_a, rel_b])

    # Documents & Chunks in Case A
    doc_a = Document(
        document_id=uuid4(),
        case_id=case_a.case_id,
        file_type="PDF",
        file_hash="sha256_case_a_doc",
        storage_key="cases/a/fir_01.pdf",
        status="EXTRACTED",
    )
    db_session.add(doc_a)

    ver_a = DocumentVersion(
        version_id=uuid4(),
        document_id=doc_a.document_id,
        version_hash="verhash_001",
        meta={"page_count": 5},
    )
    db_session.add(ver_a)

    chunk_a = DocumentChunk(
        chunk_id=uuid4(),
        version_id=ver_a.version_id,
        page_number=2,
        character_span="120-350",
        text_hash="chunkhash_120_350",
        storage_ref="storage/chunks/chunk_01.txt",
    )
    db_session.add(chunk_a)

    # Evidence linking relationship in Case A to chunk
    evidence_a = RelationshipEvidence(
        evidence_id=uuid4(),
        relationship_id=rel_a.relationship_id,
        source_ref=str(chunk_a.chunk_id),
        support_type="CDR_ROW",
    )
    # Evidence in Case B
    evidence_b = RelationshipEvidence(
        evidence_id=uuid4(),
        relationship_id=rel_b.relationship_id,
        source_ref="CASE_B_EXTERNAL_REF",
        support_type="FIR_PARAGRAPH",
    )
    db_session.add_all([evidence_a, evidence_b])

    db_session.commit()

    return {
        "user": user,
        "case_a": case_a,
        "case_b": case_b,
        "entity_a1": entity_a1,
        "entity_a2": entity_a2,
        "entity_b1": entity_b1,
        "rel_a": rel_a,
        "rel_b": rel_b,
        "doc_a": doc_a,
        "ver_a": ver_a,
        "chunk_a": chunk_a,
        "evidence_a": evidence_a,
        "evidence_b": evidence_b,
    }


# ==============================================================================
# 1. EVIDENCE REPOSITORY TESTS
# ==============================================================================

class TestEvidenceRepository:
    """Verifies evidence retrieval, case scoping, and provenance tracking."""

    def test_retrieve_case_scoped_evidence_success(self, db_session: Session, test_data: dict):
        repo = EvidenceRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        ev_a_id = test_data["evidence_a"].evidence_id

        evidence = repo.get_evidence_by_id(case_id=case_a_id, evidence_id=ev_a_id)
        assert evidence is not None
        assert evidence.evidence_id == ev_a_id
        assert evidence.support_type == "CDR_ROW"

    def test_cross_case_evidence_retrieval_blocked(self, db_session: Session, test_data: dict):
        repo = EvidenceRepository(db_session)
        case_b_id = test_data["case_b"].case_id
        ev_a_id = test_data["evidence_a"].evidence_id

        # Case B cannot retrieve Case A's evidence
        evidence = repo.get_evidence_by_id(case_id=case_b_id, evidence_id=ev_a_id)
        assert evidence is None

    def test_list_relationship_evidence_case_scoped(self, db_session: Session, test_data: dict):
        repo = EvidenceRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        rel_a_id = test_data["rel_a"].relationship_id

        citations = repo.list_relationship_evidence(case_id=case_a_id, relationship_id=rel_a_id)
        assert len(citations) == 1
        assert citations[0].evidence_id == test_data["evidence_a"].evidence_id

        # Attempt with wrong case returns empty list
        citations_wrong = repo.list_relationship_evidence(
            case_id=test_data["case_b"].case_id, relationship_id=rel_a_id
        )
        assert len(citations_wrong) == 0

    def test_chunk_provenance_and_character_offsets(self, db_session: Session, test_data: dict):
        repo = EvidenceRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        chunk_id = test_data["chunk_a"].chunk_id

        prov = repo.get_chunk_provenance(case_id=case_a_id, chunk_id=chunk_id)
        assert prov is not None
        assert prov["page_number"] == 2
        assert prov["character_start"] == 120
        assert prov["character_end"] == 350
        assert prov["version_hash"] == "verhash_001"
        assert prov["file_hash"] == "sha256_case_a_doc"

    def test_cross_case_chunk_provenance_blocked(self, db_session: Session, test_data: dict):
        repo = EvidenceRepository(db_session)
        case_b_id = test_data["case_b"].case_id
        chunk_id = test_data["chunk_a"].chunk_id

        # Case B cannot retrieve Case A chunk provenance
        prov = repo.get_chunk_provenance(case_id=case_b_id, chunk_id=chunk_id)
        assert prov is None

    def test_evidence_provenance_response(self, db_session: Session, test_data: dict):
        repo = EvidenceRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        ev_a_id = test_data["evidence_a"].evidence_id

        res = repo.get_evidence_provenance(case_id=case_a_id, evidence_id=ev_a_id)
        assert res is not None
        assert res.evidence_id == ev_a_id
        assert res.chunk_id == test_data["chunk_a"].chunk_id
        assert res.character_start == 120
        assert res.character_end == 350

    def test_raw_source_remains_immutable_on_query(self, db_session: Session, test_data: dict):
        repo = EvidenceRepository(db_session)
        chunk = test_data["chunk_a"]
        orig_hash = chunk.text_hash
        orig_span = chunk.character_span

        _ = repo.get_chunk_provenance(case_id=test_data["case_a"].case_id, chunk_id=chunk.chunk_id)

        db_session.refresh(chunk)
        assert chunk.text_hash == orig_hash
        assert chunk.character_span == orig_span


# ==============================================================================
# 2. REVIEW & ENTITY RESOLUTION REPOSITORY TESTS
# ==============================================================================

class TestReviewRepository:
    """Verifies entity merge confirmation, alias deduplication, and merge rejection."""

    def test_confirm_entity_merge_success(self, db_session: Session, test_data: dict):
        repo = ReviewRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        target_id = test_data["entity_a1"].entity_id
        secondary_id = test_data["entity_a2"].entity_id
        actor_id = test_data["user"].user_id

        res = repo.confirm_entity_merge(
            case_id=case_a_id,
            target_entity_id=target_id,
            secondary_entity_id=secondary_id,
            actor_uuid=actor_id,
            override_notes="Confirmed fingerprinted alias merge",
        )

        assert res.action == "CONFIRM"
        assert res.status == "CONFIRMED"
        assert res.target_id == target_id
        assert res.secondary_target_id == secondary_id

        # Check secondary entity is marked MERGED
        secondary = db_session.query(Entity).filter(Entity.entity_id == secondary_id).first()
        assert secondary.status == "MERGED"

        # Check alias was appended to target
        aliases = db_session.query(EntityAlias).filter(EntityAlias.entity_id == target_id).all()
        alias_texts = [a.alias_text for a in aliases]
        assert "V. Singh (Alias Candidate)" in alias_texts

        # Check identifier was re-pointed to target
        ident = db_session.query(EntityIdentifier).filter(EntityIdentifier.entity_id == target_id).first()
        assert ident is not None
        assert ident.normalized_value_hash == "hash_phone_9999"

        # Check relationship was updated
        rel = db_session.query(Relationship).filter(Relationship.relationship_id == test_data["rel_a"].relationship_id).first()
        # It connected a1 and a2; since a2 merged into a1, this became a self-loop
        assert rel.status == "MERGED_SELF_LOOP"

        # Check audit entry created
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.case_id == case_a_id, AuditLog.action_code == "ENTITY_MERGE")
            .first()
        )
        assert audit is not None
        assert audit.outcome == "CONFIRMED"

    def test_prevent_duplicate_alias_insertion_on_merge(self, db_session: Session, test_data: dict):
        repo = ReviewRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        target_id = test_data["entity_a1"].entity_id
        secondary_id = test_data["entity_a2"].entity_id
        actor_id = test_data["user"].user_id

        # Pre-seed identical alias on target
        existing = EntityAlias(
            alias_id=uuid4(),
            entity_id=target_id,
            alias_text="V. Singh (Alias Candidate)",
            source_ref="PRE_EXISTING",
        )
        db_session.add(existing)
        db_session.commit()

        # Run merge
        repo.confirm_entity_merge(
            case_id=case_a_id,
            target_entity_id=target_id,
            secondary_entity_id=secondary_id,
            actor_uuid=actor_id,
            override_notes="Duplicate alias test",
        )

        # Ensure no duplicate alias created with identical text
        matching_aliases = (
            db_session.query(EntityAlias)
            .filter(
                EntityAlias.entity_id == target_id,
                EntityAlias.alias_text == "V. Singh (Alias Candidate)",
            )
            .all()
        )
        assert len(matching_aliases) == 1

    def test_reject_entity_merge_preserves_separation(self, db_session: Session, test_data: dict):
        repo = ReviewRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        target_id = test_data["entity_a1"].entity_id
        secondary_id = test_data["entity_a2"].entity_id
        actor_id = test_data["user"].user_id

        res = repo.reject_entity_merge(
            case_id=case_a_id,
            target_entity_id=target_id,
            secondary_entity_id=secondary_id,
            actor_uuid=actor_id,
            override_notes="Different people with identical names",
        )

        assert res.action == "REJECT"
        assert res.status == "REJECTED"

        # Secondary entity status remains ACTIVE
        secondary = db_session.query(Entity).filter(Entity.entity_id == secondary_id).first()
        assert secondary.status == "ACTIVE"

        # No alias appended to target
        aliases = db_session.query(EntityAlias).filter(EntityAlias.entity_id == target_id).all()
        assert len(aliases) == 0

        # Audit recorded as REJECTED
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.case_id == case_a_id, AuditLog.action_code == "ENTITY_MERGE_REJECT")
            .first()
        )
        assert audit is not None
        assert audit.outcome == "REJECTED"

    def test_cross_case_entity_merge_rejected(self, db_session: Session, test_data: dict):
        repo = ReviewRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        target_id = test_data["entity_a1"].entity_id
        secondary_id = test_data["entity_b1"].entity_id  # In Case B!
        actor_id = test_data["user"].user_id

        with pytest.raises(EntityNotFoundError):
            repo.confirm_entity_merge(
                case_id=case_a_id,
                target_entity_id=target_id,
                secondary_entity_id=secondary_id,
                actor_uuid=actor_id,
            )

    def test_self_merge_blocked(self, db_session: Session, test_data: dict):
        repo = ReviewRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        target_id = test_data["entity_a1"].entity_id
        actor_id = test_data["user"].user_id

        with pytest.raises(DuplicateMergeError):
            repo.confirm_entity_merge(
                case_id=case_a_id,
                target_entity_id=target_id,
                secondary_entity_id=target_id,
                actor_uuid=actor_id,
            )


# ==============================================================================
# 3. AUDIT REPOSITORY TESTS
# ==============================================================================

class TestAuditRepository:
    """Verifies append-only audit trail, case scoping, and PII/token redaction."""

    def test_append_audit_event_success(self, db_session: Session, test_data: dict):
        repo = AuditRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        user_id = test_data["user"].user_id

        entry = repo.append_audit_event(
            actor_uuid=user_id,
            action_code="CASE_VIEW",
            case_id=case_a_id,
            target_item="Opened investigation canvas",
            outcome="SUCCESS",
        )
        assert entry.audit_id is not None
        assert entry.action_code == "CASE_VIEW"
        assert entry.case_id == case_a_id

    def test_case_scoped_audit_listing(self, db_session: Session, test_data: dict):
        repo = AuditRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        case_b_id = test_data["case_b"].case_id
        user_id = test_data["user"].user_id

        # Insert 2 events in Case A and 1 in Case B
        repo.append_audit_event(actor_uuid=user_id, action_code="ACTION_A1", case_id=case_a_id)
        repo.append_audit_event(actor_uuid=user_id, action_code="ACTION_A2", case_id=case_a_id)
        repo.append_audit_event(actor_uuid=user_id, action_code="ACTION_B1", case_id=case_b_id)

        logs_a, total_a = repo.list_case_audit_logs(case_id=case_a_id)
        assert total_a == 2
        assert all(log.case_id == case_a_id for log in logs_a)

        logs_b, total_b = repo.list_case_audit_logs(case_id=case_b_id)
        assert total_b == 1
        assert logs_b[0].case_id == case_b_id

    def test_audit_immutability_prohibits_update_and_delete(self, db_session: Session):
        repo = AuditRepository(db_session)

        with pytest.raises(ImmutableRecordViolationError):
            repo.update_audit_log()

        with pytest.raises(ImmutableRecordViolationError):
            repo.delete_audit_log()

    def test_pii_and_token_redaction_on_write(self, db_session: Session, test_data: dict):
        repo = AuditRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        user_id = test_data["user"].user_id

        # Raw string with Phone Number, Bearer Token, Credit Card, and Password
        raw_text = (
            "User called +91 9876543210 with Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakSig "
            "using card 4111222233334444 and password=SuperSecretPassword123"
        )

        entry = repo.append_audit_event(
            actor_uuid=user_id,
            action_code="SENSITIVE_CALL",
            case_id=case_a_id,
            target_item=raw_text,
            outcome="SUCCESS",
        )

        # Verify sensitive info is masked / redacted in stored DB record
        assert "SuperSecretPassword123" not in entry.target_item
        assert "Bearer eyJhbGci" not in entry.target_item
        assert "4111222233334444" not in entry.target_item
        assert "9876543210" not in entry.target_item

        assert "[REDACTED" in entry.target_item
        assert "****" in entry.target_item


# ==============================================================================
# 4. EXPORT REPOSITORY TESTS
# ==============================================================================

class TestExportRepository:
    """Verifies case export ledger persistence and cross-case access controls."""

    def test_create_export_record_success(self, db_session: Session, test_data: dict):
        repo = ExportRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        user_id = test_data["user"].user_id

        export = repo.create_export(
            case_id=case_a_id,
            user_uuid=user_id,
            artifact_ref="storage/exports/case_a_report.pdf",
            version_hash="sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        )

        assert export.export_id is not None
        assert export.case_id == case_a_id
        assert export.artifact_ref == "storage/exports/case_a_report.pdf"
        assert export.version_hash.startswith("sha256:")

    def test_case_scoped_export_lookup(self, db_session: Session, test_data: dict):
        repo = ExportRepository(db_session)
        case_a_id = test_data["case_a"].case_id
        case_b_id = test_data["case_b"].case_id
        user_id = test_data["user"].user_id

        export_a = repo.create_export(
            case_id=case_a_id,
            user_uuid=user_id,
            artifact_ref="storage/exports/a.pdf",
            version_hash="hash_a",
        )

        # Same case can retrieve
        fetched = repo.get_export_by_id(case_id=case_a_id, export_id=export_a.export_id)
        assert fetched is not None
        assert fetched.export_id == export_a.export_id

        # Different case is blocked (returns None)
        cross_fetched = repo.get_export_by_id(case_id=case_b_id, export_id=export_a.export_id)
        assert cross_fetched is None


# ==============================================================================
# 5. DTO VALIDATION & ENVELOPE TESTS
# ==============================================================================

class TestDtoAndEnvelopeContracts:
    """Verifies Pydantic DTO validation, ReviewRequest compatibility, and envelope specs."""

    def test_review_request_with_override_notes(self):
        req = ReviewRequest(
            target_id=uuid4(),
            target_type="ENTITY_RESOLUTION",
            action="CONFIRM",
            override_notes="Validated via fingerprint analysis",
        )
        assert req.override_notes == "Validated via fingerprint analysis"
        # Reason was symmetrically populated
        assert req.reason == "Validated via fingerprint analysis"

    def test_review_request_with_reason(self):
        req = ReviewRequest(
            target_id=uuid4(),
            target_type="ENTITY_RESOLUTION",
            action="REJECT",
            reason="Different individuals",
        )
        assert req.reason == "Different individuals"
        # override_notes was symmetrically populated
        assert req.override_notes == "Different individuals"

    def test_review_request_missing_justification_fails(self):
        with pytest.raises(ValidationError):
            ReviewRequest(
                target_id=uuid4(),
                target_type="ENTITY_RESOLUTION",
                action="CONFIRM",
            )

    def test_review_request_invalid_target_type_fails(self):
        with pytest.raises(ValidationError):
            ReviewRequest(
                target_id=uuid4(),
                target_type="INVALID_TYPE",
                action="CONFIRM",
                reason="Valid justification",
            )

    def test_review_request_invalid_action_fails(self):
        with pytest.raises(ValidationError):
            ReviewRequest(
                target_id=uuid4(),
                target_type="ENTITY_RESOLUTION",
                action="INVALID_ACTION",
                reason="Valid justification",
            )

    def test_api_success_envelope_has_request_and_tracking_id(self):
        payload = {"status": "ok", "count": 42}
        resp = envelope_success(data=payload, request_id="custom-req-id-123")

        assert resp.success is True
        assert resp.data == payload
        assert resp.request_id == "custom-req-id-123"
        assert resp.tracking_id == "custom-req-id-123"

    def test_api_error_envelope_has_request_and_tracking_id(self):
        err = envelope_error(
            code="RESOURCE_NOT_FOUND",
            message="Entity does not exist",
            tracking_id="trace-uuid-456",
        )
        assert err.success is False
        assert err.error.code == "RESOURCE_NOT_FOUND"
        assert err.request_id == "trace-uuid-456"
        assert err.tracking_id == "trace-uuid-456"
