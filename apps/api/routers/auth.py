"""
FastAPI Authentication Router for SIH26189.
Conforms strictly to 07_AUTH_SECURITY.md and 04_API_SPEC.md.
"""

from typing import Any, List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.config.security import get_security_settings
from backend.db.models.identity import Role, User, UserRole
from backend.db.session import get_db
from backend.security.audit import SecurityAuditAction, record_security_event
from backend.security.password import dummy_verify, verify_password
from backend.security.tokens import create_access_token
from apps.api.deps import get_current_user, get_user_roles

router = APIRouter(prefix="/auth", tags=["auth"])



class LoginRequest(BaseModel):
    username: str = Field(..., description="User's login username or email")
    password: str = Field(..., description="Plaintext password")


class UserProfileResponse(BaseModel):
    user_id: UUID
    username: str
    email: str
    roles: List[str]


class LoginDataResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse


class LoginResponseEnvelope(BaseModel):
    success: bool = True
    data: LoginDataResponse
    error: Optional[Any] = None
    tracking_id: str
    request_id: Optional[str] = None


class CurrentUserResponseEnvelope(BaseModel):
    success: bool = True
    data: UserProfileResponse
    error: Optional[Any] = None
    tracking_id: str
    request_id: Optional[str] = None


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponseEnvelope,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates an investigator or analyst using username/email and password.
    Returns HS256 JWT access token valid for 8 hours (28,800s).
    Audits AUTH_LOGIN_SUCCESS and AUTH_LOGIN_FAILURE.
    Mitigates user enumeration and timing attacks.
    """
    from apps.api.tracking import get_tracking_id
    tracking_id = get_tracking_id()

    username_clean = payload.username.strip()

    # Query user by username or email
    user = (
        db.query(User)
        .filter(
            (User.username == username_clean) | (User.email == username_clean)
        )
        .first()
    )

    if not user:
        # Mitigate username enumeration timing attacks with dummy verification
        dummy_verify()
        record_security_event(
            db=db,
            action_code=SecurityAuditAction.AUTH_LOGIN_FAILURE,
            actor_uuid=None,  # No valid user UUID
            target_item=username_clean,
            outcome="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password hash
    if not verify_password(payload.password, user.password_hash):
        record_security_event(
            db=db,
            action_code=SecurityAuditAction.AUTH_LOGIN_FAILURE,
            actor_uuid=user.user_id,
            target_item=username_clean,
            outcome="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account status
    if user.account_status != "ACTIVE":
        record_security_event(
            db=db,
            action_code=SecurityAuditAction.AUTH_LOGIN_FAILURE,
            actor_uuid=user.user_id,
            target_item=f"{username_clean}:STATUS_{user.account_status}",
            outcome="FAILURE",
        )
        # Generic error message to prevent account status enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retrieve assigned roles
    roles = get_user_roles(user, db)

    # Construct claims and create token
    settings = get_security_settings()
    access_token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=roles,
        custom_expire_seconds=settings.jwt_access_token_expire_seconds,
    )

    # Record successful login event
    record_security_event(
        db=db,
        action_code=SecurityAuditAction.AUTH_LOGIN_SUCCESS,
        actor_uuid=user.user_id,
        target_item=username_clean,
        outcome="SUCCESS",
    )

    return LoginResponseEnvelope(
        success=True,
        data=LoginDataResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_seconds,
            user=UserProfileResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                roles=roles,
            ),
        ),
        request_id=tracking_id,
        tracking_id=tracking_id,
        error=None,
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=CurrentUserResponseEnvelope,
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns profile and role claims for the currently authenticated user.
    """
    from apps.api.tracking import get_tracking_id
    tracking_id = get_tracking_id()
    roles = get_user_roles(current_user, db)
    return CurrentUserResponseEnvelope(
        success=True,
        data=UserProfileResponse(
            user_id=current_user.user_id,
            username=current_user.username,
            email=current_user.email,
            roles=roles,
        ),
        tracking_id=tracking_id,
        request_id=tracking_id,
        error=None,
    )
