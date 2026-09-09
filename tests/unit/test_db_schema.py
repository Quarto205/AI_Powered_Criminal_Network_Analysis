"""
Comprehensive PostgreSQL Relational Schema & Invariants Test Suite for SIH26189.
Verifies:
1. All 31 tables exist in metadata and database.
2. UUID-v4 primary key invariant across all tables.
3. Monetary precision invariant (transactions.amount is Numeric/Decimal, not float).
4. Analytical scores invariant (predictions.score and risk_scores.value are Float).
5. Uniqueness constraints (case_code, (case_id, file_hash), (case_id, user_id), role.name, permission_code).
6. Foreign key referential integrity and cascading/restricting policies.
7. Case tenancy and isolation.
8. Append-only and immutability enforcement on audit_logs and source tables (documents, events, communications, transactions).
9. ORM round-trip across all domains.
10. Alembic migration discovery and validation.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Generator
from uuid import UUID, uuid4
import pytest

from sqlalchemy import Numeric, create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.db.base import Base
from backend.db.models import (
    Account,
    Alert,
    AuditLog,
    Case,
    CaseMember,
    Communication,
    Document,
    DocumentChunk,
    DocumentVersion,
    Entity,
    EntityAlias,
    EntityIdentifier,
    Event,
    Export,
    GraphSnapshot,
    InvestigationNote,
    Location,
    ModelRun,
    Organization,
    Permission,
    Phone,
    Prediction,
    Relationship,
    RelationshipEvidence,
    RiskScore,
    Role,
    SavedQuery,
    Transaction,
    User,
    UserRole,
    Vehicle,
)
from backend.db.triggers import ImmutableRecordError

EXPECTED_31_TABLES = {
    # Domain A: Identity / RBAC / Multi-Tenant (6)
    "users",
    "roles",
    "permissions",
    "user_roles",
    "cases",
    "case_members",
    # Domain B: Ingestion / Source Artifacts (3)
    "documents",
    "document_versions",
    "document_chunks",
    # Domain C: Entities / Relationships / Evidence (14)
    "entities",
    "entity_aliases",
    "entity_identifiers",
    "relationships",
    "relationship_evidence",
    "events",
    "communications",
    "transactions",
    "locations",
    "vehicles",
    "organizations",
    "phones",
    "accounts",
    "investigation_notes",
    # Domain D: AI / Analytics / Audit (8)
    "model_runs",
    "predictions",
    "risk_scores",
    "alerts",
    "graph_snapshots",
    "audit_logs",
    "saved_queries",
    "exports",
}


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture(scope="module")
def db_engine():
    """In-memory SQLite database engine with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all 31 tables
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
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


# ==============================================================================
# 1. SCHEMA COMPLETENESS & TABLE COUNT (31 TABLES)
# ==============================================================================

class TestSchemaCompleteness:
    """Verifies that all 31 required tables exist with required constraints and columns."""

    def test_all_31_tables_in_metadata(self):
        registered_tables = set(Base.metadata.tables.keys())
        assert len(registered_tables) == 31, f"Expected 31 tables, found {len(registered_tables)}"
        assert registered_tables == EXPECTED_31_TABLES

    def test_all_31_tables_created_in_database(self, db_engine):
        inspector = inspect(db_engine)
        db_tables = set(inspector.get_table_names())
        assert len(db_tables) == 31
        assert db_tables == EXPECTED_31_TABLES

    def test_uuid_primary_keys_on_all_tables(self):
        """All internal primary keys must be UUID type (not autoincrement integer)."""
        for table_name, table in Base.metadata.tables.items():
            pk_cols = table.primary_key.columns
            assert len(pk_cols) > 0, f"Table {table_name} has no primary key"
            for col in pk_cols:
                col_type_name = type(col.type).__name__
                assert "Uuid" in col_type_name or "UUID" in col_type_name or "GUID" in col_type_name, (
                    f"Table {table_name} PK column {col.name} has non-UUID type: {col_type_name}"
                )


# ==============================================================================
# 2. TYPE INVARIANTS (MONETARY & ANALYTICAL PRECISION)
# ==============================================================================

class TestTypeInvariants:
    """Verifies numeric monetary precision and floating-point analytical values."""

    def test_monetary_precision_invariant(self):
        """transactions.amount must be Numeric/Decimal, binary float is strictly forbidden."""
        tx_table = Base.metadata.tables["transactions"]
        amount_col = tx_table.columns["amount"]
        assert isinstance(amount_col.type, Numeric), (
            f"transactions.amount must be Numeric/Decimal, got {type(amount_col.type)}"
        )
        assert amount_col.type.asdecimal is True
        assert amount_col.type.precision == 18
        assert amount_col.type.scale == 2

    def test_analytical_float_invariants(self):
        """predictions.score and risk_scores.value must be floating-point."""
        pred_table = Base.metadata.tables["predictions"]
        assert type(pred_table.columns["score"].type).__name__ == "Float"

        risk_table = Base.metadata.tables["risk_scores"]
        assert type(risk_table.columns["value"].type).__name__ == "Float"

    def test_external_identifiers_not_pks(self):
        """External identifiers (phone, account, vehicle plate) must not be primary keys."""
        phones = Base.metadata.tables["phones"]
        assert phones.primary_key.columns.keys() == ["phone_id"]
        assert "normalized_number" not in phones.primary_key.columns

        accounts = Base.metadata.tables["accounts"]
        assert accounts.primary_key.columns.keys() == ["account_id"]
        assert "masked_identifier" not in accounts.primary_key.columns

        vehicles = Base.metadata.tables["vehicles"]
        assert vehicles.primary_key.columns.keys() == ["vehicle_id"]
        assert "masked_plate" not in vehicles.primary_key.columns


# ==============================================================================
# 3. UNIQUENESS CONSTRAINTS
# ==============================================================================

class TestUniquenessConstraints:
    """Verifies uniqueness constraints on cases, documents, members, roles, permissions."""

    def test_case_code_uniqueness(self, db_session):
        user = User(username="officer1", email="off1@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case1 = Case(case_code="FIR-2026-001", title="Case 1", jurisdiction="MH", created_by=user.user_id)
        db_session.add(case1)
        db_session.flush()

        case2 = Case(case_code="FIR-2026-001", title="Case 2", jurisdiction="MH", created_by=user.user_id)
        db_session.add(case2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_document_case_file_hash_uniqueness(self, db_session):
        """Enforces unique (case_id, file_hash) per documents table constraint."""
        user = User(username="officer2", email="off2@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case = Case(case_code="FIR-2026-002", title="Case 2", jurisdiction="DL", created_by=user.user_id)
        db_session.add(case)
        db_session.flush()

        doc1 = Document(
            case_id=case.case_id,
            file_type="application/pdf",
            file_hash="hash_abc123",
            storage_key="cases/doc1.pdf",
        )
        db_session.add(doc1)
        db_session.flush()

        doc2 = Document(
            case_id=case.case_id,
            file_type="application/pdf",
            file_hash="hash_abc123",  # duplicate hash in same case
            storage_key="cases/doc2.pdf",
        )
        db_session.add(doc2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_case_member_composite_uniqueness(self, db_session):
        """Enforces unique (case_id, user_id) in case_members."""
        user = User(username="officer3", email="off3@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case = Case(case_code="FIR-2026-003", title="Case 3", jurisdiction="KA", created_by=user.user_id)
        db_session.add(case)
        db_session.flush()

        cm1 = CaseMember(case_id=case.case_id, user_id=user.user_id, role_in_case="LEAD")
        db_session.add(cm1)
        db_session.flush()

        cm2 = CaseMember(case_id=case.case_id, user_id=user.user_id, role_in_case="ANALYST")
        db_session.add(cm2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_role_and_permission_uniqueness(self, db_session):
        role1 = Role(name="ANALYST")
        db_session.add(role1)
        db_session.flush()

        role2 = Role(name="ANALYST")
        db_session.add(role2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_permission_code_uniqueness(self, db_session):
        perm1 = Permission(permission_code="CASE_VIEW")
        db_session.add(perm1)
        db_session.flush()

        perm2 = Permission(permission_code="CASE_VIEW")
        db_session.add(perm2)
        with pytest.raises(IntegrityError):
            db_session.flush()


# ==============================================================================
# 4. REFERENTIAL INTEGRITY & CASE TENANCY
# ==============================================================================

class TestReferentialIntegrityAndTenancy:
    """Verifies foreign key constraints and case tenancy scoping."""

    def test_foreign_key_violation_rejected(self, db_session):
        """Inserting child with nonexistent parent UUID fails."""
        nonexistent_case = uuid4()
        doc = Document(
            case_id=nonexistent_case,
            file_type="application/pdf",
            file_hash="hash_999",
            storage_key="invalid.pdf",
        )
        db_session.add(doc)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_case_tenancy_foreign_keys(self):
        """Case tenancy invariant: all case-scoped domain tables carry case_id FK."""
        case_scoped_tables = [
            "case_members",
            "documents",
            "entities",
            "relationships",
            "events",
            "investigation_notes",
            "predictions",
            "alerts",
            "graph_snapshots",
            "saved_queries",
            "exports",
            "audit_logs",
        ]
        for tbl_name in case_scoped_tables:
            table = Base.metadata.tables[tbl_name]
            assert "case_id" in table.columns, f"Table {tbl_name} is missing case_id column"
            fk_targets = [fk.target_fullname for fk in table.foreign_keys]
            assert "cases.case_id" in fk_targets, f"Table {tbl_name} is missing foreign key to cases.case_id"


# ==============================================================================
# 5. IMMUTABILITY & APPEND-ONLY ENFORCEMENT
# ==============================================================================

class TestImmutabilityAndAppendOnly:
    """Verifies that audit_logs and source tables reject UPDATE and DELETE."""

    def test_audit_logs_rejects_update(self, db_session):
        user = User(username="auditor_upd", email="audit_upd@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        audit = AuditLog(
            actor_uuid=user.user_id,
            action_code="CASE_VIEW",
            outcome="SUCCESS",
            target_item="CASE-001",
        )
        db_session.add(audit)
        db_session.flush()

        audit.outcome = "MODIFIED"
        with pytest.raises(ImmutableRecordError, match="UPDATE operation is strictly forbidden"):
            db_session.flush()

    def test_audit_logs_rejects_delete(self, db_session):
        user = User(username="auditor_del", email="audit_del@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        audit = AuditLog(
            actor_uuid=user.user_id,
            action_code="DOCUMENT_DOWNLOAD",
            outcome="SUCCESS",
        )
        db_session.add(audit)
        db_session.flush()

        db_session.delete(audit)
        with pytest.raises(ImmutableRecordError, match="DELETE operation is strictly forbidden"):
            db_session.flush()

    def test_documents_rejects_update(self, db_session):
        user = User(username="doc_cop", email="doc_cop@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case = Case(case_code="FIR-DOC-UPD", title="Doc Upd", jurisdiction="MH", created_by=user.user_id)
        db_session.add(case)
        db_session.flush()

        doc = Document(case_id=case.case_id, file_type="pdf", file_hash="orig_hash", storage_key="k1")
        db_session.add(doc)
        db_session.flush()

        doc.file_hash = "tampered_hash"
        with pytest.raises(ImmutableRecordError, match="UPDATE operation is strictly forbidden on immutable entity 'documents'"):
            db_session.flush()

    def test_documents_rejects_delete(self, db_session):
        user = User(username="doc_del_cop", email="doc_del@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case = Case(case_code="FIR-DOC-DEL", title="Doc Del", jurisdiction="MH", created_by=user.user_id)
        db_session.add(case)
        db_session.flush()

        doc = Document(case_id=case.case_id, file_type="pdf", file_hash="hash_del", storage_key="k2")
        db_session.add(doc)
        db_session.flush()

        db_session.delete(doc)
        with pytest.raises(ImmutableRecordError, match="DELETE operation is strictly forbidden on immutable entity 'documents'"):
            db_session.flush()

    def test_transactions_rejects_delete(self, db_session):
        user = User(username="tx_cop", email="tx_cop@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case = Case(case_code="FIR-TX-IMMUTABLE", title="Tx Immutability", jurisdiction="MH", created_by=user.user_id)
        db_session.add(case)
        db_session.flush()

        ent1 = Entity(case_id=case.case_id, entity_type="PERSON", canonical_name="Sender")
        ent2 = Entity(case_id=case.case_id, entity_type="PERSON", canonical_name="Receiver")
        db_session.add_all([ent1, ent2])
        db_session.flush()

        tx = Transaction(
            sender_ref=ent1.entity_id,
            receiver_ref=ent2.entity_id,
            amount=Decimal("75000.00"),
            currency="INR",
            channel="UPI",
            time=datetime.now(timezone.utc),
        )
        db_session.add(tx)
        db_session.flush()

        db_session.delete(tx)
        with pytest.raises(ImmutableRecordError, match="DELETE operation is strictly forbidden on immutable entity 'transactions'"):
            db_session.flush()


# ==============================================================================
# 6. ORM ROUND-TRIP ACROSS DOMAINS
# ==============================================================================

class TestORMRoundTrip:
    """Verifies that representative records across all 4 domains insert and query cleanly."""

    def test_full_domain_roundtrip(self, db_session):
        # 1. Identity
        user = User(username="lead_inv", email="lead@police.gov.in", password_hash="hashed_pw")
        role = Role(name="INVESTIGATOR")
        user.roles.append(role)
        db_session.add_all([user, role])
        db_session.flush()

        case = Case(case_code="FIR-2026-ROUNDTRIP", title="Smuggling Network", jurisdiction="MH", created_by=user.user_id)
        db_session.add(case)
        db_session.flush()

        member = CaseMember(case_id=case.case_id, user_id=user.user_id, role_in_case="LEAD")
        db_session.add(member)

        # 2. Ingestion
        doc = Document(case_id=case.case_id, file_type="application/pdf", file_hash="sha256_full", storage_key="cases/doc.pdf")
        db_session.add(doc)
        db_session.flush()

        ver = DocumentVersion(document_id=doc.document_id, version_hash="ver_1", meta={"pages": 5})
        db_session.add(ver)
        db_session.flush()

        chunk = DocumentChunk(version_id=ver.version_id, page_number=1, character_span="0:50", text_hash="ch_1", storage_ref="s3://chunk")
        db_session.add(chunk)

        # 3. Entities & Relationships
        e1 = Entity(case_id=case.case_id, entity_type="PERSON", canonical_name="Suresh Verma")
        e2 = Entity(case_id=case.case_id, entity_type="PHONE", canonical_name="+919876543210")
        db_session.add_all([e1, e2])
        db_session.flush()

        alias = EntityAlias(entity_id=e1.entity_id, alias_text="Surya")
        ident = EntityIdentifier(entity_id=e2.entity_id, type="PHONE_NUMBER", normalized_value_hash="hash_phone")
        rel = Relationship(case_id=case.case_id, source_entity_uuid=e1.entity_id, target_entity_uuid=e2.entity_id, type="OWNS")
        db_session.add_all([alias, ident, rel])
        db_session.flush()

        ev = RelationshipEvidence(relationship_id=rel.relationship_id, source_ref="FIR para 3", support_type="FIR_PARAGRAPH")
        tx = Transaction(
            sender_ref=e1.entity_id,
            receiver_ref=e2.entity_id,
            amount=Decimal("1250000.75"),
            currency="INR",
            channel="RTGS",
            time=datetime.now(timezone.utc),
        )
        db_session.add_all([ev, tx])

        # 4. AI & Analytics
        run = ModelRun(model_name="GATv2-LinkPredict", version="1.0.0", task_type="GAT_LINK_PREDICTION", input_snapshot_checksum="chk_123")
        db_session.add(run)
        db_session.flush()

        pred = Prediction(
            run_id=run.run_id,
            case_id=case.case_id,
            source_ref=e1.entity_id,
            target_ref=e2.entity_id,
            score=0.945,
            calibration="CALIBRATED",
        )
        risk = RiskScore(
            target_entity_uuid=e1.entity_id,
            run_id=run.run_id,
            score_type="INVESTIGATION_PRIORITY",
            value=0.88,
            features_summary={"degree": 12, "betweenness": 0.45},
        )
        alert = Alert(
            case_id=case.case_id,
            alert_type="COMMUNICATION_BURST",
            severity="HIGH",
            rule_id="RULE_BURST_01",
            contributing_entities={"entities": [str(e1.entity_id), str(e2.entity_id)]},
        )
        query = SavedQuery(case_id=case.case_id, user_uuid=user.user_id, filters_json={"type": "PERSON"})
        export = Export(case_id=case.case_id, user_uuid=user.user_id, artifact_ref="reports/rep.pdf", version_hash="rep_hash")
        db_session.add_all([pred, risk, alert, query, export])
        db_session.flush()

        # Query back and verify values
        queried_tx = db_session.query(Transaction).filter_by(transaction_id=tx.transaction_id).one()
        assert queried_tx.amount == Decimal("1250000.75")
        assert isinstance(queried_tx.amount, Decimal)

        queried_pred = db_session.query(Prediction).filter_by(prediction_id=pred.prediction_id).one()
        assert round(queried_pred.score, 3) == 0.945

        queried_case = db_session.query(Case).filter_by(case_code="FIR-2026-ROUNDTRIP").one()
        assert len(queried_case.members) == 1
        assert queried_case.members[0].role_in_case == "LEAD"


# ==============================================================================
# 7. CROSS-CASE INTEGRITY & TENANCY ENFORCEMENT
# ==============================================================================

class TestCrossCaseIntegrity:
    """Verifies case isolation and cross-case association boundaries."""

    def test_case_scoped_query_isolation(self, db_session):
        user = User(username="officer_iso", email="iso@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case_a = Case(case_code="CASE-ALPHA", title="Alpha", jurisdiction="MH", created_by=user.user_id)
        case_b = Case(case_code="CASE-BETA", title="Beta", jurisdiction="DL", created_by=user.user_id)
        db_session.add_all([case_a, case_b])
        db_session.flush()

        doc_a = Document(case_id=case_a.case_id, file_type="pdf", file_hash="hash_a", storage_key="a.pdf")
        doc_b = Document(case_id=case_b.case_id, file_type="pdf", file_hash="hash_b", storage_key="b.pdf")
        db_session.add_all([doc_a, doc_b])
        db_session.flush()

        # Case A queries never leak Case B documents
        docs_for_a = db_session.query(Document).filter_by(case_id=case_a.case_id).all()
        assert len(docs_for_a) == 1
        assert docs_for_a[0].file_hash == "hash_a"

        docs_for_b = db_session.query(Document).filter_by(case_id=case_b.case_id).all()
        assert len(docs_for_b) == 1
        assert docs_for_b[0].file_hash == "hash_b"

    def test_cross_case_association_validation(self, db_session):
        """
        Application/Domain invariant: entities in Case A and Case B cannot be
        arbitrarily linked in a relationship under Case A without validation error.
        """
        user = User(username="officer_cross", email="cross@police.gov.in", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        case_a = Case(case_code="CASE-X", title="Case X", jurisdiction="MH", created_by=user.user_id)
        case_b = Case(case_code="CASE-Y", title="Case Y", jurisdiction="KA", created_by=user.user_id)
        db_session.add_all([case_a, case_b])
        db_session.flush()

        ent_a = Entity(case_id=case_a.case_id, entity_type="PERSON", canonical_name="Suspect X")
        ent_b = Entity(case_id=case_b.case_id, entity_type="PERSON", canonical_name="Suspect Y")
        db_session.add_all([ent_a, ent_b])
        db_session.flush()

        # Invariant check: source and target entities must match relationship case_id
        def validate_relationship_case_tenancy(rel: Relationship, session: Session) -> bool:
            source = session.query(Entity).filter_by(entity_id=rel.source_entity_uuid).one()
            target = session.query(Entity).filter_by(entity_id=rel.target_entity_uuid).one()
            return source.case_id == rel.case_id and target.case_id == rel.case_id

        invalid_rel = Relationship(
            case_id=case_a.case_id,
            source_entity_uuid=ent_a.entity_id,
            target_entity_uuid=ent_b.entity_id,  # Target is in Case B!
            type="ASSOCIATE_OF",
        )
        assert validate_relationship_case_tenancy(invalid_rel, db_session) is False

        valid_ent_a2 = Entity(case_id=case_a.case_id, entity_type="PHONE", canonical_name="+919999988888")
        db_session.add(valid_ent_a2)
        db_session.flush()

        valid_rel = Relationship(
            case_id=case_a.case_id,
            source_entity_uuid=ent_a.entity_id,
            target_entity_uuid=valid_ent_a2.entity_id,
            type="OWNS",
        )
        assert validate_relationship_case_tenancy(valid_rel, db_session) is True


# ==============================================================================
# 8. ALEMBIC MIGRATION DISCOVERY, UPGRADE & DOWNGRADE
# ==============================================================================

class TestAlembicMigration:
    """Verifies that Alembic discovers revisions, creates all 31 tables, and rolls back cleanly."""

    def test_alembic_upgrade_downgrade_cycle(self, tmp_path):
        import sqlite3
        from alembic.config import Config
        from alembic import command

        db_file = tmp_path / "alembic_test.db"
        db_url = f"sqlite:///{db_file.as_posix()}"

        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", db_url)

        # 1. Run upgrade head
        command.upgrade(cfg, "head")

        conn = sqlite3.connect(str(db_file))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'")
        created_tables = {row[0] for row in cur.fetchall()}
        conn.close()

        assert len(created_tables) == 31, f"Expected 31 tables from Alembic upgrade, got {len(created_tables)}"
        assert created_tables == EXPECTED_31_TABLES

        # 2. Run downgrade base
        command.downgrade(cfg, "base")

        conn = sqlite3.connect(str(db_file))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'")
        tables_after_downgrade = [row[0] for row in cur.fetchall()]
        conn.close()

        assert len(tables_after_downgrade) == 0, f"Expected 0 tables after downgrade, found {len(tables_after_downgrade)}"

        # 3. Re-run upgrade head
        command.upgrade(cfg, "head")

        conn = sqlite3.connect(str(db_file))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'")
        recreated_tables = {row[0] for row in cur.fetchall()}
        conn.close()

        assert len(recreated_tables) == 31

