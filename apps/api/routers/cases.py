"""
FastAPI Case Management Router for SIH26189.
Conforms strictly to 04_API_SPEC.md (Section 4.2), 07_AUTH_SECURITY.md,
and Section 21-42 of the task contract.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.db.models.identity import User
from backend.db.session import get_db
from backend.schemas.cases import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseDetailResponse,
    CaseListResponse,
    CaseMemberAddRequest,
    CaseMemberItem,
    CaseUpdateRequest,
)
from backend.schemas.envelope import ApiSuccessResponse, envelope_success
from backend.security.rbac import Permissions
from backend.services.case_service import CaseService
from apps.api.deps import (
    CaseAuthContext,
    get_current_user,
    require_permission,
    verify_case_access,
)
from apps.api.tracking import get_tracking_id

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiSuccessResponse[CaseCreateResponse],
)
def create_case(
    payload: CaseCreateRequest,
    current_user: User = Depends(require_permission(Permissions.CASE_CREATE)),
    db: Session = Depends(get_db),
):
    """
    Creates a new case, auto-assigns the creator as SUPERVISOR, and records CASE_CREATE.
    Requires CASE_CREATE permission (Supervisor persona).
    """
    case = CaseService.create_case(db=db, req=payload, creator=current_user)
    data = CaseCreateResponse(
        case_id=case.case_id,
        case_code=case.case_code,
        title=case.title,
        status=case.status,
        jurisdiction=case.jurisdiction,
        created_at=case.created_at,
        created_by=case.created_by,
    )
    return envelope_success(data=data, tracking_id=get_tracking_id())


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=ApiSuccessResponse[CaseListResponse],
)
def list_cases(
    status: Optional[str] = Query(None, description="Filter by case status (e.g. ACTIVE, CLOSED)"),
    limit: int = Query(50, ge=1, le=100, description="Page limit (default 50, max 100)"),
    offset: int = Query(0, ge=0, description="Page offset (default 0)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists only cases where the requesting authenticated user holds membership.
    Never exposes cases the user does not belong to.
    """
    items, total = CaseService.list_cases_for_user(
        db=db,
        user_id=current_user.user_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    data = CaseListResponse(
        cases=items,
        total=total,
        limit=limit,
        offset=offset,
    )
    return envelope_success(data=data, tracking_id=get_tracking_id())


@router.get(
    "/{case_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiSuccessResponse[CaseDetailResponse],
)
def get_case(
    case_id: UUID,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ)),
    db: Session = Depends(get_db),
):
    """
    Retrieves full case details including aggregate document and entity counts.
    Returns 404 Not Found if requesting user is not a member of the case.
    """
    details = CaseService.get_case_details(db=db, case_id=case_id)
    return envelope_success(data=details, tracking_id=get_tracking_id())


@router.patch(
    "/{case_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiSuccessResponse[CaseDetailResponse],
)
def update_case(
    case_id: UUID,
    payload: CaseUpdateRequest,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_UPDATE)),
    db: Session = Depends(get_db),
):
    """
    Updates case title, description, jurisdiction, or status.
    Requires case membership and CASE_UPDATE permission. Audits CASE_UPDATE.
    """
    updated = CaseService.update_case(
        db=db,
        case_id=case_id,
        patch=payload,
        actor=auth_ctx.user,
    )
    return envelope_success(data=updated, tracking_id=get_tracking_id())


@router.post(
    "/{case_id}/members",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiSuccessResponse[CaseMemberItem],
)
def assign_member(
    case_id: UUID,
    payload: CaseMemberAddRequest,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_ASSIGN_MEMBER)),
    db: Session = Depends(get_db),
):
    """
    Assigns or updates a member's role within a case.
    Requires case membership and CASE_ASSIGN_MEMBER permission. Audits CASE_MEMBER_ADD.
    """
    member_item = CaseService.assign_case_member(
        db=db,
        case_id=case_id,
        req=payload,
        actor=auth_ctx.user,
    )
    return envelope_success(data=member_item, tracking_id=get_tracking_id())


@router.get(
    "/{case_id}/members",
    status_code=status.HTTP_200_OK,
    response_model=ApiSuccessResponse[List[CaseMemberItem]],
)
def list_members(
    case_id: UUID,
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ)),
    db: Session = Depends(get_db),
):
    """
    Lists all members and their roles within a case.
    Requires case membership and CASE_READ permission.
    """
    members = CaseService.list_case_members(db=db, case_id=case_id)
    return envelope_success(data=members, tracking_id=get_tracking_id())
