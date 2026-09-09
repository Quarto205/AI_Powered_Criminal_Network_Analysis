"""
Case Management service orchestrating transactional persistence and audit logging.
Conforms strictly to 04_API_SPEC.md, 02_DATABASE_SCHEMA.md, and Sections 21-44 of contract.
"""

from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.models.identity import Case, CaseMember, User
from backend.db.models.ingestion import Document
from backend.db.models.entities import Entity
from backend.schemas.cases import (
    CaseCreateRequest,
    CaseDetailResponse,
    CaseListItem,
    CaseMemberAddRequest,
    CaseMemberItem,
    CaseUpdateRequest,
)
from backend.security.audit import SecurityAuditAction, record_security_event

VALID_CASE_STATUSES = {"ACTIVE", "ARCHIVED", "CLOSED", "PENDING_REVIEW"}
VALID_CASE_ROLES = {"INVESTIGATOR", "ANALYST", "SUPERVISOR"}


class CaseService:
    """Service layer encapsulating case management business rules."""

    @staticmethod
    def create_case(db: Session, req: CaseCreateRequest, creator: User) -> Case:
        """
        Creates a new investigation case, assigns the creator as SUPERVISOR,
        and audits CASE_CREATE in a single atomic transaction.
        """
        code_clean = req.case_code.strip()

        # Check case_code uniqueness before insert for clear 409 conflict
        existing = db.query(Case).filter(Case.case_code == code_clean).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Case with code '{code_clean}' already exists.",
            )

        case_id = uuid4()
        new_case = Case(
            case_id=case_id,
            case_code=code_clean,
            title=req.title.strip(),
            description=req.description.strip() if req.description else None,
            status="ACTIVE",
            jurisdiction=req.jurisdiction.strip(),
            created_by=creator.user_id,
        )
        db.add(new_case)
        db.flush()

        # Creator automatically becomes a member with SUPERVISOR role
        creator_membership = CaseMember(
            case_member_id=uuid4(),
            case_id=case_id,
            user_id=creator.user_id,
            role_in_case="SUPERVISOR",
        )
        db.add(creator_membership)
        db.flush()

        # Record mutation audit event
        record_security_event(
            db=db,
            action_code="CASE_CREATE",
            actor_uuid=creator.user_id,
            case_id=case_id,
            target_item=code_clean,
            outcome="SUCCESS",
        )

        db.commit()
        db.refresh(new_case)
        return new_case

    @staticmethod
    def list_cases_for_user(
        db: Session,
        user_id: UUID,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CaseListItem], int]:
        """
        Returns authorized cases for the user via DB join with case_members.
        Never fetches unauthorized cases into Python memory.
        """
        # Clamp pagination
        limit_clamped = max(1, min(limit, 100))
        offset_clamped = max(0, offset)

        query = (
            db.query(Case, CaseMember.role_in_case)
            .join(CaseMember, CaseMember.case_id == Case.case_id)
            .filter(CaseMember.user_id == user_id)
        )

        if status_filter:
            status_clean = status_filter.strip().upper()
            query = query.filter(Case.status == status_clean)

        total_count = query.count()
        rows = (
            query.order_by(Case.created_at.desc())
            .offset(offset_clamped)
            .limit(limit_clamped)
            .all()
        )

        items = [
            CaseListItem(
                case_id=c.case_id,
                case_code=c.case_code,
                title=c.title,
                status=c.status,
                jurisdiction=c.jurisdiction,
                member_role=role_in_case,
                created_at=c.created_at,
            )
            for c, role_in_case in rows
        ]

        return items, total_count

    @staticmethod
    def get_case_details(db: Session, case_id: UUID) -> CaseDetailResponse:
        """
        Retrieves case metadata plus aggregate document and entity counts.
        """
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        # Efficient aggregate counts
        doc_count = (
            db.query(func.count(Document.document_id))
            .filter(Document.case_id == case_id)
            .scalar() or 0
        )

        entity_count = (
            db.query(func.count(Entity.entity_id))
            .filter(Entity.case_id == case_id)
            .scalar() or 0
        )

        return CaseDetailResponse(
            case_id=case.case_id,
            case_code=case.case_code,
            title=case.title,
            description=case.description,
            status=case.status,
            jurisdiction=case.jurisdiction,
            created_by=case.created_by,
            created_at=case.created_at,
            document_count=doc_count,
            entity_count=entity_count,
        )

    @staticmethod
    def update_case(
        db: Session,
        case_id: UUID,
        patch: CaseUpdateRequest,
        actor: User,
    ) -> CaseDetailResponse:
        """
        Applies partial updates to a case, audits CASE_UPDATE, and commits atomically.
        """
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        if patch.title is not None:
            case.title = patch.title.strip()
        if patch.description is not None:
            case.description = patch.description.strip()
        if patch.jurisdiction is not None:
            case.jurisdiction = patch.jurisdiction.strip()
        if patch.status is not None:
            clean_status = patch.status.strip().upper()
            if clean_status not in VALID_CASE_STATUSES:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid status '{patch.status}'. Allowed: {', '.join(sorted(VALID_CASE_STATUSES))}",
                )
            case.status = clean_status

        # Audit mutation
        record_security_event(
            db=db,
            action_code="CASE_UPDATE",
            actor_uuid=actor.user_id,
            case_id=case_id,
            target_item=case.case_code,
            outcome="SUCCESS",
        )

        db.commit()
        db.refresh(case)
        return CaseService.get_case_details(db, case_id)

    @staticmethod
    def assign_case_member(
        db: Session,
        case_id: UUID,
        req: CaseMemberAddRequest,
        actor: User,
    ) -> CaseMemberItem:
        """
        Adds or updates a user's membership and role in a case. Audits CASE_MEMBER_ADD.
        """
        role_clean = req.role_in_case.strip().upper()
        if role_clean not in VALID_CASE_ROLES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid case role '{req.role_in_case}'. Allowed: {', '.join(sorted(VALID_CASE_ROLES))}",
            )

        target_user = db.query(User).filter(User.user_id == req.user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found.",
            )

        # Check existing membership
        member = (
            db.query(CaseMember)
            .filter(
                CaseMember.case_id == case_id,
                CaseMember.user_id == req.user_id,
            )
            .first()
        )

        if member:
            member.role_in_case = role_clean
        else:
            member = CaseMember(
                case_member_id=uuid4(),
                case_id=case_id,
                user_id=req.user_id,
                role_in_case=role_clean,
            )
            db.add(member)

        # Audit mutation
        record_security_event(
            db=db,
            action_code="CASE_MEMBER_ADD",
            actor_uuid=actor.user_id,
            case_id=case_id,
            target_item=f"USER:{req.user_id}:{role_clean}",
            outcome="SUCCESS",
        )

        db.commit()

        return CaseMemberItem(
            user_id=target_user.user_id,
            username=target_user.username,
            email=target_user.email,
            role_in_case=role_clean,
        )

    @staticmethod
    def list_case_members(db: Session, case_id: UUID) -> List[CaseMemberItem]:
        """
        Returns sanitized user profile and role info for all members of a case.
        Never exposes password hashes or authentication tokens.
        """
        rows = (
            db.query(User.user_id, User.username, User.email, CaseMember.role_in_case)
            .join(CaseMember, CaseMember.user_id == User.user_id)
            .filter(CaseMember.case_id == case_id)
            .order_by(User.username.asc())
            .all()
        )

        return [
            CaseMemberItem(
                user_id=uid,
                username=uname,
                email=uemail,
                role_in_case=role,
            )
            for uid, uname, uemail, role in rows
        ]
