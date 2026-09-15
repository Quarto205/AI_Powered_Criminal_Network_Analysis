"""
Integration Test Suite for Multi-Tenant Case Management.
Tests:
- POST /api/v1/cases (Creation, auto-membership as SUPERVISOR, duplicate code 409, audit CASE_CREATE)
- GET /api/v1/cases (Tenant boundary listing, status filtering, pagination)
- GET /api/v1/cases/{case_id} (Metadata, document_count, entity_count, non-member 404)
- PATCH /api/v1/cases/{case_id} (Partial update, status validation, audit CASE_UPDATE, non-member 404)
- POST /api/v1/cases/{case_id}/members (Member assignment, role validation, audit CASE_MEMBER_ADD)
- GET /api/v1/cases/{case_id}/members (Sanitized member listing, non-member 404)
- Universal response envelope verification across all endpoints
"""

from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app
from backend.config.security import SecuritySettings, set_security_settings
from backend.db.base import Base
from backend.db.models.analytics import AuditLog
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.ingestion import Document
from backend.db.models.entities import Entity
from backend.db.session import get_db, get_engine, get_session_factory
from backend.schemas.envelope import ErrorCodes
from backend.security.password import hash_password
from backend.security.rbac import Permissions, SystemRoles
from backend.security.tokens import create_access_token

# Shared test database engine using StaticPool
case_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
CaseTestingSessionLocal = sessionmaker(bind=case_test_engine)


def override_case_get_db():
    session = CaseTestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module", autouse=True)
def setup_case_test_environment():
    """Sets test configuration and creates database schema."""
    test_settings = SecuritySettings(
        jwt_secret_key="case-mgmt-test-deterministic-jwt-secret-key-32b!",
        jwt_algorithm="HS256",
        jwt_access_token_expire_seconds=28800,
    )
    set_security_settings(test_settings)
    Base.metadata.create_all(case_test_engine)
    app.dependency_overrides[get_db] = override_case_get_db

    # Seed roles in test DB
    session = CaseTestingSessionLocal()
    for role_name in [SystemRoles.INVESTIGATOR, SystemRoles.ANALYST, SystemRoles.SUPERVISOR]:
        existing = session.query(Role).filter_by(name=role_name).first()
        if not existing:
            session.add(Role(role_id=uuid4(), name=role_name))
    session.commit()
    session.close()

    yield

    app.dependency_overrides.clear()
    set_security_settings(None)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = CaseTestingSessionLocal()
    yield session
    session.close()


def create_user_with_token(
    db,
    username: str,
    email: str,
    role_name: str = SystemRoles.INVESTIGATOR,
) -> tuple[User, str]:
    """Helper creating a test user, assigning a role, and returning (User, JWT token)."""
    user = User(
        user_id=uuid4(),
        username=username,
        email=email,
        password_hash=hash_password("CaseTestPass123!"),
        account_status="ACTIVE",
    )
    db.add(user)
    db.commit()

    role = db.query(Role).filter_by(name=role_name).first()
    if role:
        user_role = UserRole(user_id=user.user_id, role_id=role.role_id)
        db.add(user_role)
        db.commit()

    token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=[role_name],
    )
    return user, token


# ==============================================================================
# 1. CASE CREATION TESTS (POST /api/v1/cases)
# ==============================================================================

class TestCaseCreation:

    def test_supervisor_create_case_success(self, client, db):
        supervisor, token = create_user_with_token(
            db, "sup_creator", "sup_creator@sih.gov.in", SystemRoles.SUPERVISOR
        )

        payload = {
            "case_code": "CASE-2026-DEL-001",
            "title": "Operation Red Falcon",
            "description": "Investigation into interstate financial network.",
            "jurisdiction": "Delhi NCR",
        }

        resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["error"] is None
        assert "tracking_id" in data
        assert resp.headers.get("X-Tracking-ID") == data["tracking_id"]

        case_info = data["data"]
        case_id = UUID(case_info["case_id"])
        assert case_info["case_code"] == "CASE-2026-DEL-001"
        assert case_info["title"] == "Operation Red Falcon"
        assert case_info["status"] == "ACTIVE"
        assert case_info["jurisdiction"] == "Delhi NCR"
        assert case_info["created_by"] == str(supervisor.user_id)

        # 1. Verify creator membership auto-assigned with role SUPERVISOR
        member = (
            db.query(CaseMember)
            .filter_by(case_id=case_id, user_id=supervisor.user_id)
            .first()
        )
        assert member is not None
        assert member.role_in_case == "SUPERVISOR"

        # 2. Verify CASE_CREATE audit event written
        audit = (
            db.query(AuditLog)
            .filter_by(actor_uuid=supervisor.user_id, action_code="CASE_CREATE", case_id=case_id)
            .first()
        )
        assert audit is not None
        assert audit.outcome == "SUCCESS"
        assert audit.target_item == "CASE-2026-DEL-001"

    def test_investigator_cannot_create_case(self, client, db):
        # Investigator lacks CASE_CREATE permission
        investigator, token = create_user_with_token(
            db, "inv_nocreate", "inv_nocreate@sih.gov.in", SystemRoles.INVESTIGATOR
        )

        resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "case_code": "CASE-FORBIDDEN-01",
                "title": "Unauthorized Case",
                "jurisdiction": "Mumbai",
            },
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCodes.FORBIDDEN

    def test_duplicate_case_code_returns_409_conflict(self, client, db):
        supervisor, token = create_user_with_token(
            db, "sup_dup", "sup_dup@sih.gov.in", SystemRoles.SUPERVISOR
        )

        payload = {
            "case_code": "CASE-DUP-001",
            "title": "First Case",
            "jurisdiction": "Central",
        }

        # First creation succeeds
        resp1 = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert resp1.status_code == 201

        # Second creation with identical case_code returns 409 Conflict
        resp2 = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert resp2.status_code == 409
        data = resp2.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCodes.CONFLICT
        assert "already exists" in data["error"]["message"].lower()


# ==============================================================================
# 2. AUTHORIZED CASE LISTING TESTS (GET /api/v1/cases)
# ==============================================================================

class TestCaseListing:

    def test_case_list_tenant_isolation(self, client, db):
        sup_a, token_a = create_user_with_token(db, "sup_list_a", "sup_a@sih.gov.in", SystemRoles.SUPERVISOR)
        sup_b, token_b = create_user_with_token(db, "sup_list_b", "sup_b@sih.gov.in", SystemRoles.SUPERVISOR)

        # Sup A creates Case A1 and Case A2
        resp_a1 = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"case_code": "CASE-LIST-A1", "title": "Case A1", "jurisdiction": "Delhi"},
        )
        resp_a2 = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"case_code": "CASE-LIST-A2", "title": "Case A2", "jurisdiction": "Delhi"},
        )
        assert resp_a1.status_code == 201
        assert resp_a2.status_code == 201

        # Sup B creates Case B1
        resp_b1 = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"case_code": "CASE-LIST-B1", "title": "Case B1", "jurisdiction": "Kolkata"},
        )
        assert resp_b1.status_code == 201

        # Sup A lists cases: must see only Case A1 and A2, never Case B1
        list_a = client.get(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert list_a.status_code == 200
        data_a = list_a.json()["data"]
        case_codes_a = [c["case_code"] for c in data_a["cases"]]
        assert "CASE-LIST-A1" in case_codes_a
        assert "CASE-LIST-A2" in case_codes_a
        assert "CASE-LIST-B1" not in case_codes_a

        # Sup B lists cases: must see only Case B1
        list_b = client.get(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert list_b.status_code == 200
        data_b = list_b.json()["data"]
        case_codes_b = [c["case_code"] for c in data_b["cases"]]
        assert "CASE-LIST-B1" in case_codes_b
        assert "CASE-LIST-A1" not in case_codes_b
        assert "CASE-LIST-A2" not in case_codes_b

    def test_case_list_status_filter_and_pagination(self, client, db):
        sup, token = create_user_with_token(db, "sup_paginate", "sup_p@sih.gov.in", SystemRoles.SUPERVISOR)

        # Create two cases
        c1 = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json={"case_code": "CASE-PAG-01", "title": "Pagination 1", "jurisdiction": "North"},
        ).json()["data"]
        c2 = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json={"case_code": "CASE-PAG-02", "title": "Pagination 2", "jurisdiction": "North"},
        ).json()["data"]

        # Close case 2
        client.patch(
            f"/api/v1/cases/{c2['case_id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "CLOSED"},
        )

        # Filter by ACTIVE status
        resp_active = client.get(
            "/api/v1/cases?status=ACTIVE",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_active.status_code == 200
        active_codes = [c["case_code"] for c in resp_active.json()["data"]["cases"]]
        assert "CASE-PAG-01" in active_codes
        assert "CASE-PAG-02" not in active_codes

        # Filter by CLOSED status
        resp_closed = client.get(
            "/api/v1/cases?status=CLOSED",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_closed.status_code == 200
        closed_codes = [c["case_code"] for c in resp_closed.json()["data"]["cases"]]
        assert "CASE-PAG-02" in closed_codes


# ==============================================================================
# 3. CASE DETAILS & AGGREGATE COUNTS (GET /api/v1/cases/{case_id})
# ==============================================================================

class TestCaseDetails:

    def test_get_case_details_with_counts(self, client, db):
        sup, token = create_user_with_token(db, "sup_details", "details@sih.gov.in", SystemRoles.SUPERVISOR)

        # Create case
        c_resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json={"case_code": "CASE-DET-01", "title": "Detailed Case", "jurisdiction": "West"},
        ).json()["data"]
        case_id = UUID(c_resp["case_id"])

        # Add 1 Document and 2 Entities to DB
        doc = Document(
            document_id=uuid4(),
            case_id=case_id,
            file_type="application/pdf",
            file_hash="hash_count_01",
            storage_key="cases/count.pdf",
            status="EXTRACTED",
        )
        e1 = Entity(
            entity_id=uuid4(),
            case_id=case_id,
            entity_type="PERSON",
            canonical_name="Target Person Alpha",
            status="CONFIRMED",
        )
        e2 = Entity(
            entity_id=uuid4(),
            case_id=case_id,
            entity_type="PHONE",
            canonical_name="+919000000001",
            status="CONFIRMED",
        )
        db.add_all([doc, e1, e2])
        db.commit()

        # Retrieve details
        resp = client.get(
            f"/api/v1/cases/{case_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        details = resp.json()["data"]
        assert details["case_code"] == "CASE-DET-01"
        assert details["document_count"] == 1
        assert details["entity_count"] == 2

    def test_get_case_details_non_member_returns_404(self, client, db):
        sup_owner, token_owner = create_user_with_token(db, "owner_det", "owner@sih.gov.in", SystemRoles.SUPERVISOR)
        inv_stranger, token_stranger = create_user_with_token(db, "stranger_det", "stranger@sih.gov.in", SystemRoles.INVESTIGATOR)

        c_resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token_owner}"},
            json={"case_code": "CASE-SECRET-01", "title": "Secret Case", "jurisdiction": "South"},
        ).json()["data"]
        case_id = c_resp["case_id"]

        # Stranger attempts access -> 404 Not Found (RESOURCE_NOT_FOUND)
        resp = client.get(
            f"/api/v1/cases/{case_id}",
            headers={"Authorization": f"Bearer {token_stranger}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == ErrorCodes.RESOURCE_NOT_FOUND


# ==============================================================================
# 4. CASE UPDATE TESTS (PATCH /api/v1/cases/{case_id})
# ==============================================================================

class TestCaseUpdate:

    def test_patch_case_fields_and_audit(self, client, db):
        sup, token = create_user_with_token(db, "sup_patch", "patch@sih.gov.in", SystemRoles.SUPERVISOR)

        c_resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json={"case_code": "CASE-PATCH-01", "title": "Original Title", "jurisdiction": "Old Jurisdiction"},
        ).json()["data"]
        case_id = UUID(c_resp["case_id"])

        # Patch title and jurisdiction
        patch_resp = client.patch(
            f"/api/v1/cases/{case_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Updated Title", "jurisdiction": "New Jurisdiction"},
        )
        assert patch_resp.status_code == 200
        updated = patch_resp.json()["data"]
        assert updated["title"] == "Updated Title"
        assert updated["jurisdiction"] == "New Jurisdiction"

        # Verify CASE_UPDATE audit event
        audit = (
            db.query(AuditLog)
            .filter_by(actor_uuid=sup.user_id, action_code="CASE_UPDATE", case_id=case_id)
            .first()
        )
        assert audit is not None
        assert audit.outcome == "SUCCESS"

    def test_patch_invalid_status_returns_422(self, client, db):
        sup, token = create_user_with_token(db, "sup_badstatus", "badstatus@sih.gov.in", SystemRoles.SUPERVISOR)

        c_resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json={"case_code": "CASE-STATUS-01", "title": "Status Test", "jurisdiction": "Central"},
        ).json()["data"]
        case_id = c_resp["case_id"]

        resp = client.patch(
            f"/api/v1/cases/{case_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "INVALID_BOGUS_STATUS"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == ErrorCodes.VALIDATION_ERROR


# ==============================================================================
# 5. CASE MEMBER ASSIGNMENT & LISTING TESTS
# ==============================================================================

class TestCaseMembers:

    def test_assign_member_and_list(self, client, db):
        sup, token_sup = create_user_with_token(db, "sup_member_mgmt", "sup_mgmt@sih.gov.in", SystemRoles.SUPERVISOR)
        inv_target, _ = create_user_with_token(db, "inv_target", "target@sih.gov.in", SystemRoles.INVESTIGATOR)

        # 1. Create case
        c_resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token_sup}"},
            json={"case_code": "CASE-MEM-01", "title": "Membership Test", "jurisdiction": "Delhi"},
        ).json()["data"]
        case_id = UUID(c_resp["case_id"])

        # 2. Assign investigator to case
        assign_resp = client.post(
            f"/api/v1/cases/{case_id}/members",
            headers={"Authorization": f"Bearer {token_sup}"},
            json={"user_id": str(inv_target.user_id), "role_in_case": "INVESTIGATOR"},
        )
        assert assign_resp.status_code == 201
        member_data = assign_resp.json()["data"]
        assert member_data["username"] == "inv_target"
        assert member_data["role_in_case"] == "INVESTIGATOR"

        # Verify CASE_MEMBER_ADD audit
        audit = (
            db.query(AuditLog)
            .filter_by(actor_uuid=sup.user_id, action_code="CASE_MEMBER_ADD", case_id=case_id)
            .first()
        )
        assert audit is not None
        assert audit.outcome == "SUCCESS"

        # 3. List members
        list_resp = client.get(
            f"/api/v1/cases/{case_id}/members",
            headers={"Authorization": f"Bearer {token_sup}"},
        )
        assert list_resp.status_code == 200
        members = list_resp.json()["data"]
        usernames = [m["username"] for m in members]
        assert "sup_member_mgmt" in usernames
        assert "inv_target" in usernames

        # Verify no password hashes or tokens exposed
        for m in members:
            assert "password" not in m
            assert "password_hash" not in m
            assert "token" not in m

    def test_assign_nonexistent_user_returns_404(self, client, db):
        sup, token = create_user_with_token(db, "sup_nonexist", "nonexist@sih.gov.in", SystemRoles.SUPERVISOR)

        c_resp = client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"},
            json={"case_code": "CASE-NOUSER-01", "title": "No User Case", "jurisdiction": "Delhi"},
        ).json()["data"]
        case_id = c_resp["case_id"]

        random_user_id = str(uuid4())
        resp = client.post(
            f"/api/v1/cases/{case_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": random_user_id, "role_in_case": "INVESTIGATOR"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == ErrorCodes.RESOURCE_NOT_FOUND
