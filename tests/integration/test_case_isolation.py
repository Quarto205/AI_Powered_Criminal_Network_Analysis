"""
Integration Test Suite for Server-Side Case Isolation, RBAC, and Authentication.
Strictly verifies:
- Invariant 1: Server-Side Security Enforcement
- Invariant 2: 404 Case-Isolation Rule (Non-members receive 404 Not Found, NEVER 403, and audit CASE_ACCESS_DENIED)
- Invariant 3: Stateless JWT Bearer Authorization
- Invariant 4: Immutable Security Event Auditing
- Direct ID / IDOR Cross-Case Access Protection
"""

import io
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.main import app
from backend.config.security import SecuritySettings, set_security_settings
from backend.db.base import Base
from backend.db.models.analytics import AuditLog
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.session import get_db, get_engine, get_session_factory
from backend.repositories.document_repository import DocumentRepository
from backend.schemas.document_jobs import DocumentRecord, DocumentState
from backend.security.audit import SecurityAuditAction
from backend.security.password import hash_password
from backend.security.rbac import Permissions, SystemRoles
from backend.security.tokens import create_access_token


from sqlalchemy.pool import StaticPool

# Authoritative database engine and sessionmaker (PostgreSQL if available, fallback to in-memory SQLite)
test_engine = get_engine()
with test_engine.connect() as _test_conn:
    pass
TestingSessionLocal = get_session_factory(test_engine)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Sets test configuration and creates database schema."""
    test_settings = SecuritySettings(
        jwt_secret_key="case-isolation-test-deterministic-jwt-secret-key-32b!",
        jwt_algorithm="HS256",
        jwt_access_token_expire_seconds=28800,
    )
    set_security_settings(test_settings)
    Base.metadata.create_all(test_engine)
    app.dependency_overrides[get_db] = override_get_db
    from apps.api.routers.documents import get_document_service, get_repository, get_storage, get_worker_bridge
    from backend.services.document_service import DocumentService
    test_repo = DocumentRepository(session_factory=TestingSessionLocal)
    app.dependency_overrides[get_repository] = lambda: test_repo
    app.dependency_overrides[get_document_service] = lambda: DocumentService(
        repository=test_repo,
        storage=get_storage(),
        worker_bridge=get_worker_bridge(),
    )

    # Seed roles in test DB
    session = TestingSessionLocal()
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
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()


# Helper function to create users with roles
def create_test_user(
    db,
    username: str,
    email: str,
    password: str = "SecurePass123!",
    role_name: str = SystemRoles.INVESTIGATOR,
    account_status: str = "ACTIVE",
) -> User:
    user = db.query(User).filter_by(username=username).first()
    if not user:
        user = User(
            user_id=uuid4(),
            username=username,
            email=email,
            password_hash=hash_password(password),
            account_status=account_status,
        )
        db.add(user)
        db.commit()
    else:
        user.password_hash = hash_password(password)
        user.account_status = account_status
        user.email = email
        db.commit()

    role = db.query(Role).filter_by(name=role_name).first()
    if not role:
        role = Role(role_id=uuid4(), name=role_name)
        db.add(role)
        db.commit()
    user_role = db.query(UserRole).filter_by(user_id=user.user_id, role_id=role.role_id).first()
    if not user_role:
        user_role = UserRole(user_id=user.user_id, role_id=role.role_id)
        db.add(user_role)
        db.commit()

    return user


# Helper function to create cases
def create_test_case(db, creator_user: User, case_code: str, title: str) -> Case:
    unique_suffix = uuid4().hex[:8].upper()
    actual_code = f"{case_code}-{unique_suffix}" if case_code else f"CASE-{unique_suffix}"
    case = Case(
        case_id=uuid4(),
        case_code=actual_code,
        title=title,
        description="Test case description",
        status="ACTIVE",
        jurisdiction="CENTRAL",
        created_by=creator_user.user_id,
    )
    db.add(case)
    db.commit()
    return case


# Helper function to assign case membership
def add_case_member(db, case: Case, user: User, role_in_case: str = SystemRoles.INVESTIGATOR) -> CaseMember:
    member = CaseMember(
        case_member_id=uuid4(),
        case_id=case.case_id,
        user_id=user.user_id,
        role_in_case=role_in_case,
    )
    db.add(member)
    db.commit()
    return member


# ==============================================================================
# 1. AUTHENTICATION & LOGIN INTEGRATION TESTS
# ==============================================================================

class TestAuthEndpoints:

    def test_login_success(self, client, db_session):
        user = create_test_user(
            db=db_session,
            username="investigator_login_ok",
            email="ok@sih.gov.in",
            password="SecretPassword123!",
            role_name=SystemRoles.INVESTIGATOR,
        )

        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "investigator_login_ok", "password": "SecretPassword123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        token = data["data"]["access_token"]
        assert token is not None
        assert data["data"]["user"]["username"] == "investigator_login_ok"
        assert SystemRoles.INVESTIGATOR in data["data"]["user"]["roles"]

        # Verify AUTH_LOGIN_SUCCESS recorded in audit_logs table
        audit_row = (
            db_session.query(AuditLog)
            .filter_by(
                actor_uuid=user.user_id,
                action_code=SecurityAuditAction.AUTH_LOGIN_SUCCESS,
            )
            .first()
        )
        assert audit_row is not None
        assert audit_row.outcome == "SUCCESS"

    def test_login_wrong_password_returns_401_and_audits(self, client, db_session):
        user = create_test_user(
            db=db_session,
            username="investigator_wrong_pw",
            email="wrong_pw@sih.gov.in",
            password="RealPassword123!",
        )

        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "investigator_wrong_pw", "password": "IncorrectPassword!"},
        )
        assert resp.status_code == 401
        assert "Invalid username or password" in resp.json()["detail"]

        # Verify AUTH_LOGIN_FAILURE recorded in audit_logs
        audit_row = (
            db_session.query(AuditLog)
            .filter_by(
                actor_uuid=user.user_id,
                action_code=SecurityAuditAction.AUTH_LOGIN_FAILURE,
            )
            .first()
        )
        assert audit_row is not None
        assert audit_row.outcome == "FAILURE"

    def test_login_unknown_username_returns_401_no_enumeration(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent_investigator_user", "password": "AnyPassword123!"},
        )
        assert resp.status_code == 401
        # Generic error message to prevent enumeration
        assert "Invalid username or password" in resp.json()["detail"]

    def test_login_suspended_user_returns_401_generic(self, client, db_session):
        user = create_test_user(
            db=db_session,
            username="suspended_investigator",
            email="suspended@sih.gov.in",
            password="ValidPassword123!",
            account_status="SUSPENDED",
        )

        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "suspended_investigator", "password": "ValidPassword123!"},
        )
        assert resp.status_code == 401
        assert "Invalid username or password" in resp.json()["detail"]

    def test_get_me_profile_with_bearer_token(self, client, db_session):
        user = create_test_user(
            db=db_session,
            username="investigator_me",
            email="me@sih.gov.in",
            role_name=SystemRoles.INVESTIGATOR,
        )
        token = create_access_token(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=[SystemRoles.INVESTIGATOR],
        )

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["username"] == "investigator_me"
        assert SystemRoles.INVESTIGATOR in data["roles"]

    def test_get_me_missing_token_returns_401(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ==============================================================================
# 2. CANONICAL CASE-ISOLATION TESTS (404 RULE & AUDITING)
# ==============================================================================

class TestCaseIsolationAndRBAC:

    def test_canonical_non_member_case_access_returns_404_not_403(self, client, db_session):
        """
        CANONICAL REQUIREMENT (Section 4, 43):
        User A belongs to Case 1.
        User B belongs to Case 2.
        User B attempts to access Case 1.
        Must return 404 Not Found (NEVER 403), and record CASE_ACCESS_DENIED in audit_logs.
        """
        # User A -> Case 1
        user_a = create_test_user(db_session, f"user_a_iso_{uuid4().hex[:8]}", f"usera_{uuid4().hex[:8]}@sih.gov.in")
        case_1 = create_test_case(db_session, user_a, "CASE-ISO-001", "Counterfeiting Investigation Alpha")
        add_case_member(db_session, case_1, user_a, SystemRoles.INVESTIGATOR)

        # User B -> Case 2
        user_b = create_test_user(db_session, f"user_b_iso_{uuid4().hex[:8]}", f"userb_{uuid4().hex[:8]}@sih.gov.in")
        case_2 = create_test_case(db_session, user_b, "CASE-ISO-002", "Smuggling Network Beta")
        add_case_member(db_session, case_2, user_b, SystemRoles.INVESTIGATOR)

        token_b = create_access_token(
            user_id=user_b.user_id,
            username=user_b.username,
            email=user_b.email,
            roles=[SystemRoles.INVESTIGATOR],
        )

        pdf_bytes = f"%PDF-1.4 dummy case content {uuid4()}".encode()

        # User B attempts to upload to Case 1
        response = client.post(
            f"/api/v1/cases/{case_1.case_id}/documents",
            headers={"Authorization": f"Bearer {token_b}"},
            files={"file": ("memo.pdf", pdf_bytes, "application/pdf")},
        )

        # Non-member MUST receive 404 Not Found, NEVER 403 Forbidden!
        assert response.status_code == 404
        assert response.status_code != 403
        assert "Resource not found" in response.json()["detail"]

        # Verify CASE_ACCESS_DENIED recorded in audit_logs table
        audit_row = (
            db_session.query(AuditLog)
            .filter_by(
                actor_uuid=user_b.user_id,
                case_id=case_1.case_id,
                action_code=SecurityAuditAction.CASE_ACCESS_DENIED,
            )
            .first()
        )
        assert audit_row is not None
        assert audit_row.outcome == "DENIED"

    def test_authorized_case_member_upload_succeeds(self, client, db_session):
        """
        Authorized case member with DOCUMENT_UPLOAD permission succeeds (202 Accepted).
        """
        user_a = create_test_user(db_session, f"user_member_ok_{uuid4().hex[:8]}", f"member_ok_{uuid4().hex[:8]}@sih.gov.in")
        case = create_test_case(db_session, user_a, "CASE-AUTH-OK", "Authorized Case")
        add_case_member(db_session, case, user_a, SystemRoles.INVESTIGATOR)

        token_a = create_access_token(
            user_id=user_a.user_id,
            username=user_a.username,
            email=user_a.email,
            roles=[SystemRoles.INVESTIGATOR],
        )

        # Upload document as authorized member with unique content so file hash is unique
        pdf_bytes = f"%PDF-1.4 valid member content {uuid4()}".encode()
        response = client.post(
            f"/api/v1/cases/{case.case_id}/documents",
            headers={"Authorization": f"Bearer {token_a}"},
            files={"file": ("valid_evidence.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "RECEIVED"

    def test_privilege_denial_returns_403_not_404(self, client, db_session):
        """
        User IS a member of the case, but role in case lacks required permission.
        Must return 403 Forbidden (NOT 404) and record PERMISSION_DENIED.
        """
        user = create_test_user(db_session, f"readonly_member_{uuid4().hex[:8]}", f"ro_{uuid4().hex[:8]}@sih.gov.in", role_name="CUSTOM_VIEWER")
        case = create_test_case(db_session, user, "CASE-RO-001", "Readonly Case")
        # Member with READONLY role lacking DOCUMENT_UPLOAD
        add_case_member(db_session, case, user, role_in_case="CUSTOM_VIEWER")

        token = create_access_token(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=["CUSTOM_VIEWER"],
        )

        response = client.post(
            f"/api/v1/cases/{case.case_id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("unauthorized_upload.pdf", b"%PDF-1.4 data", "application/pdf")},
        )

        # Member with insufficient permissions receives 403 Forbidden
        assert response.status_code == 403
        assert response.status_code != 404
        assert "Insufficient privileges" in response.json()["detail"]

        # Verify PERMISSION_DENIED recorded in audit_logs
        audit_row = (
            db_session.query(AuditLog)
            .filter_by(
                actor_uuid=user.user_id,
                case_id=case.case_id,
                action_code=SecurityAuditAction.PERMISSION_DENIED,
            )
            .first()
        )
        assert audit_row is not None
        assert audit_row.outcome == "DENIED"

    def test_direct_id_idor_cross_case_access_rejected_with_404(self, client, db_session):
        """
        Direct document ID lookup (/api/v1/documents/{document_id}).
        User B (Case 2 member) attempts to access document belonging to Case 1.
        Must return 404 Not Found (NEVER 403) and record CASE_ACCESS_DENIED.
        """
        repo = DocumentRepository(session_factory=TestingSessionLocal)

        # Create Case 1 and Case 2 with unique users and cases
        user_1 = create_test_user(db_session, f"idor_user_1_{uuid4().hex[:8]}", f"idor1_{uuid4().hex[:8]}@sih.gov.in")
        case_1 = create_test_case(db_session, user_1, "CASE-IDOR-001", "Case 1")
        add_case_member(db_session, case_1, user_1, SystemRoles.INVESTIGATOR)

        user_2 = create_test_user(db_session, f"idor_user_2_{uuid4().hex[:8]}", f"idor2_{uuid4().hex[:8]}@sih.gov.in")
        case_2 = create_test_case(db_session, user_2, "CASE-IDOR-002", "Case 2")
        add_case_member(db_session, case_2, user_2, SystemRoles.INVESTIGATOR)

        # Register a document in Case 1 repository with unique document ID and unique hash
        doc_1_id = uuid4()
        unique_hash = f"hash_case1_{uuid4().hex}"
        repo.create(
            document_id=doc_1_id,
            case_id=case_1.case_id,
            filename="confidential_case1.pdf",
            file_type="application/pdf",
            file_hash=unique_hash,
            storage_key=f"cases/{case_1.case_id}/docs/{doc_1_id}/confidential.pdf",
            initial_status=DocumentState.RECEIVED,
        )

        token_2 = create_access_token(
            user_id=user_2.user_id,
            username=user_2.username,
            email=user_2.email,
            roles=[SystemRoles.INVESTIGATOR],
        )

        # User 2 attempts direct-ID access to Case 1 document
        resp = client.get(
            f"/api/v1/documents/{doc_1_id}",
            headers={"Authorization": f"Bearer {token_2}"},
        )
        assert resp.status_code == 404
        assert "Resource not found" in resp.json()["detail"]

        # Verify CASE_ACCESS_DENIED recorded
        audit_row = (
            db_session.query(AuditLog)
            .filter_by(
                actor_uuid=user_2.user_id,
                case_id=case_1.case_id,
                action_code=SecurityAuditAction.CASE_ACCESS_DENIED,
            )
            .first()
        )
        assert audit_row is not None
        assert audit_row.outcome == "DENIED"

    def test_random_case_id_returns_404(self, client, db_session):
        user = create_test_user(db_session, f"random_case_user_{uuid4().hex[:8]}", f"rand_{uuid4().hex[:8]}@sih.gov.in")
        token = create_access_token(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=[SystemRoles.INVESTIGATOR],
        )
        random_case_id = uuid4()

        resp = client.post(
            f"/api/v1/cases/{random_case_id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("memo.pdf", b"%PDF-1.4 data", "application/pdf")},
        )
        assert resp.status_code == 404
        assert "Resource not found" in resp.json()["detail"]

        # Verify audit trail recorded CASE_ACCESS_DENIED safely with case_id = None
        audit_row = (
            db_session.query(AuditLog)
            .filter_by(
                actor_uuid=user.user_id,
                action_code=SecurityAuditAction.CASE_ACCESS_DENIED,
            )
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert audit_row is not None
        assert audit_row.case_id is None
        assert audit_row.outcome == "DENIED"
