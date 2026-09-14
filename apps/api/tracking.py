"""
Request-scoped UUID-v4 tracking ID management and propagation middleware.
Ensures every request has a validated correlation ID available in context and headers.
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID, uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for accessing the current tracking ID anywhere in the request lifecycle
current_tracking_id_ctx: ContextVar[Optional[str]] = ContextVar("current_tracking_id", default=None)


def validate_or_generate_tracking_id(incoming_header: Optional[str]) -> str:
    """
    Validates that incoming tracking ID is a valid UUID string.
    If valid, reuses it. If absent or malformed, generates a new UUID-v4.
    """
    if incoming_header:
        cleaned = incoming_header.strip()
        try:
            parsed = UUID(cleaned)
            return str(parsed)
        except (ValueError, TypeError):
            # Malformed header: generate a fresh UUID-v4 safely
            pass
    return str(uuid4())


def get_tracking_id() -> str:
    """
    Returns the current request's tracking ID.
    If called outside of an active HTTP request context, generates a new UUID-v4.
    """
    val = current_tracking_id_ctx.get()
    return val or str(uuid4())


class TrackingIdMiddleware(BaseHTTPMiddleware):
    """
    Starlette/FastAPI middleware that:
    1. Extracts or generates a UUID-v4 tracking ID.
    2. Stores tracking ID in request.state.tracking_id and the context variable.
    3. Attaches 'X-Tracking-ID' header to all outgoing HTTP responses.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("X-Tracking-ID")
        tracking_id = validate_or_generate_tracking_id(incoming)

        # Set request state and context variable
        request.state.tracking_id = tracking_id
        token = current_tracking_id_ctx.set(tracking_id)

        try:
            response: Response = await call_next(request)
            response.headers["X-Tracking-ID"] = tracking_id
            return response
        finally:
            current_tracking_id_ctx.reset(token)
