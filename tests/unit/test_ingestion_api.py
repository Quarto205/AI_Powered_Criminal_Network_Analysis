"""
Unit Test Suite for SIH26189 Document Ingestion API & Validation.
Tests magic bytes validation, MIME detection, size limits, path traversal defenses,
SHA-256 deduplication, tracking ID propagation, and universal response envelopes.
"""

from io import BytesIO
from typing import Generator
from uuid import UUID, uuid4
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sqlalchemy.pool import StaticPool

from apps.api.deps import get_current_user
from apps.api.main import app
from apps.api.routers.documents import get_document_service, get_repository, get_storage
from backend.config.security import SecuritySettings, set_security_settings
from backend.db.base import Base
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.ingestion import Document
from backend.db.session import get_db, get_engine, get_session_factory
from backend.security.rbac import Permissions, SystemRoles
from backend.security.tokens import create_access_token


# Shared test database engine using StaticPool
ingestion_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
IngestionTestingSessionLocal = sessionmaker(bind=ingestion_test_engine)


def override_ingestion_get_db():
    session = IngestionTestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module", autouse=True)
def setup_ingestion_test_environment():
    test_settings = SecuritySettings(
        jwt_secret_key="ingestion-test-deterministic-jwt-secret-key-32b!",
        jwt_algorithm="HS256",
        jwt_access_token_expire_seconds=28800,
    )
    set_security_settings(test_settings)
    Base.metadata.create_all(ingestion_test_engine)
    app.dependency_overrides[get_db] = override_ingestion_get_db

    from backend.repositories.document_repository import DocumentRepository
    from backend.services.document_service import DocumentService
    from apps.api.routers.documents import get_worker_bridge
    test_repo = DocumentRepository(session_factory=IngestionTestingSessionLocal)
    test_service = DocumentService(
        repository=test_repo,
        storage=get_storage(),
        worker_bridge=get_worker_bridge(),
    )
    app.dependency_overrides[get_repository] = lambda: test_repo
    app.dependency_overrides[get_document_service] = lambda: test_service

    # Seed roles in test DB
    session = IngestionTestingSessionLocal()
    for role_name in [SystemRoles.INVESTIGATOR, SystemRoles.ANALYST, SystemRoles.SUPERVISOR]:
        existing = session.query(Role).filter_by(name=role_name).first()
        if not existing:
            session.add(Role(role_id=uuid4(), name=role_name))
    session.commit()
    session.close()

    yield

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_repository, None)
    app.dependency_overrides.pop(get_document_service, None)
    Base.metadata.drop_all(ingestion_test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    session = IngestionTestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    get_repository().clear()
    get_storage().clear()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(db_session: Session):
    """Creates an investigator user and active case, returns auth headers and case_id."""
    u_id = uuid4()
    user = User(
        user_id=u_id,
        username=f"inv_{u_id.hex[:8]}",
        email=f"inv_{u_id.hex[:8]}@sih.gov.in",
        password_hash="argon2_placeholder",
        account_status="ACTIVE",
    )
    db_session.add(user)

    case = Case(
        case_id=uuid4(),
        case_code=f"CASE-{u_id.hex[:8]}",
        title="Unit Test Case",
        jurisdiction="Delhi NCR",
        status="ACTIVE",
        created_by=user.user_id,
    )
    db_session.add(case)

    member = CaseMember(
        case_id=case.case_id,
        user_id=user.user_id,
        role_in_case=SystemRoles.INVESTIGATOR,
    )
    db_session.add(member)
    db_session.commit()

    token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=[SystemRoles.INVESTIGATOR],
    )
    headers = {"Authorization": f"Bearer {token}"}
    return headers, case.case_id, user.user_id


# ==============================================================================
# 1. MAGIC BYTES & FILE VALIDATION TESTS
# ==============================================================================

class TestMagicBytesAndValidation:

    def test_valid_pdf_magic_bytes_accepted(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        pdf_content = b"%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF"

        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("report.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        body = response.json()
        assert body["success"] is True
        assert body["data"]["file_type"] == "application/pdf"
        assert body["data"]["status"] == "RECEIVED"
        assert body["data"]["case_id"] == str(case_id)

    def test_valid_png_magic_bytes_accepted(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"

        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("evidence.png", png_content, "image/png")},
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        body = response.json()
        assert body["data"]["file_type"] == "image/png"

    def test_valid_jpeg_magic_bytes_accepted(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        jpeg_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01"

        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("photo.jpg", jpeg_content, "image/jpeg")},
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        body = response.json()
        assert body["data"]["file_type"] == "image/jpeg"

    def test_spoofed_extension_rejected_by_magic_bytes(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        # Executable bytes disguised with .pdf filename
        exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF"

        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("malicious_executable.pdf", exe_content, "application/pdf")},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.json()
        assert body["success"] is False
        assert "Unsupported file format" in body["error"]["message"]

    def test_empty_document_rejected(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        empty_content = b""

        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("empty.pdf", empty_content, "application/pdf")},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.json()
        assert body["success"] is False
        assert "empty" in body["error"]["message"].lower()

    def test_oversized_payload_rejected(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        # Set max_file_size to 1KB to test limit enforcement safely without allocating 50MB
        service_override = app.dependency_overrides.get(get_document_service)
        doc_service = service_override() if service_override else get_document_service()
        orig_max = doc_service.max_file_size
        doc_service.max_file_size = 1024

        try:
            oversized_pdf = b"%PDF-1.4 " + (b"X" * 2048)
            response = client.post(
                f"/api/v1/cases/{case_id}/documents",
                headers=headers,
                files={"file": ("huge.pdf", oversized_pdf, "application/pdf")},
            )
            assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            body = response.json()
            assert body["success"] is False
            assert "exceeds maximum allowed size" in body["error"]["message"]
        finally:
            doc_service.max_file_size = orig_max

    def test_directory_traversal_filename_sanitized(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        pdf_content = b"%PDF-1.4 sample content"

        # Traversal in filename is sanitized by sanitize_filename
        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("../../../../etc/passwd.pdf", pdf_content, "application/pdf")},
        )
        # Should be rejected with 400 Bad Request due to path traversal sequence
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.json()
        assert body["success"] is False
        assert "traversal" in body["error"]["message"].lower()


# ==============================================================================
# 2. SHA-256 DEDUPLICATION TESTS
# ==============================================================================

class TestDeduplication:

    def test_duplicate_file_in_same_case_returns_409(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        pdf_content = b"%PDF-1.4 deterministic deduplication test payload"

        # First upload -> 202
        resp1 = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("doc1.pdf", pdf_content, "application/pdf")},
        )
        assert resp1.status_code == status.HTTP_202_ACCEPTED
        assert resp1.json()["success"] is True

        # Second upload of same content to same case -> 409 Conflict
        resp2 = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("doc2.pdf", pdf_content, "application/pdf")},
        )
        assert resp2.status_code == status.HTTP_409_CONFLICT
        body = resp2.json()
        assert body["success"] is False
        assert body["error"]["code"] == "CONFLICT"
        assert "already exists in case" in body["error"]["message"]

    def test_duplicate_file_across_different_cases_allowed(self, client, db_session, auth_headers):
        headers, case_1_id, user_id = auth_headers

        # Create second case and grant access to user
        case_2 = Case(
            case_id=uuid4(),
            case_code="CASE-UNIT-002",
            title="Second Case",
            jurisdiction="Mumbai",
            status="ACTIVE",
            created_by=user_id,
        )
        db_session.add(case_2)
        db_session.add(CaseMember(case_id=case_2.case_id, user_id=user_id, role_in_case=SystemRoles.INVESTIGATOR))
        db_session.commit()

        pdf_content = b"%PDF-1.4 shared evidence across investigations"

        # Upload to Case 1 -> 202
        resp1 = client.post(
            f"/api/v1/cases/{case_1_id}/documents",
            headers=headers,
            files={"file": ("evidence_case1.pdf", pdf_content, "application/pdf")},
        )
        assert resp1.status_code == status.HTTP_202_ACCEPTED

        # Upload exact same bytes to Case 2 -> 202 (cross-case duplicate is permitted)
        resp2 = client.post(
            f"/api/v1/cases/{case_2.case_id}/documents",
            headers=headers,
            files={"file": ("evidence_case2.pdf", pdf_content, "application/pdf")},
        )
        assert resp2.status_code == status.HTTP_202_ACCEPTED
        assert resp2.json()["success"] is True


# ==============================================================================
# 3. TRACKING ID & UNIVERSAL ENVELOPE TESTS
# ==============================================================================

class TestTrackingIdAndEnvelope:

    def test_tracking_id_propagated_in_body_and_header(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        client_tracking_id = str(uuid4())
        req_headers = {**headers, "X-Tracking-ID": client_tracking_id}

        pdf_content = b"%PDF-1.4 tracking test content"
        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=req_headers,
            files={"file": ("tracked.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        body = response.json()
        assert body["tracking_id"] == client_tracking_id
        assert response.headers.get("X-Tracking-ID") == client_tracking_id

    def test_error_envelope_contains_tracking_id(self, client, auth_headers):
        headers, case_id, _ = auth_headers
        custom_tracking_id = str(uuid4())
        req_headers = {**headers, "X-Tracking-ID": custom_tracking_id}

        # Request with empty content to trigger 400
        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=req_headers,
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["tracking_id"] == custom_tracking_id
        assert response.headers.get("X-Tracking-ID") == custom_tracking_id
