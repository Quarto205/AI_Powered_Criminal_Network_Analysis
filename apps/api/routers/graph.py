"""
Graph API Endpoints for SIH26189.
Mounted under /api/v1/cases/{case_id}/graph.
Includes:
- GET  /api/v1/cases/{case_id}/graph         (GRAPH_READ permission)
- POST /api/v1/cases/{case_id}/graph/rebuild (REVIEW_OVERRIDE permission, supervisor-level)
Enforces universal response envelopes, tracking IDs, server-side case isolation,
and safe Neo4j outage handling.
"""

import asyncio
import logging
from typing import Any, List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.deps import CaseAuthContext, get_current_user, verify_case_access
from apps.api.tracking import get_tracking_id
from backend.db.models.identity import User
from backend.db.session import get_db
from backend.graph.connection import get_graph_manager
from backend.schemas.envelope import (
    ApiErrorResponse,
    ApiSuccessResponse,
    ErrorCodes,
    envelope_error,
    envelope_success,
)
from backend.schemas.graph import CaseGraphResponse, GraphRebuildResponse
from backend.security.audit import SecurityAuditAction, record_security_event
from backend.security.rbac import Permissions
from backend.services.graph_projection import GraphProjectionError, GraphProjectionService
from backend.services.graph_query import GraphQueryError, GraphQueryService

logger = logging.getLogger("apps.api.routers.graph")

router = APIRouter(tags=["Graph"])


def _resolve_tracking_id(request: Request) -> str:
    return getattr(request.state, "tracking_id", None) or get_tracking_id()


async def _async_rebuild_worker(
    case_id: UUID,
    actor_uuid: UUID,
    session_factory: Optional[Any] = None,
) -> None:
    """
    Background worker task executing full case graph rebuild.
    Isolated from HTTP request to prevent blocking API responses.
    """
    from backend.db.session import get_session_factory
    factory = session_factory or get_session_factory()
    db = factory()
    try:
        service = GraphProjectionService(db=db)
        result = service.rebuild_case_graph(case_id)
        logger.info(f"Background graph rebuild succeeded for case {case_id}: {result}")
        record_security_event(
            db=db,
            action_code=SecurityAuditAction.GRAPH_REBUILD,
            actor_uuid=actor_uuid,
            case_id=case_id,
            target_item=f"SNAPSHOT:{result.get('snapshot_id')}",
            outcome="SUCCESS",
        )
    except Exception as e:
        logger.error(f"Background graph rebuild failed for case {case_id}: {type(e).__name__}", exc_info=True)
        record_security_event(
            db=db,
            action_code=SecurityAuditAction.GRAPH_REBUILD,
            actor_uuid=actor_uuid,
            case_id=case_id,
            target_item=f"CASE:{case_id}",
            outcome="FAILED",
        )
    finally:
        db.close()


@router.get(
    "/cases/{case_id}/graph",
    response_model=ApiSuccessResponse[CaseGraphResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
        503: {"model": ApiErrorResponse},
    },
)
def get_case_graph(
    request: Request,
    case_id: UUID,
    depth: int = Query(default=2, ge=1, le=3, description="Traversal hop depth (1 to 3)"),
    focus_entity_id: Optional[UUID] = Query(default=None, description="Center graph on specific entity"),
    entity_types: Optional[List[str]] = Query(default=None, description="Filter by entity types"),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum confidence score"),
    include_predicted: bool = Query(default=True, description="Whether to include AI predicted links"),
    limit: int = Query(default=300, gt=0, le=1000, description="Maximum nodes to return"),
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.GRAPH_READ)),
    db: Session = Depends(get_db),
):
    """
    Retrieves the analytical graph projection for a case in Cytoscape.js format.
    Requires case membership and GRAPH_READ permission.
    Non-members receive 404 RESOURCE_NOT_FOUND to prevent case enumeration.
    """
    tracking_id = _resolve_tracking_id(request)

    # Check Neo4j availability before proceeding
    graph_manager = get_graph_manager()
    if not graph_manager.is_healthy():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph analytical database is currently unavailable. Source evidence and case records remain intact.",
        )

    try:
        service = GraphQueryService(db=db, graph_manager=graph_manager)
        response_data = service.get_case_graph(
            case_id=case_id,
            depth=depth,
            focus_entity_id=focus_entity_id,
            entity_types=entity_types,
            min_confidence=min_confidence,
            include_predicted=include_predicted,
            limit=limit,
        )
        return envelope_success(data=response_data, tracking_id=tracking_id)
    except GraphQueryError as e:
        logger.error(f"Graph query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while executing the graph query.",
        )


@router.post(
    "/cases/{case_id}/graph/rebuild",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApiSuccessResponse[GraphRebuildResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        503: {"model": ApiErrorResponse},
    },
)
def rebuild_case_graph(
    request: Request,
    case_id: UUID,
    background_tasks: BackgroundTasks,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.REVIEW_OVERRIDE)),
    db: Session = Depends(get_db),
):
    """
    Triggers an asynchronous, non-blocking rebuild of the case graph projection from PostgreSQL.
    Requires supervisor-level REVIEW_OVERRIDE permission.
    Immediately returns HTTP 202 Accepted with a stable job_id.
    """
    tracking_id = _resolve_tracking_id(request)

    # Verify Neo4j connectivity before dispatching rebuild job
    graph_manager = get_graph_manager()
    if not graph_manager.is_healthy():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot trigger graph rebuild: Neo4j analytical database is currently unavailable.",
        )

    job_id = uuid4()

    # Record immediate audit event for rebuild dispatch
    record_security_event(
        db=db,
        action_code=SecurityAuditAction.GRAPH_REBUILD,
        actor_uuid=auth_ctx.user.user_id,
        case_id=case_id,
        target_item=f"JOB:{job_id}",
        outcome="DISPATCHED",
    )

    # Dispatch asynchronous background task
    background_tasks.add_task(
        _async_rebuild_worker,
        case_id=case_id,
        actor_uuid=auth_ctx.user.user_id,
        session_factory=db.session_factory if hasattr(db, "session_factory") else None,
    )

    receipt = GraphRebuildResponse(
        case_id=case_id,
        job_id=job_id,
        status="REBUILDING",
    )
    return envelope_success(data=receipt, tracking_id=tracking_id)
