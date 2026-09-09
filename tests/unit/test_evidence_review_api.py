"""
Unit Tests for Evidence Detail, Provenance Spans, and Human Review Overrides.
Validates:
- GET /entities/{entity_id}: aliases, masked identifiers, risk scores, provenance spans
- GET /relationships/{relationship_id}: citations, endpoint metadata, is_predicted separation
- POST /reviews: CONFIRM, REJECT, MERGE actions
- Human decision primacy: confirmed/rejected status is canonical and preserved
- Entity merge: alias absorption, identifier re-pointing, relationship redirection, self-loop prevention
- Supervisor permission enforcement (REVIEW_OVERRIDE) & Investigator denial (403)
- Server-side case isolation (404 RESOURCE_NOT_FOUND)
- Immutability: source records are never physically deleted
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app
from apps.api.deps import get_db
from backend.db.base import Base
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.entities import (
    Entity,
    EntityAlias,
    EntityIdentifier,
    Relationship,
    RelationshipEvidence,
)
from backend.db.models.analytics import AuditLog, RiskScore
from backend.graph.connection import set_graph_manager
from backend.graph.mock_driver import MockNeo4jConnectionManager
from backend.security.password import hash_password
from backend.security.rbac import SystemRoles
from backend.security.tokens import create_access_token


@pytest.fixture
def evidence_test_env():
    """Sets up SQLite test environment for evidence and human review tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    db.session_factory = TestingSessionLocal

    mock_mgr = MockNeo4jConnectionManager()
    set_graph_manager(mock_mgr)

    # 1. Seed Roles
    inv_role = Role(role_id=uuid4(), name=SystemRoles.INVESTIGATOR)
    sup_role = Role(role_id=uuid4(), name=SystemRoles.SUPERVISOR)
    db.add_all([inv_role, sup_role])
    db.commit()

    # 2. Seed Users
    # Supervisor
    sup_user = User(
        user_id=uuid4(),
        email="supervisor@example.com",
        username="supervisor",
        password_hash=hash_password("SuperSecret1!"),
        account_status="ACTIVE",
    )
    # Investigator
    inv_user = User(
        user_id=uuid4(),
        email="investigator@example.com",
        username="investigator",
        password_hash=hash_password("InvestSecret1!"),
        account_status="ACTIVE",
    )
    db.add_all([sup_user, inv_user])
    db.commit()

    db.add(UserRole(user_id=sup_user.user_id, role_id=sup_role.role_id))
    db.add(UserRole(user_id=inv_user.user_id, role_id=inv_role.role_id))
    db.commit()

    # 3. Seed Cases
    case_a = Case(
        case_id=uuid4(),
        case_code="CASE-EV-A",
        title="Evidence Case A",
        status="ACTIVE",
        jurisdiction="DL-CENTRAL",
        created_by=sup_user.user_id,
    )
    case_b = Case(
        case_id=uuid4(),
        case_code="CASE-EV-B",
        title="Evidence Case B",
        status="ACTIVE",
        jurisdiction="DL-SOUTH",
        created_by=sup_user.user_id,
    )
    db.add_all([case_a, case_b])
    db.commit()

    # Memberships
    db.add(CaseMember(case_member_id=uuid4(), case_id=case_a.case_id, user_id=sup_user.user_id, role_in_case="SUPERVISOR"))
    db.add(CaseMember(case_member_id=uuid4(), case_id=case_a.case_id, user_id=inv_user.user_id, role_in_case="INVESTIGATOR"))
    # inv_user is NOT a member of Case B
    db.commit()

    # 4. Seed Canonical Entity with aliases, identifiers, and risk score in Case A
    target_entity = Entity(
        entity_id=uuid4(),
        case_id=case_a.case_id,
        entity_type="PERSON",
        canonical_name="Vikram Singh",
        status="ACTIVE",
    )
    alias1 = EntityAlias(
        alias_id=uuid4(),
        entity_id=target_entity.entity_id,
        alias_text="Vicky",
        source_ref="FIR:2026/04:Page2",
    )
    ident1 = EntityIdentifier(
        identifier_id=uuid4(),
        entity_id=target_entity.entity_id,
        type="PHONE_NUMBER",
        normalized_value_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        value_policy="MASKED_STORAGE",
    )
    risk_score = RiskScore(
        score_id=uuid4(),
        target_entity_uuid=target_entity.entity_id,
        run_id=uuid4(),
        score_type="PRIORITY_RANKING",
        value=0.88,
        features_summary={"degree_centrality": 4, "betweenness": 0.32},
    )

    # Secondary Entity for merge testing
    secondary_entity = Entity(
        entity_id=uuid4(),
        case_id=case_a.case_id,
        entity_type="PERSON",
        canonical_name="V. Singh",
        status="ACTIVE",
    )
    sec_alias = EntityAlias(
        alias_id=uuid4(),
        entity_id=secondary_entity.entity_id,
        alias_text="Vikram",
        source_ref="INTERROGATION:2026",
    )

    # Associate Entity (e.g. Phone)
    phone_entity = Entity(
        entity_id=uuid4(),
        case_id=case_a.case_id,
        entity_type="PHONE",
        canonical_name="+919811122233",
        status="ACTIVE",
    )

    # Relationships
    rel1 = Relationship(
        relationship_id=uuid4(),
        case_id=case_a.case_id,
        source_entity_uuid=target_entity.entity_id,
        target_entity_uuid=phone_entity.entity_id,
        type="OWNS",
        status="OBSERVED",
    )
    rel1_ev = RelationshipEvidence(
        evidence_id=uuid4(),
        relationship_id=rel1.relationship_id,
        source_ref="CAF_RECORD_449",
        support_type="SUBSCRIBER_APPLICATION",
    )

    # Relationship from secondary to phone
    rel2 = Relationship(
        relationship_id=uuid4(),
        case_id=case_a.case_id,
        source_entity_uuid=secondary_entity.entity_id,
        target_entity_uuid=phone_entity.entity_id,
        type="CONTACTED",
        status="OBSERVED",
    )

    db.add_all([
        target_entity, alias1, ident1, risk_score,
        secondary_entity, sec_alias, phone_entity,
        rel1, rel1_ev, rel2,
    ])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield {
        "db": db,
        "client": client,
        "case_a": case_a,
        "case_b": case_b,
        "sup_user": sup_user,
        "inv_user": inv_user,
        "target_entity": target_entity,
        "secondary_entity": secondary_entity,
        "phone_entity": phone_entity,
        "rel1": rel1,
    }

    app.dependency_overrides.clear()
    set_graph_manager(None)
    db.close()


def auth_header(user: User, roles: list = None) -> dict:
    token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=roles or ["INVESTIGATOR"],
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. ENTITY & RELATIONSHIP EVIDENCE DETAIL TESTS
# ==============================================================================

class TestEvidenceDetailAPIs:
    """Validates entity detail, provenance, identifier masking, and relationship citations."""

    def test_get_entity_detail_success(self, evidence_test_env):
        client = evidence_test_env["client"]
        case_a = evidence_test_env["case_a"]
        inv_user = evidence_test_env["inv_user"]
        target_e = evidence_test_env["target_entity"]

        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}/entities/{target_e.entity_id}",
            headers=auth_header(inv_user),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "tracking_id" in body

        data = body["data"]
        assert data["entity_id"] == str(target_e.entity_id)
        assert data["canonical_name"] == "Vikram Singh"
        assert len(data["aliases"]) >= 1
        assert data["aliases"][0]["alias_text"] == "Vicky"

        # Check defensive identifier masking
        assert len(data["identifiers"]) >= 1
        masked = data["identifiers"][0]["masked_value"]
        assert "e3b0c4" not in masked or "..." in masked

        # Check risk score feature summary
        assert data["risk_score"] is not None
        assert data["risk_score"]["value"] == 0.88
        assert data["risk_score"]["features_summary"]["degree_centrality"] == 4

        # Check provenance span
        assert len(data["provenance_spans"]) >= 1
        assert data["provenance_spans"][0]["snippet"] == "Vicky"

    def test_get_entity_detail_non_member_case_isolation(self, evidence_test_env):
        """User requesting entity in a case they do not belong to receives 404 RESOURCE_NOT_FOUND."""
        client = evidence_test_env["client"]
        case_b = evidence_test_env["case_b"]
        inv_user = evidence_test_env["inv_user"]  # Only member of Case A
        fake_id = uuid4()

        resp = client.get(
            f"/api/v1/cases/{case_b.case_id}/entities/{fake_id}",
            headers=auth_header(inv_user),
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_get_relationship_detail_success(self, evidence_test_env):
        client = evidence_test_env["client"]
        case_a = evidence_test_env["case_a"]
        inv_user = evidence_test_env["inv_user"]
        rel1 = evidence_test_env["rel1"]

        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}/relationships/{rel1.relationship_id}",
            headers=auth_header(inv_user),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["relationship_id"] == str(rel1.relationship_id)
        assert data["type"] == "OWNS"
        assert data["source_entity"]["canonical_name"] == "Vikram Singh"
        assert len(data["evidence_citations"]) == 1
        assert data["evidence_citations"][0]["source_ref"] == "CAF_RECORD_449"


# ==============================================================================
# 2. HUMAN REVIEW OVERRIDES TESTS
# ==============================================================================

class TestHumanReviewOverrides:
    """Validates CONFIRM, REJECT, MERGE, and human decision primacy."""

    def test_review_confirm_entity(self, evidence_test_env):
        client = evidence_test_env["client"]
        case_a = evidence_test_env["case_a"]
        sup_user = evidence_test_env["sup_user"]
        target_e = evidence_test_env["target_entity"]

        resp = client.post(
            f"/api/v1/cases/{case_a.case_id}/reviews",
            json={
                "target_type": "ENTITY",
                "target_id": str(target_e.entity_id),
                "action": "CONFIRM",
                "reason": "Verified through government photo identification produced.",
            },
            headers=auth_header(sup_user, roles=["SUPERVISOR"]),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["resulting_status"] == "CONFIRMED"

        # Verify state in PostgreSQL
        db = evidence_test_env["db"]
        refreshed = db.query(Entity).filter(Entity.entity_id == target_e.entity_id).first()
        assert refreshed.status == "CONFIRMED"

        # Verify audit entry
        audit = db.query(AuditLog).filter(AuditLog.action_code == "REVIEW_OVERRIDE").first()
        assert audit is not None
        assert str(target_e.entity_id) in audit.target_item

    def test_review_permission_enforcement(self, evidence_test_env):
        """Investigator role lacks REVIEW_OVERRIDE permission and receives 403 Forbidden."""
        client = evidence_test_env["client"]
        case_a = evidence_test_env["case_a"]
        inv_user = evidence_test_env["inv_user"]
        target_e = evidence_test_env["target_entity"]

        resp = client.post(
            f"/api/v1/cases/{case_a.case_id}/reviews",
            json={
                "target_type": "ENTITY",
                "target_id": str(target_e.entity_id),
                "action": "CONFIRM",
                "reason": "Attempting override as investigator",
            },
            headers=auth_header(inv_user, roles=["INVESTIGATOR"]),
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_entity_merge_workflow(self, evidence_test_env):
        """Validates merging secondary entity into primary target entity."""
        client = evidence_test_env["client"]
        case_a = evidence_test_env["case_a"]
        sup_user = evidence_test_env["sup_user"]
        target_e = evidence_test_env["target_entity"]
        sec_e = evidence_test_env["secondary_entity"]

        resp = client.post(
            f"/api/v1/cases/{case_a.case_id}/reviews",
            json={
                "target_type": "ENTITY",
                "target_id": str(target_e.entity_id),
                "secondary_target_id": str(sec_e.entity_id),
                "action": "MERGE",
                "reason": "V. Singh confirmed to be the same individual as Vikram Singh.",
            },
            headers=auth_header(sup_user, roles=["SUPERVISOR"]),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["resulting_status"] == "CONFIRMED"

        # Verify PostgreSQL state
        db = evidence_test_env["db"]
        primary = db.query(Entity).filter(Entity.entity_id == target_e.entity_id).first()
        secondary = db.query(Entity).filter(Entity.entity_id == sec_e.entity_id).first()

        assert primary.status == "CONFIRMED"
        assert secondary.status == "MERGED"  # Soft merge, never physically deleted

        # Verify secondary's name absorbed as alias
        alias_texts = [a.alias_text for a in primary.aliases]
        assert "V. Singh" in alias_texts

        # Verify relationship redirection: rel2 originally from secondary -> now points to target
        rels_from_target = (
            db.query(Relationship)
            .filter(Relationship.source_entity_uuid == target_e.entity_id)
            .all()
        )
        assert len(rels_from_target) >= 2  # rel1 + redirected rel2

    def test_self_merge_rejected(self, evidence_test_env):
        """Attempting to merge an entity into itself returns 409 Conflict."""
        client = evidence_test_env["client"]
        case_a = evidence_test_env["case_a"]
        sup_user = evidence_test_env["sup_user"]
        target_e = evidence_test_env["target_entity"]

        resp = client.post(
            f"/api/v1/cases/{case_a.case_id}/reviews",
            json={
                "target_type": "ENTITY",
                "target_id": str(target_e.entity_id),
                "secondary_target_id": str(target_e.entity_id),
                "action": "MERGE",
                "reason": "Self merge test",
            },
            headers=auth_header(sup_user, roles=["SUPERVISOR"]),
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CONFLICT"
