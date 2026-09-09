"""
Central API v1 router for SIH26189.
All endpoints mounted here are available under /api/v1 prefix.
"""

from fastapi import APIRouter
from apps.api.routers.auth import router as auth_router
from apps.api.routers.cases import router as cases_router
from apps.api.routers.documents import router as documents_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(cases_router)
v1_router.include_router(documents_router)
