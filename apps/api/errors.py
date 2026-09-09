"""
Centralized FastAPI exception handlers.
Translates all application exceptions into canonical JSON error envelopes.
Strictly enforces:
{
  "success": false,
  "data": null,
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  },
  "tracking_id": "uuid"
}
"""

import logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from backend.schemas.envelope import ErrorCodes, envelope_error
from apps.api.tracking import get_tracking_id

logger = logging.getLogger("apps.api.errors")

STATUS_TO_ERROR_CODE: Dict[int, str] = {
    400: ErrorCodes.VALIDATION_ERROR,
    401: ErrorCodes.UNAUTHORIZED,
    403: ErrorCodes.FORBIDDEN,
    404: ErrorCodes.RESOURCE_NOT_FOUND,
    409: ErrorCodes.CONFLICT,
    413: ErrorCodes.VALIDATION_ERROR,
    422: ErrorCodes.VALIDATION_ERROR,
    500: ErrorCodes.INTERNAL_SERVER_ERROR,
    503: ErrorCodes.SERVICE_UNAVAILABLE,
}


def _resolve_tracking_id(request: Request) -> str:
    """Safely extracts tracking_id from request state or fallback."""
    tracking_id = getattr(request.state, "tracking_id", None)
    return tracking_id or get_tracking_id()


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Standardizes HTTPExceptions into canonical error envelopes.
    Preserves 401, 403, 404, 409 status codes and custom headers.
    """
    tracking_id = _resolve_tracking_id(request)
    code = STATUS_TO_ERROR_CODE.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "An error occurred."
    details = exc.detail if isinstance(exc.detail, dict) else {}

    error_body = envelope_error(
        code=code,
        message=message,
        details=details,
        tracking_id=tracking_id,
    ).model_dump()
    # Provide backward-compatible detail field
    error_body["detail"] = message

    headers = dict(exc.headers) if exc.headers else {}
    headers["X-Tracking-ID"] = tracking_id

    return JSONResponse(
        status_code=exc.status_code,
        content=error_body,
        headers=headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Standardizes FastAPI request validation errors into 422 VALIDATION_ERROR envelopes.
    Formats field-level errors safely without exposing server internals.
    """
    tracking_id = _resolve_tracking_id(request)
    field_errors = []
    for err in exc.errors():
        field_errors.append({
            "loc": [str(loc) for loc in err.get("loc", [])],
            "msg": err.get("msg", "Invalid value"),
            "type": err.get("type", "validation_error"),
        })

    message = "Request validation failed."
    error_body = envelope_error(
        code=ErrorCodes.VALIDATION_ERROR,
        message=message,
        details={"errors": field_errors},
        tracking_id=tracking_id,
    ).model_dump()
    error_body["detail"] = message

    return JSONResponse(
        status_code=422,
        content=error_body,
        headers={"X-Tracking-ID": tracking_id},
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Translates SQLAlchemy database integrity errors (e.g. uniqueness violations)
    into 409 CONFLICT envelopes without exposing raw database tables or queries.
    """
    tracking_id = _resolve_tracking_id(request)
    logger.warning(f"Database integrity conflict: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}")

    message = "A resource conflict or duplicate record was detected."
    error_body = envelope_error(
        code=ErrorCodes.CONFLICT,
        message=message,
        details={},
        tracking_id=tracking_id,
    ).model_dump()
    error_body["detail"] = message

    return JSONResponse(
        status_code=409,
        content=error_body,
        headers={"X-Tracking-ID": tracking_id},
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all unexpected internal server errors, logs tracebacks server-side,
    and returns a clean 500 INTERNAL_SERVER_ERROR envelope.
    Never leaks tracebacks, SQL statements, or filesystem paths to clients.
    """
    tracking_id = _resolve_tracking_id(request)
    logger.error(f"Unhandled exception [tracking_id={tracking_id}]: {str(exc)}", exc_info=True)

    message = "An unexpected internal server error occurred."
    error_body = envelope_error(
        code=ErrorCodes.INTERNAL_SERVER_ERROR,
        message=message,
        details={},
        tracking_id=tracking_id,
    ).model_dump()
    error_body["detail"] = message

    return JSONResponse(
        status_code=500,
        content=error_body,
        headers={"X-Tracking-ID": tracking_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers the centralized exception handlers on the FastAPI application."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)
