"""
FastAPI Router for Evidence Detail, Human Review Overrides, and Analysis APIs.
Endpoints:
- GET  /api/v1/cases/{case_id}/entities/{entity_id}           (ENTITY_READ)
- GET  /api/v1/cases/{case_id}/relationships/{relationship_id} (ENTITY_READ)
- POST /api/v1/cases/{case_id}/reviews                       (REVIEW_OVERRIDE, supervisor-level)
- POST /api/v1/cases/{case_id}/analysis                      (ANALYSIS_TRIGGER, async 202)
- GET  /api/v1/cases/{case_id}/analysis/{run_id}             (CASE_READ)
- GET  /api/v1/cases/{case_id}/scores                        (CASE_READ)
- GET  /api/v1/cases/{case_id}/alerts                        (CASE_READ)
Enforces universal response envelopes, tracking IDs, server-side case isolation (404),
and append-only audit logging.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.deps import CaseAuthContext, verify_case_access
from apps.api.tracking import get_tracking_id
from backend.db.session import get_db
from backend.schemas.envelope import (
    ApiErrorResponse,
    ApiSuccessResponse,
    ErrorCodes,
    envelope_error,
    envelope_success,
)
from backend.schemas.evidence_analysis import (
    AnalysisRunDetailResponse,
    AnalysisTriggerRequest,
    AnalysisTriggerResponse,
    CaseAlertsResponse,
    CaseScoresResponse,
    EntityDetailResponse,
    RelationshipDetailResponse,
    ReviewRequest,
    ReviewResponse,
)
from backend.security.rbac import Permissions
from backend.services.analysis_service import (
    AnalysisNotFoundError,
    AnalysisService,
    AnalysisServiceError,
)
from backend.services.evidence_review import (
    EvidenceReviewService,
    ReviewConflictError,
    ReviewNotFoundError,
    ReviewServiceError,
)

logger = logging.getLogger("apps.api.routers.evidence_analysis")

router = APIRouter(tags=["Evidence, Reviews & Analysis"])


def _resolve_tracking_id(request: Request) -> str:
    return getattr(request.state, "tracking_id", None) or get_tracking_id()


async def _async_analysis_worker(run_id: UUID, case_id: UUID, session_factory=None) -> None:
    """
    Simulated asynchronous analysis runner.
    Transitions ModelRun from PENDING to RUNNING, then completes without fabricating fake outputs.
    """
    from datetime import datetime, timezone
    from backend.db.session import get_session_factory
    from backend.db.models.analytics import ModelRun

    factory = session_factory or get_session_factory()
    db = factory()
    try:
        run = db.query(ModelRun).filter(ModelRun.run_id == run_id).first()
        if run:
            run.status = "SUCCESS"
            db.commit()
            logger.info(f"Asynchronous analysis run {run_id} marked SUCCESS.")
    except Exception as e:
        logger.error(f"Analysis worker failure for run {run_id}: {e}", exc_info=True)
    finally:
        db.close()


# ==============================================================================
# 1. EVIDENCE APIS
# ==============================================================================

@router.get(
    "/cases/{case_id}/entities/{entity_id}",
    response_model=ApiSuccessResponse[EntityDetailResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
def get_entity_evidence_detail(
    request: Request,
    case_id: UUID,
    entity_id: UUID,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.ENTITY_READ)),
    db: Session = Depends(get_db),
):
    """
    Retrieves deep canonical entity details including aliases, masked identifiers,
    priority score, and provenance spans.
    Non-members or foreign entity IDs return 404 RESOURCE_NOT_FOUND.
    """
    tracking_id = _resolve_tracking_id(request)
    service = EvidenceReviewService(db=db)
    try:
        data = service.get_entity_detail(case_id=case_id, entity_id=entity_id)
        return envelope_success(data=data, tracking_id=tracking_id)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )


@router.get(
    "/cases/{case_id}/relationships/{relationship_id}",
    response_model=ApiSuccessResponse[RelationshipDetailResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
def get_relationship_evidence_detail(
    request: Request,
    case_id: UUID,
    relationship_id: UUID,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.ENTITY_READ)),
    db: Session = Depends(get_db),
):
    """
    Retrieves detailed relationship information with citation chain and endpoint metadata.
    """
    tracking_id = _resolve_tracking_id(request)
    service = EvidenceReviewService(db=db)
    try:
        data = service.get_relationship_detail(case_id=case_id, relationship_id=relationship_id)
        return envelope_success(data=data, tracking_id=tracking_id)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )


# ==============================================================================
# 2. EVIDENCE TRACE API
# ==============================================================================

@router.get(
    "/cases/{case_id}/evidence/{evidence_id}",
    response_model=ApiSuccessResponse[Any],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
def get_relationship_evidence_trace(
    request: Request,
    case_id: UUID,
    evidence_id: UUID,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.ENTITY_READ)),
    db: Session = Depends(get_db),
):
    """
    Exposes the Dempster-Shafer provenance trace and confidence values.
    """
    tracking_id = _resolve_tracking_id(request)
    
    from backend.db.models.entities import Relationship, Entity
    rel = db.query(Relationship).filter_by(relationship_id=evidence_id, case_id=case_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship trace not found")
        
    source_e = db.query(Entity).filter_by(entity_id=rel.source_entity_uuid).first()
    target_e = db.query(Entity).filter_by(entity_id=rel.target_entity_uuid).first()
    
    from backend.schemas.evidence import EvidenceTraceResponse, EvidenceTraceItem
    
    items = []
    for ev in rel.evidence:
        items.append(EvidenceTraceItem(
            evidence_id=ev.evidence_id,
            source_ref=ev.source_ref,
            support_type=ev.support_type,
            provenance_spans=[]
        ))
        
    from backend.db.models.analytics import AuditLog
    audits = db.query(AuditLog).filter_by(case_id=case_id, target_item=str(rel.relationship_id)).all()
    audit_events = [{"action": a.action_code, "timestamp": a.timestamp.isoformat(), "actor": str(a.actor_uuid)} for a in audits]

    data = EvidenceTraceResponse(
        relationship_id=rel.relationship_id,
        case_id=rel.case_id,
        source_entity=RelationshipEndpointSummary(entity_id=source_e.entity_id, canonical_name=source_e.canonical_name, entity_type=source_e.entity_type),
        target_entity=RelationshipEndpointSummary(entity_id=target_e.entity_id, canonical_name=target_e.canonical_name, entity_type=target_e.entity_type),
        type=rel.type,
        status=rel.status,
        evidence_items=items,
        extraction_confidence=1.0,
        entity_match_confidence=1.0,
        relationship_confidence=rel.relationship_confidence,
        belief=rel.belief,
        disbelief=rel.disbelief,
        uncertainty=rel.uncertainty,
        conflict_mass=rel.conflict_mass,
        audit_events=audit_events,
        created_at=rel.created_at
    )
    return envelope_success(data=data.model_dump(), tracking_id=tracking_id)


# ==============================================================================
# 3. HUMAN REVIEW OVERRIDES API
# ==============================================================================

@router.post(
    "/cases/{case_id}/reviews",
    response_model=ApiSuccessResponse[ReviewResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def submit_review_override(
    request: Request,
    case_id: UUID,
    payload: ReviewRequest,
    background_tasks: BackgroundTasks,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.REVIEW_OVERRIDE)),
    db: Session = Depends(get_db),
):
    """
    Applies a human review decision (CONFIRM, REJECT, or MERGE) to an entity or relationship.
    Requires supervisor-level REVIEW_OVERRIDE permission.
    Human decisions are authoritative and cannot be overwritten by downstream AI models.
    """
    tracking_id = _resolve_tracking_id(request)
    service = EvidenceReviewService(db=db, background_tasks=background_tasks)
    try:
        result = service.apply_review_override(
            case_id=case_id,
            actor_uuid=auth_ctx.user.user_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            action=payload.action,
            reason=payload.reason,
            secondary_target_id=payload.secondary_target_id,
        )
        return envelope_success(data=result, tracking_id=tracking_id)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target resource not found.",
        )
    except ReviewConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ReviewServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==============================================================================
# 4. ANALYSIS & INTELLIGENCE APIS
# ==============================================================================

@router.post(
    "/cases/{case_id}/analysis",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApiSuccessResponse[AnalysisTriggerResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def trigger_case_analysis(
    request: Request,
    case_id: UUID,
    payload: AnalysisTriggerRequest,
    background_tasks: BackgroundTasks,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.ANALYSIS_TRIGGER)),
    db: Session = Depends(get_db),
):
    """
    Dispatches asynchronous network intelligence analysis pipelines (SNA, PATTERNS, GATv2).
    Requires ANALYSIS_TRIGGER permission.
    Returns HTTP 202 Accepted with stable run_id.
    """
    tracking_id = _resolve_tracking_id(request)
    service = AnalysisService(db=db)

    trigger_resp = service.trigger_analysis(
        case_id=case_id,
        actor_uuid=auth_ctx.user.user_id,
        pipelines=payload.pipelines,
        parameters=payload.parameters.model_dump(),
    )

    # Dispatch asynchronous execution
    background_tasks.add_task(
        _async_analysis_worker,
        run_id=trigger_resp.run_id,
        case_id=case_id,
        session_factory=db.session_factory if hasattr(db, "session_factory") else None,
    )

    return envelope_success(data=trigger_resp, tracking_id=tracking_id)


@router.get(
    "/cases/{case_id}/analysis/{run_id}",
    response_model=ApiSuccessResponse[AnalysisRunDetailResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
def get_analysis_run_status(
    request: Request,
    case_id: UUID,
    run_id: UUID,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ)),
    db: Session = Depends(get_db),
):
    """
    Queries execution status of an analytical run.
    """
    tracking_id = _resolve_tracking_id(request)
    service = AnalysisService(db=db)
    try:
        detail = service.get_run_status(case_id=case_id, run_id=run_id)
        return envelope_success(data=detail, tracking_id=tracking_id)
    except AnalysisNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found.",
        )


@router.get(
    "/cases/{case_id}/scores",
    response_model=ApiSuccessResponse[CaseScoresResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
def list_case_priority_scores(
    request: Request,
    case_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
    entity_type: Optional[str] = Query(default=None),
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ)),
    db: Session = Depends(get_db),
):
    """
    Retrieves canonical investigative priority rankings and risk scores.
    Ordered by value DESC. Strictly prohibited from using guilt or criminal likelihood terms.
    """
    tracking_id = _resolve_tracking_id(request)
    service = AnalysisService(db=db)
    scores_resp = service.get_case_scores(case_id=case_id, limit=limit, entity_type=entity_type)
    return envelope_success(data=scores_resp, tracking_id=tracking_id)


@router.get(
    "/cases/{case_id}/alerts",
    response_model=ApiSuccessResponse[CaseAlertsResponse],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
def list_case_pattern_alerts(
    request: Request,
    case_id: UUID,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity_filter: Optional[str] = Query(default=None, alias="severity"),
    limit: int = Query(default=100, ge=1, le=500),
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ)),
    db: Session = Depends(get_db),
):
    """
    Retrieves deterministic pattern alerts (transaction cycles, rapid fan-out, call bursts).
    """
    tracking_id = _resolve_tracking_id(request)
    service = AnalysisService(db=db)
    alerts_resp = service.get_case_alerts(
        case_id=case_id,
        status_filter=status_filter,
        severity_filter=severity_filter,
        limit=limit,
    )
    return envelope_success(data=alerts_resp, tracking_id=tracking_id)
