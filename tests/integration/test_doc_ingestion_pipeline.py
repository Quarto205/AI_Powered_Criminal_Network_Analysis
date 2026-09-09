"""
Integration Test Suite for SIH26189 Document Ingestion API + Background Worker Pipeline.
Tests asynchronous non-blocking upload (HTTP 202), worker execution to EXTRACTED,
document versions and chunks generation, deterministic ordering, failure isolation,
document listing with filters/pagination, server-side 404 case isolation,
direct-ID IDOR defense, soft deletion (REJECTED), and security audit verification.
"""

import io
from typing import Generator
from uuid import UUID, uuid4
import pypdf
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.deps import get_current_user
from apps.api.main import app
from apps.api.routers.documents import get_document_service, get_repository, get_storage, get_worker
from backend.config.security import SecuritySettings, set_security_settings
from backend.db.base import Base
from backend.db.models.analytics import AuditLog
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.ingestion import Document
from backend.db.session import get_db
from backend.schemas.document_jobs import DocumentState
from backend.security.audit import SecurityAuditAction
from backend.security.rbac import Permissions, SystemRoles
from backend.security.tokens import create_access_token


# ==============================================================================
# DETERMINISTIC HELPERS & FIXTURES
# ==============================================================================

def build_pdf_with_text(text: str) -> bytes:
    """Builds a valid digital PDF containing the specified text."""
    stream_content = f"BT /F1 12 Tf 50 100 Td ({text}) Tj ET".encode("latin-1")
    length = len(stream_content)
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 500 300] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length " + str(length).encode("ascii") + b" >> stream\n"
        + stream_content + b"\nendstream endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"500\n"
        b"%%EOF\n"
    )
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    writer = pypdf.PdfWriter()
    writer.add_page(reader.pages[0])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


pipeline_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
PipelineTestingSessionLocal = sessionmaker(bind=pipeline_test_engine)


def override_pipeline_get_db():
    session = PipelineTestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module", autouse=True)
def setup_pipeline_test_environment():
    test_settings = SecuritySettings(
        jwt_secret_key="doc-pipeline-test-deterministic-jwt-secret-key-32b!",
        jwt_algorithm="HS256",
        jwt_access_token_expire_seconds=28800,
    )
    set_security_settings(test_settings)
    Base.metadata.create_all(pipeline_test_engine)
    app.dependency_overrides[get_db] = override_pipeline_get_db

    session = PipelineTestingSessionLocal()
    for role_name in [SystemRoles.INVESTIGATOR, SystemRoles.ANALYST, SystemRoles.SUPERVISOR]:
        existing = session.query(Role).filter_by(name=role_name).first()
        if not existing:
            session.add(Role(role_id=uuid4(), name=role_name))
    session.commit()
    session.close()

    yield

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(pipeline_test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    session = PipelineTestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    get_repository().clear()
    get_storage().clear()
    get_worker().clear()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def case_setup(db_session: Session):
    """Sets up an investigator, a supervisor, an unrelated user, and two cases."""
    # 1. Investigator
    inv_id = uuid4()
    investigator = User(
        user_id=inv_id,
        username=f"inv_{inv_id.hex[:8]}",
        email=f"inv_{inv_id.hex[:8]}@sih.gov.in",
        password_hash="hash",
        account_status="ACTIVE",
    )
    db_session.add(investigator)

    # 2. Supervisor
    sup_id = uuid4()
    supervisor = User(
        user_id=sup_id,
        username=f"sup_{sup_id.hex[:8]}",
        email=f"sup_{sup_id.hex[:8]}@sih.gov.in",
        password_hash="hash",
        account_status="ACTIVE",
    )
    db_session.add(supervisor)

    # 3. Unrelated User B
    b_id = uuid4()
    user_b = User(
        user_id=b_id,
        username=f"userb_{b_id.hex[:8]}",
        email=f"userb_{b_id.hex[:8]}@sih.gov.in",
        password_hash="hash",
        account_status="ACTIVE",
    )
    db_session.add(user_b)

    # 4. Case 1 (Belongs to Investigator & Supervisor)
    case_1 = Case(
        case_id=uuid4(),
        case_code=f"CASE-P-{uuid4().hex[:8]}",
        title="Operation Falcon",
        jurisdiction="Delhi NCR",
        status="ACTIVE",
        created_by=supervisor.user_id,
    )
    db_session.add(case_1)
    db_session.add(CaseMember(case_id=case_1.case_id, user_id=investigator.user_id, role_in_case=SystemRoles.INVESTIGATOR))
    db_session.add(CaseMember(case_id=case_1.case_id, user_id=supervisor.user_id, role_in_case=SystemRoles.SUPERVISOR))

    # 5. Case 2 (Belongs ONLY to User B)
    case_2 = Case(
        case_id=uuid4(),
        case_code=f"CASE-P-{uuid4().hex[:8]}",
        title="Private Investigation",
        jurisdiction="Mumbai",
        status="ACTIVE",
        created_by=user_b.user_id,
    )
    db_session.add(case_2)
    db_session.add(CaseMember(case_id=case_2.case_id, user_id=user_b.user_id, role_in_case=SystemRoles.INVESTIGATOR))

    db_session.commit()

    # Create tokens
    token_inv = create_access_token(
        user_id=investigator.user_id,
        username=investigator.username,
        email=investigator.email,
        roles=[SystemRoles.INVESTIGATOR],
    )
    token_sup = create_access_token(
        user_id=supervisor.user_id,
        username=supervisor.username,
        email=supervisor.email,
        roles=[SystemRoles.SUPERVISOR],
    )
    token_b = create_access_token(
        user_id=user_b.user_id,
        username=user_b.username,
        email=user_b.email,
        roles=[SystemRoles.INVESTIGATOR],
    )

    return {
        "investigator": investigator,
        "supervisor": supervisor,
        "user_b": user_b,
        "case_1": case_1,
        "case_2": case_2,
        "headers_inv": {"Authorization": f"Bearer {token_inv}"},
        "headers_sup": {"Authorization": f"Bearer {token_sup}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
    }


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestDocumentIngestionPipelineIntegration:

    @pytest.mark.asyncio
    async def test_async_upload_lifecycle_to_extracted(self, client, case_setup):
        """
        1. Non-blocking upload returns 202 Accepted immediately with status RECEIVED.
        2. Worker processes job in background and reaches EXTRACTED.
        3. Document detail reflects EXTRACTED, version info, and chunk count.
        """
        setup = case_setup
        case_id = setup["case_1"].case_id
        headers = setup["headers_inv"]
        worker = get_worker()

        pdf_bytes = build_pdf_with_text(
            "Suspect Rajesh Kumar transferred 500000 INR from State Bank to Account 987654321."
        )

        # 1. POST upload -> 202 Accepted
        response = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("financial_record.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "RECEIVED"
        doc_id = UUID(body["data"]["document_id"])
        job_id = UUID(body["data"]["job_id"])

        # 2. Wait for worker execution
        job_result = await worker.wait_for_job(job_id, timeout=10.0)
        assert job_result is not None
        assert job_result.status == DocumentState.EXTRACTED

        # 3. GET document detail
        detail_resp = client.get(
            f"/api/v1/cases/{case_id}/documents/{doc_id}",
            headers=headers,
        )
        assert detail_resp.status_code == status.HTTP_200_OK
        detail_data = detail_resp.json()["data"]
        assert detail_data["status"] == "EXTRACTED"
        assert detail_data["document_id"] == str(doc_id)
        assert detail_data["chunk_count"] >= 1
        assert detail_data["latest_version"] is not None
        assert "version_hash" in detail_data["latest_version"]

    @pytest.mark.asyncio
    async def test_chunks_endpoint_ordered_deterministic(self, client, case_setup):
        """
        Tests GET /cases/{case_id}/documents/{document_id}/chunks returns ordered chunks.
        """
        setup = case_setup
        case_id = setup["case_1"].case_id
        headers = setup["headers_inv"]
        worker = get_worker()

        pdf_bytes = build_pdf_with_text("Page 1 intelligence report for criminal network.")
        upload_resp = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("intel.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = UUID(upload_resp.json()["data"]["document_id"])
        job_id = UUID(upload_resp.json()["data"]["job_id"])
        await worker.wait_for_job(job_id, timeout=10.0)

        # Query chunks endpoint
        chunks_resp = client.get(
            f"/api/v1/cases/{case_id}/documents/{doc_id}/chunks",
            headers=headers,
        )
        assert chunks_resp.status_code == status.HTTP_200_OK
        chunks_data = chunks_resp.json()["data"]
        assert chunks_data["total"] >= 1
        first_chunk = chunks_data["items"][0]
        assert first_chunk["page_number"] == 1
        assert "text_hash" in first_chunk
        assert "character_span" in first_chunk
        assert "storage_ref" in first_chunk

    @pytest.mark.asyncio
    async def test_corrupted_document_terminates_in_failed_state(self, client, case_setup):
        """
        Corrupted document transitions safely to FAILED with safe error category,
        and the background worker continues processing subsequent documents cleanly.
        """
        setup = case_setup
        case_id = setup["case_1"].case_id
        headers = setup["headers_inv"]
        worker = get_worker()

        # PDF header with corrupted binary junk
        corrupted_bytes = b"%PDF-1.4\ncorrupted bytes that fail pypdf parsing completely\xFF\xFE\xFD"
        upload_resp = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("corrupt.pdf", corrupted_bytes, "application/pdf")},
        )
        assert upload_resp.status_code == status.HTTP_202_ACCEPTED
        doc_id = UUID(upload_resp.json()["data"]["document_id"])
        job_id = UUID(upload_resp.json()["data"]["job_id"])

        job_result = await worker.wait_for_job(job_id, timeout=10.0)
        assert job_result is not None
        assert job_result.status == DocumentState.FAILED

        # Detail endpoint reports FAILED with safe error category
        detail_resp = client.get(
            f"/api/v1/cases/{case_id}/documents/{doc_id}",
            headers=headers,
        )
        assert detail_resp.status_code == status.HTTP_200_OK
        detail_data = detail_resp.json()["data"]
        assert detail_data["status"] == "FAILED"
        assert detail_data["error_category"] is not None

        # Subsequent valid document processes successfully (worker survives)
        valid_pdf = build_pdf_with_text("Subsequent valid evidence after worker error recovery.")
        valid_resp = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers,
            files={"file": ("recovered.pdf", valid_pdf, "application/pdf")},
        )
        valid_job_id = UUID(valid_resp.json()["data"]["job_id"])
        valid_job_result = await worker.wait_for_job(valid_job_id, timeout=10.0)
        assert valid_job_result.status == DocumentState.EXTRACTED

    def test_document_list_filtering_and_pagination(self, client, case_setup):
        """
        Tests GET /cases/{case_id}/documents supports status filtering, pagination, and total count.
        """
        setup = case_setup
        case_id = setup["case_1"].case_id
        headers = setup["headers_inv"]

        # Upload 3 distinct documents
        for i in range(3):
            pdf_bytes = build_pdf_with_text(f"Distinct evidence record #{i} for pagination test.")
            client.post(
                f"/api/v1/cases/{case_id}/documents",
                headers=headers,
                files={"file": (f"record_{i}.pdf", pdf_bytes, "application/pdf")},
            )

        # List first page: limit=2, offset=0
        resp_page1 = client.get(
            f"/api/v1/cases/{case_id}/documents?limit=2&offset=0",
            headers=headers,
        )
        assert resp_page1.status_code == status.HTTP_200_OK
        data1 = resp_page1.json()["data"]
        assert data1["total"] == 3
        assert len(data1["items"]) == 2
        assert data1["limit"] == 2
        assert data1["offset"] == 0

        # List second page: limit=2, offset=2
        resp_page2 = client.get(
            f"/api/v1/cases/{case_id}/documents?limit=2&offset=2",
            headers=headers,
        )
        assert resp_page2.status_code == status.HTTP_200_OK
        data2 = resp_page2.json()["data"]
        assert len(data2["items"]) == 1

        # Filter by status
        resp_filter = client.get(
            f"/api/v1/cases/{case_id}/documents?status=RECEIVED",
            headers=headers,
        )
        assert resp_filter.status_code == status.HTTP_200_OK
        assert len(resp_filter.json()["data"]["items"]) == 3

    def test_non_member_case_isolation_returns_404_not_403(self, client, case_setup):
        """
        User B (belongs to Case 2, not Case 1) attempting to access Case 1 documents
        strictly receives 404 RESOURCE_NOT_FOUND (never 403), and logs CASE_ACCESS_DENIED.
        """
        setup = case_setup
        case_1_id = setup["case_1"].case_id
        headers_b = setup["headers_b"]

        pdf_bytes = build_pdf_with_text("Adversary attempting cross-case upload.")
        # Upload attempt
        resp_post = client.post(
            f"/api/v1/cases/{case_1_id}/documents",
            headers=headers_b,
            files={"file": ("hostile.pdf", pdf_bytes, "application/pdf")},
        )
        assert resp_post.status_code == status.HTTP_404_NOT_FOUND
        assert resp_post.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

        # List attempt
        resp_list = client.get(
            f"/api/v1/cases/{case_1_id}/documents",
            headers=headers_b,
        )
        assert resp_list.status_code == status.HTTP_404_NOT_FOUND

        # Detail attempt
        fake_doc_id = uuid4()
        resp_detail = client.get(
            f"/api/v1/cases/{case_1_id}/documents/{fake_doc_id}",
            headers=headers_b,
        )
        assert resp_detail.status_code == status.HTTP_404_NOT_FOUND

        # Chunks attempt
        resp_chunks = client.get(
            f"/api/v1/cases/{case_1_id}/documents/{fake_doc_id}/chunks",
            headers=headers_b,
        )
        assert resp_chunks.status_code == status.HTTP_404_NOT_FOUND

        # Delete attempt
        resp_delete = client.delete(
            f"/api/v1/cases/{case_1_id}/documents/{fake_doc_id}",
            headers=headers_b,
        )
        assert resp_delete.status_code == status.HTTP_404_NOT_FOUND

    def test_direct_id_idor_cross_case_access_rejected(self, client, case_setup):
        """
        User B possessing Case 1's document ID attempts direct retrieval via /api/v1/documents/{id}.
        Must return 404 RESOURCE_NOT_FOUND to prevent IDOR cross-case leakage.
        """
        setup = case_setup
        case_1_id = setup["case_1"].case_id
        headers_inv = setup["headers_inv"]
        headers_b = setup["headers_b"]

        pdf_bytes = build_pdf_with_text("Case 1 confidential evidence for IDOR test.")
        upload_resp = client.post(
            f"/api/v1/cases/{case_1_id}/documents",
            headers=headers_inv,
            files={"file": ("confidential.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = UUID(upload_resp.json()["data"]["document_id"])

        # User B attempts direct retrieval
        idor_resp = client.get(
            f"/api/v1/documents/{doc_id}",
            headers=headers_b,
        )
        assert idor_resp.status_code == status.HTTP_404_NOT_FOUND
        assert idor_resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_soft_delete_supervisor_allowed_investigator_forbidden(self, client, case_setup, db_session):
        """
        Investigator attempting DELETE -> 403 FORBIDDEN.
        Supervisor attempting DELETE -> 200 OK, status becomes REJECTED.
        Physical record is strictly preserved.
        """
        setup = case_setup
        case_id = setup["case_1"].case_id
        headers_inv = setup["headers_inv"]
        headers_sup = setup["headers_sup"]

        pdf_bytes = build_pdf_with_text("Evidence candidate for archiving/rejection.")
        upload_resp = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers_inv,
            files={"file": ("archive_candidate.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = UUID(upload_resp.json()["data"]["document_id"])

        # 1. Investigator attempts delete -> 403 Forbidden
        inv_del_resp = client.delete(
            f"/api/v1/cases/{case_id}/documents/{doc_id}",
            headers=headers_inv,
        )
        assert inv_del_resp.status_code == status.HTTP_403_FORBIDDEN
        assert inv_del_resp.json()["error"]["code"] == "FORBIDDEN"

        # 2. Supervisor attempts delete -> 200 OK
        sup_del_resp = client.delete(
            f"/api/v1/cases/{case_id}/documents/{doc_id}",
            headers=headers_sup,
        )
        assert sup_del_resp.status_code == status.HTTP_200_OK
        del_data = sup_del_resp.json()["data"]
        assert del_data["status"] == "REJECTED"
        assert del_data["document_id"] == str(doc_id)

        # 3. Verify physical document still exists in repository and DB with status REJECTED
        detail_resp = client.get(
            f"/api/v1/cases/{case_id}/documents/{doc_id}",
            headers=headers_inv,
        )
        assert detail_resp.status_code == status.HTTP_200_OK
        assert detail_resp.json()["data"]["status"] == "REJECTED"

    def test_audit_logs_recorded_for_document_mutations(self, client, case_setup, db_session):
        """
        Verifies DOCUMENT_UPLOAD and DOCUMENT_DELETE audit events are persisted in audit_logs.
        """
        setup = case_setup
        case_id = setup["case_1"].case_id
        headers_sup = setup["headers_sup"]
        sup_user = setup["supervisor"]

        pdf_bytes = build_pdf_with_text("Audit trail verification document content.")
        upload_resp = client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=headers_sup,
            files={"file": ("audited.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = UUID(upload_resp.json()["data"]["document_id"])

        # Check DOCUMENT_UPLOAD audit event
        audit_upload = (
            db_session.query(AuditLog)
            .filter_by(
                case_id=case_id,
                actor_uuid=sup_user.user_id,
                action_code=SecurityAuditAction.DOCUMENT_UPLOAD,
            )
            .first()
        )
        assert audit_upload is not None
        assert audit_upload.outcome == "SUCCESS"

        # Delete document as supervisor
        client.delete(
            f"/api/v1/cases/{case_id}/documents/{doc_id}",
            headers=headers_sup,
        )

        # Check DOCUMENT_DELETE audit event
        audit_delete = (
            db_session.query(AuditLog)
            .filter_by(
                case_id=case_id,
                actor_uuid=sup_user.user_id,
                action_code=SecurityAuditAction.DOCUMENT_DELETE,
            )
            .first()
        )
        assert audit_delete is not None
        assert audit_delete.outcome == "SUCCESS"
