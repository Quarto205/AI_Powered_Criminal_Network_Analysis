"""
FastAPI application entry point for SIH26189.
Configures universal envelope exception handlers, tracking ID middleware,
and the central /api/v1 router.
"""

from fastapi import FastAPI
from apps.api.errors import register_exception_handlers
from apps.api.routers.v1 import v1_router
from apps.api.tracking import TrackingIdMiddleware
from backend.security.redaction import apply_logging_redaction

apply_logging_redaction()

app = FastAPI(
    title="SIH26189 Criminal Network Analysis API",
    description="Investigation Support Decision System API with Server-Side Case Isolation, RBAC, and Universal Envelopes",
    version="1.0.0",
)

# 1. Register Tracking ID correlation middleware
app.add_middleware(TrackingIdMiddleware)

# 2. Register Centralized Exception Handlers for universal error envelopes
register_exception_handlers(app)

# 3. Mount central v1 router (/api/v1)
app.include_router(v1_router)


@app.get("/health")
def health():
    return {"status": "healthy"}
