"""
Canonical API Response and Error Envelopes for SIH26189.
Strictly adheres to 04_API_SPEC.md (Section 4.1) and Section 3 of the task contract:
Every JSON response exposes:
- success: bool
- data: Any | None
- error: ApiErrorDetail | None
- tracking_id: str (UUID-v4)
"""

from typing import Any, Dict, Generic, Optional, TypeVar
from uuid import uuid4
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorCodes:
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFLICT = "CONFLICT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class ApiErrorDetail(BaseModel):
    """Structured error information."""
    code: str = Field(..., description="Canonical error code")
    message: str = Field(..., description="Safe, client-facing explanation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured error context")


class ApiSuccessResponse(BaseModel, Generic[T]):
    """Standardized success response envelope."""
    success: bool = Field(default=True, description="Always true for successful operations")
    data: T = Field(..., description="Primary response payload")
    error: Optional[ApiErrorDetail] = Field(default=None, description="Always null on success")
    tracking_id: str = Field(..., description="Request correlation UUID-v4")


class ApiErrorResponse(BaseModel):
    """Standardized error response envelope."""
    success: bool = Field(default=False, description="Always false for error responses")
    data: Optional[Any] = Field(default=None, description="Always null on error")
    error: ApiErrorDetail = Field(..., description="Structured error details")
    tracking_id: str = Field(..., description="Request correlation UUID-v4")


def envelope_success(data: T, tracking_id: Optional[str] = None) -> ApiSuccessResponse[T]:
    """Helper to construct a typed success envelope."""
    return ApiSuccessResponse[T](
        success=True,
        data=data,
        error=None,
        tracking_id=tracking_id or str(uuid4()),
    )


def envelope_error(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    tracking_id: Optional[str] = None,
) -> ApiErrorResponse:
    """Helper to construct an error envelope."""
    return ApiErrorResponse(
        success=False,
        data=None,
        error=ApiErrorDetail(
            code=code,
            message=message,
            details=details or {},
        ),
        tracking_id=tracking_id or str(uuid4()),
    )
