"""
FastAPI application entry point for SIH26189.
Configures universal envelope exception handlers, tracking ID middleware,
and the central /api/v1 router.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# 2. Register CORS Middleware with configurable allowed origins (SEC-001)
allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:3000"
)
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register Centralized Exception Handlers for universal error envelopes
register_exception_handlers(app)

# 4. Mount central v1 router (/api/v1)
app.include_router(v1_router)


@app.get("/health")
def health():
    return {"status": "healthy"}
