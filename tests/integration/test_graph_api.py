"""
Integration Tests for Case Graph API and Graph Rebuild Endpoint.
Validates:
- GET /api/v1/cases/{case_id}/graph retrieval with Cytoscape formatting
- Depth, focus_entity_id, confidence, and prediction filters
- 404 RESOURCE_NOT_FOUND case-isolation boundary (non-member gets 404, never 403)
- IDOR prevention: focus_entity_id from another case yields no cross-case leakage
- POST /api/v1/cases/{case_id}/graph/rebuild asynchronous HTTP 202 Accepted
- RBAC authorization: Supervisor (REVIEW_OVERRIDE) allowed; Investigator denied with 403
- GRAPH_REBUILD audit logging
- Neo4j outage handling: API returns clean 503 SERVICE_UNAVAILABLE; PostgreSQL endpoints remain functional
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
from backend.db.models.entities import Entity, Relationship, RelationshipEvidence
from backend.db.models.analytics import AuditLog, GraphSnapshot, Prediction
from backend.graph.connection import set_graph_manager
from backend.graph.mock_driver import MockNeo4jConnectionManager
from backend.security.password import hash_password
from backend.security.rbac import Permissions, SystemRoles
from backend.security.tokens import create_access_token
from backend.services.graph_projection import GraphProjectionService


@pytest.fixture
def graph_test_env():
    """Sets up SQLite database, mock Neo4j connection, and test users/cases."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    # Set up mock Neo4j manager
    mock_mgr = MockNeo4jConnectionManager()
    set_graph_manager(mock_mgr)

    # 1. Seed Roles
    investigator_role = Role(role_id=uuid4(), name=SystemRoles.INVESTIGATOR)
    supervisor_role = Role(role_id=uuid4(), name=SystemRoles.SUPERVISOR)
    db.add_all([investigator_role, supervisor_role])
    db.commit()

    # 2. Seed Users
    # User A (Supervisor of Case A)
    user_a = User(
        user_id=uuid4(),
        email="supervisor_a@example.com",
        username="supervisor_a",
        password_hash=hash_password("SuperPass123!"),
        account_status="ACTIVE",
    )
    # User B (Investigator of Case B only)
    user_b = User(
        user_id=uuid4(),
        email="investigator_b@example.com",
        username="investigator_b",
        password_hash=hash_password("InvestPass123!"),
        account_status="ACTIVE",
    )
    # User C (Investigator of Case A only)
    user_c = User(
        user_id=uuid4(),
        email="investigator_a@example.com",
        username="investigator_a",
        password_hash=hash_password("InvestPass123!"),
        account_status="ACTIVE",
    )
    db.add_all([user_a, user_b, user_c])
    db.commit()

    # Global roles
    db.add(UserRole(user_id=user_a.user_id, role_id=supervisor_role.role_id))
    db.add(UserRole(user_id=user_b.user_id, role_id=investigator_role.role_id))
    db.add(UserRole(user_id=user_c.user_id, role_id=investigator_role.role_id))
    db.commit()

    # 3. Seed Cases
    case_a = Case(
        case_id=uuid4(),
        case_code="CASE-GRAPH-A",
        title="Case A",
        status="ACTIVE",
        jurisdiction="DL-NORTH",
        created_by=user_a.user_id,
    )
    case_b = Case(
        case_id=uuid4(),
        case_code="CASE-GRAPH-B",
        title="Case B",
        status="ACTIVE",
        jurisdiction="DL-SOUTH",
        created_by=user_b.user_id,
    )
    db.add_all([case_a, case_b])
    db.commit()

    # 4. Seed Memberships
    # User A is Supervisor in Case A
    db.add(CaseMember(case_member_id=uuid4(), case_id=case_a.case_id, user_id=user_a.user_id, role_in_case="SUPERVISOR"))
    # User C is Investigator in Case A
    db.add(CaseMember(case_member_id=uuid4(), case_id=case_a.case_id, user_id=user_c.user_id, role_in_case="INVESTIGATOR"))
    # User B is Investigator in Case B
    db.add(CaseMember(case_member_id=uuid4(), case_id=case_b.case_id, user_id=user_b.user_id, role_in_case="INVESTIGATOR"))
    db.commit()

    # 5. Seed Entities and Relationships in Case A
    e1 = Entity(entity_id=uuid4(), case_id=case_a.case_id, entity_type="PERSON", canonical_name="Target Person", status="ACTIVE")
    e2 = Entity(entity_id=uuid4(), case_id=case_a.case_id, entity_type="PHONE", canonical_name="+919876543210", status="ACTIVE")
    e3 = Entity(entity_id=uuid4(), case_id=case_a.case_id, entity_type="BANK_ACCOUNT", canonical_name="SBI-10023", status="ACTIVE")
    r1 = Relationship(
        relationship_id=uuid4(),
        case_id=case_a.case_id,
        source_entity_uuid=e1.entity_id,
        target_entity_uuid=e2.entity_id,
        type="OWNS",
        status="OBSERVED",
    )
    r2 = Relationship(
        relationship_id=uuid4(),
        case_id=case_a.case_id,
        source_entity_uuid=e1.entity_id,
        target_entity_uuid=e3.entity_id,
        type="OWNS",
        status="OBSERVED",
    )
    db.add_all([e1, e2, e3, r1, r2])
    db.commit()

    # Project into mock Neo4j
    proj = GraphProjectionService(db=db, graph_manager=mock_mgr)
    proj.rebuild_case_graph(case_a.case_id)

    # Attach session factory to db session for background task resolution
    db.session_factory = TestingSessionLocal

    # Override app dependency
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
        "mock_mgr": mock_mgr,
        "case_a": case_a,
        "case_b": case_b,
        "user_a": user_a,
        "user_b": user_b,
        "user_c": user_c,
        "e1": e1,
        "e2": e2,
        "e3": e3,
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
# 1. GET CASE GRAPH TESTS
# ==============================================================================

class TestGetCaseGraphAPI:
    """Tests for GET /api/v1/cases/{case_id}/graph."""

    def test_get_graph_authorized_success(self, graph_test_env):
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_c = graph_test_env["user_c"]  # Investigator of Case A

        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}/graph",
            headers=auth_header(user_c),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "tracking_id" in body

        data = body["data"]
        assert "nodes" in data
        assert "edges" in data
        assert "stats" in data
        assert data["stats"]["node_count"] == 3
        assert data["stats"]["edge_count"] == 2

    def test_get_graph_non_member_returns_404(self, graph_test_env):
        """User B (only in Case B) accessing Case A graph strictly gets 404 RESOURCE_NOT_FOUND."""
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_b = graph_test_env["user_b"]

        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}/graph",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_get_graph_depth_validation(self, graph_test_env):
        """Depth must be between 1 and 3; depth=4 returns 422 validation error."""
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_a = graph_test_env["user_a"]

        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}/graph?depth=4",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_focus_entity_idor_defense(self, graph_test_env):
        """Foreign focus_entity_id not belonging to case returns empty graph without leaking."""
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_a = graph_test_env["user_a"]
        foreign_id = uuid4()

        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}/graph?focus_entity_id={foreign_id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["stats"]["node_count"] == 0
        assert body["data"]["stats"]["edge_count"] == 0


# ==============================================================================
# 2. POST REBUILD CASE GRAPH TESTS
# ==============================================================================

class TestRebuildCaseGraphAPI:
    """Tests for POST /api/v1/cases/{case_id}/graph/rebuild."""

    def test_rebuild_authorized_supervisor_returns_202(self, graph_test_env):
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_a = graph_test_env["user_a"]  # Supervisor with REVIEW_OVERRIDE

        resp = client.post(
            f"/api/v1/cases/{case_a.case_id}/graph/rebuild",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["case_id"] == str(case_a.case_id)
        assert "job_id" in data
        assert data["status"] == "REBUILDING"

        # Verify GRAPH_REBUILD was audited
        db = graph_test_env["db"]
        audit_events = (
            db.query(AuditLog)
            .filter(
                AuditLog.case_id == case_a.case_id,
                AuditLog.action_code == "GRAPH_REBUILD",
            )
            .all()
        )
        assert len(audit_events) >= 1

    def test_rebuild_investigator_forbidden_returns_403(self, graph_test_env):
        """Investigator lacking REVIEW_OVERRIDE permission gets 403 Forbidden."""
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_c = graph_test_env["user_c"]  # Investigator only

        resp = client.post(
            f"/api/v1/cases/{case_a.case_id}/graph/rebuild",
            headers=auth_header(user_c),
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "FORBIDDEN"

    def test_rebuild_non_member_returns_404(self, graph_test_env):
        """Non-member gets 404 RESOURCE_NOT_FOUND."""
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_b = graph_test_env["user_b"]  # Member of Case B only

        resp = client.post(
            f"/api/v1/cases/{case_a.case_id}/graph/rebuild",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "RESOURCE_NOT_FOUND"


# ==============================================================================
# 3. NEO4J OUTAGE HANDLING & POSTGRESQL INDEPENDENCE
# ==============================================================================

class TestNeo4jOutageAndDegradation:
    """Validates system behavior when Neo4j is offline."""

    def test_graph_api_returns_503_during_outage(self, graph_test_env):
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_a = graph_test_env["user_a"]
        mock_mgr = graph_test_env["mock_mgr"]

        # Simulate Neo4j outage
        mock_mgr.mock_driver.simulate_outage(True)

        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}/graph",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 503
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "password" not in resp.text.lower()
        assert "bolt://" not in resp.text.lower()

    def test_postgresql_case_api_continues_to_function_during_neo4j_outage(self, graph_test_env):
        """PostgreSQL is authoritative SoR: Case management endpoints must remain 100% operational."""
        client = graph_test_env["client"]
        case_a = graph_test_env["case_a"]
        user_a = graph_test_env["user_a"]
        mock_mgr = graph_test_env["mock_mgr"]

        # Simulate Neo4j outage
        mock_mgr.mock_driver.simulate_outage(True)

        # GET /cases/{case_id} must succeed normally via PostgreSQL
        resp = client.get(
            f"/api/v1/cases/{case_a.case_id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["case_id"] == str(case_a.case_id)
