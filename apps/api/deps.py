"""
FastAPI Security Dependencies for Authentication, RBAC, and Case Isolation.
Conforms strictly to 07_AUTH_SECURITY.md and 04_API_SPEC.md.
"""

from typing import Callable, List, Optional, Set
from uuid import UUID
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.ingestion import Document
from backend.security.audit import SecurityAuditAction, record_security_event
from backend.security.rbac import (
    Permissions,
    SystemRoles,
    get_permissions_for_roles,
    has_permission,
)
from backend.security.tokens import (
    TokenClaimsError,
    TokenExpiredError,
    TokenSecurityError,
    TokenTamperedError,
    decode_access_token,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


@dataclass
class CaseAuthContext:
    """Authorization context returned upon successful case-level access verification."""
    case_id: UUID
    user: User
    role_in_case: str
    permissions: Set[str]


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the Bearer JWT,
    resolves the user from PostgreSQL, and ensures the account is ACTIVE.
    Raises 401 Unauthorized for missing, expired, or invalid tokens.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except (TokenTamperedError, TokenClaimsError, TokenSecurityError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id_str = payload.get("sub")
    try:
        user_uuid = UUID(user_id_str)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = db.query(User).filter(User.user_id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or suspended.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_user_roles(user: User, db: Session) -> List[str]:
    """Retrieves all global role names assigned to the user from the database."""
    roles = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.role_id)
        .filter(UserRole.user_id == user.user_id)
        .all()
    )
    return [r[0] for r in roles]


def require_permission(permission_code: str) -> Callable:
    """
    Dependency factory to enforce global system permissions.
    If the user lacks the permission, records PERMISSION_DENIED and raises 403 Forbidden.
    """
    def _dependency(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        user_roles = get_user_roles(user, db)
        if not has_permission(user_roles, permission_code):
            record_security_event(
                db=db,
                action_code=SecurityAuditAction.PERMISSION_DENIED,
                actor_uuid=user.user_id,
                target_item=permission_code,
                outcome="DENIED",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges for action '{permission_code}'.",
            )
        return user

    return _dependency


class CaseAccessChecker:
    """
    FastAPI dependency enforcing server-side case isolation on {case_id} path parameters.
    INVARIANT 2: If user is not a member of case_id in case_members,
    strictly returns 404 Not Found (NEVER 403) to prevent case enumeration,
    and logs CASE_ACCESS_DENIED.
    If user is a member but lacks required_permission, returns 403 Forbidden
    and logs PERMISSION_DENIED.
    """
    def __init__(self, required_permission: Optional[str] = None):
        self.required_permission = required_permission

    def __call__(
        self,
        case_id: UUID,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> CaseAuthContext:
        # 1. Query case_members filtering on BOTH case_id and current user_id
        membership = (
            db.query(CaseMember)
            .filter(
                CaseMember.case_id == case_id,
                CaseMember.user_id == user.user_id,
            )
            .first()
        )

        # 2. Non-member: Return 404 Not Found and audit CASE_ACCESS_DENIED
        if not membership:
            record_security_event(
                db=db,
                action_code=SecurityAuditAction.CASE_ACCESS_DENIED,
                actor_uuid=user.user_id,
                case_id=case_id,
                target_item="CASE_ACCESS",
                outcome="DENIED",
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        # 3. Member: Resolve permissions (case role + global roles)
        roles_to_check = [membership.role_in_case]
        roles_to_check.extend(get_user_roles(user, db))
        granted_permissions = get_permissions_for_roles(roles_to_check)

        # 4. Permission check
        if self.required_permission and self.required_permission not in granted_permissions:
            record_security_event(
                db=db,
                action_code=SecurityAuditAction.PERMISSION_DENIED,
                actor_uuid=user.user_id,
                case_id=case_id,
                target_item=self.required_permission,
                outcome="DENIED",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges for action '{self.required_permission}'.",
            )

        return CaseAuthContext(
            case_id=case_id,
            user=user,
            role_in_case=membership.role_in_case,
            permissions=granted_permissions,
        )


def verify_case_access(required_permission: Optional[str] = None) -> CaseAccessChecker:
    """Dependency factory returning a CaseAccessChecker."""
    return CaseAccessChecker(required_permission=required_permission)


class DocumentAccessChecker:
    """
    Dependency to protect direct-ID document endpoints from IDOR cross-case leakage.
    If the document does not exist or user is not a member of its case, returns 404 Not Found.
    """
    def __init__(self, required_permission: Optional[str] = None):
        self.required_permission = required_permission

    def __call__(
        self,
        document_id: UUID,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Document:
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        # Verify case membership on the document's case
        membership = (
            db.query(CaseMember)
            .filter(
                CaseMember.case_id == doc.case_id,
                CaseMember.user_id == user.user_id,
            )
            .first()
        )

        if not membership:
            record_security_event(
                db=db,
                action_code=SecurityAuditAction.CASE_ACCESS_DENIED,
                actor_uuid=user.user_id,
                case_id=doc.case_id,
                target_item=f"DOCUMENT:{document_id}",
                outcome="DENIED",
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        if self.required_permission:
            roles_to_check = [membership.role_in_case]
            roles_to_check.extend(get_user_roles(user, db))
            granted = get_permissions_for_roles(roles_to_check)
            if self.required_permission not in granted:
                record_security_event(
                    db=db,
                    action_code=SecurityAuditAction.PERMISSION_DENIED,
                    actor_uuid=user.user_id,
                    case_id=doc.case_id,
                    target_item=f"DOCUMENT:{document_id}:{self.required_permission}",
                    outcome="DENIED",
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: Insufficient privileges for action '{self.required_permission}'.",
                )

        return doc


def verify_document_access(required_permission: Optional[str] = None) -> DocumentAccessChecker:
    """Dependency factory returning a DocumentAccessChecker."""
    return DocumentAccessChecker(required_permission=required_permission)
