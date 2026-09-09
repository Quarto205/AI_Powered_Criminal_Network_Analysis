"""
Unit Test Suite for Core API Shell.
Verifies:
- Invariant 1: Universal JSON response envelope (success, data, error, tracking_id)
- Universal error envelope (code, message, details, tracking_id)
- Tracking ID generation, propagation, and X-Tracking-ID header
- Centralized exception handlers (401, 403, 404, 409, 422, 500)
- Snake_case contract on request and response schemas
"""

from uuid import UUID, uuid4
import pytest
from fastapi import APIRouter, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from apps.api.main import app
from apps.api.tracking import get_tracking_id, validate_or_generate_tracking_id
from backend.schemas.envelope import (
    ApiErrorResponse,
    ApiSuccessResponse,
    ErrorCodes,
    envelope_error,
    envelope_success,
)

# Sample router for testing controlled failure modes
sample_shell_router = APIRouter(prefix="/api/v1/sample-shell", tags=["sample-shell"])


class SampleItem(BaseModel):
    item_name: str = Field(..., min_length=3)
    item_count: int = Field(..., ge=1)


@sample_shell_router.get("/success")
def sample_success():
    return envelope_success(data={"message": "operation_successful"}, tracking_id=get_tracking_id())


@sample_shell_router.post("/validation-test")
def sample_validation(payload: SampleItem):
    return envelope_success(data=payload.model_dump(), tracking_id=get_tracking_id())


@sample_shell_router.get("/raise-401")
def raise_401():
    raise HTTPException(status_code=401, detail="Invalid credentials provided.")


@sample_shell_router.get("/raise-403")
def raise_403():
    raise HTTPException(status_code=403, detail="Forbidden: Insufficient privileges.")


@sample_shell_router.get("/raise-404")
def raise_404():
    raise HTTPException(status_code=404, detail="Resource not found.")


@sample_shell_router.get("/raise-409")
def raise_409():
    raise HTTPException(status_code=409, detail="A conflicting resource already exists.")


@sample_shell_router.get("/raise-500")
def raise_500():
    raise RuntimeError("Simulated unhandled internal server error for testing.")


# Mount sample router to app
app.include_router(sample_shell_router)


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. ENVELOPE SCHEMA & FACTORY TESTS
# ==============================================================================

class TestEnvelopeSchemas:

    def test_success_envelope_structure(self):
        tid = str(uuid4())
        resp = envelope_success(data={"key": "value"}, tracking_id=tid)
        assert resp.success is True
        assert resp.data == {"key": "value"}
        assert resp.error is None
        assert resp.tracking_id == tid

    def test_error_envelope_structure(self):
        tid = str(uuid4())
        resp = envelope_error(
            code=ErrorCodes.RESOURCE_NOT_FOUND,
            message="Item not found.",
            details={"item_id": "123"},
            tracking_id=tid,
        )
        assert resp.success is False
        assert resp.data is None
        assert resp.error.code == ErrorCodes.RESOURCE_NOT_FOUND
        assert resp.error.message == "Item not found."
        assert resp.error.details == {"item_id": "123"}
        assert resp.tracking_id == tid


# ==============================================================================
# 2. TRACKING ID PROPAGATION & HEADER TESTS
# ==============================================================================

class TestTrackingIdSystem:

    def test_tracking_id_validator_reusable(self):
        valid_uuid = str(uuid4())
        assert validate_or_generate_tracking_id(valid_uuid) == valid_uuid

    def test_tracking_id_validator_malformed_falls_back(self):
        malformed = "not-a-valid-uuid-string"
        result = validate_or_generate_tracking_id(malformed)
        assert result != malformed
        UUID(result)  # Must be a valid UUID

    def test_tracking_id_generated_when_absent(self, client):
        resp = client.get("/api/v1/sample-shell/success")
        assert resp.status_code == 200
        data = resp.json()
        assert "tracking_id" in data
        tracking_id = data["tracking_id"]
        UUID(tracking_id)  # Validate it's a valid UUID
        assert resp.headers.get("X-Tracking-ID") == tracking_id

    def test_custom_tracking_id_propagated(self, client):
        custom_id = str(uuid4())
        resp = client.get(
            "/api/v1/sample-shell/success",
            headers={"X-Tracking-ID": custom_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tracking_id"] == custom_id
        assert resp.headers.get("X-Tracking-ID") == custom_id


# ==============================================================================
# 3. CENTRALIZED EXCEPTION HANDLERS & ERROR ENVELOPES
# ==============================================================================

class TestCentralizedExceptionHandlers:

    def test_401_unauthorized_envelope(self, client):
        resp = client.get("/api/v1/sample-shell/raise-401")
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == ErrorCodes.UNAUTHORIZED
        assert "Invalid credentials" in data["error"]["message"]
        assert "tracking_id" in data
        assert resp.headers.get("X-Tracking-ID") == data["tracking_id"]

    def test_403_forbidden_envelope(self, client):
        resp = client.get("/api/v1/sample-shell/raise-403")
        assert resp.status_code == 403
        data = resp.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == ErrorCodes.FORBIDDEN
        assert "Insufficient privileges" in data["error"]["message"]
        assert "tracking_id" in data

    def test_404_resource_not_found_envelope(self, client):
        resp = client.get("/api/v1/sample-shell/raise-404")
        assert resp.status_code == 404
        data = resp.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == ErrorCodes.RESOURCE_NOT_FOUND
        assert "Resource not found" in data["error"]["message"]
        assert "tracking_id" in data

    def test_409_conflict_envelope(self, client):
        resp = client.get("/api/v1/sample-shell/raise-409")
        assert resp.status_code == 409
        data = resp.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == ErrorCodes.CONFLICT
        assert "conflicting resource" in data["error"]["message"]
        assert "tracking_id" in data

    def test_422_validation_error_envelope(self, client):
        # Sending invalid payload (item_name too short, item_count < 1)
        resp = client.post(
            "/api/v1/sample-shell/validation-test",
            json={"item_name": "x", "item_count": -5},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == ErrorCodes.VALIDATION_ERROR
        assert "Request validation failed" in data["error"]["message"]
        assert "errors" in data["error"]["details"]
        assert len(data["error"]["details"]["errors"]) > 0
        assert "tracking_id" in data

    def test_500_internal_error_no_traceback_leakage(self):
        # Using raise_server_exceptions=False allows TestClient to return 500 response
        unhandled_client = TestClient(app, raise_server_exceptions=False)
        resp = unhandled_client.get("/api/v1/sample-shell/raise-500")
        assert resp.status_code == 500
        data = resp.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == ErrorCodes.INTERNAL_SERVER_ERROR
        # Must not leak internal Python exception text or traceback to the client
        assert "Simulated unhandled internal server error" not in data["error"]["message"]
        assert "Traceback" not in str(data)
        assert "tracking_id" in data
        assert resp.headers.get("X-Tracking-ID") == data["tracking_id"]
