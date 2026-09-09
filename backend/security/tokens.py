"""
Stateless JWT creation and validation using PyJWT.
Enforces HS256 signature verification, required claims, and 8-hour expiration.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidSignatureError,
    InvalidTokenError,
)

from backend.config.security import get_security_settings


class TokenSecurityError(Exception):
    """Base exception for JWT security violations."""
    pass


class TokenExpiredError(TokenSecurityError):
    """Raised when a JWT has expired past its exp claim."""
    pass


class TokenTamperedError(TokenSecurityError):
    """Raised when a JWT signature verification fails or algorithm confusion is attempted."""
    pass


class TokenClaimsError(TokenSecurityError):
    """Raised when required claims are missing or malformed."""
    pass


REQUIRED_CLAIMS = {"sub", "username", "email", "roles", "iat", "exp", "jti"}


def create_access_token(
    user_id: UUID,
    username: str,
    email: str,
    roles: List[str],
    custom_expire_seconds: Optional[int] = None,
) -> str:
    """
    Generates a cryptographically signed HS256 JWT access token.
    Claims: sub, username, email, roles, iat, exp, jti.
    """
    settings = get_security_settings()
    now = datetime.now(timezone.utc)
    iat = int(now.timestamp())
    expire_seconds = custom_expire_seconds or settings.jwt_access_token_expire_seconds
    exp = iat + expire_seconds
    jti = str(uuid4())

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "email": email,
        "roles": roles,
        "iat": iat,
        "exp": exp,
        "jti": jti,
    }

    token = jwt.encode(
        payload=payload,
        key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Validates and decodes a JWT access token.
    Enforces HS256 algorithm whitelist, signature integrity, expiration, and claim presence.
    """
    if not token:
        raise TokenClaimsError("Access token is missing.")

    settings = get_security_settings()
    allowed_algorithms = [settings.jwt_algorithm]

    try:
        payload = jwt.decode(
            token,
            key=settings.jwt_secret_key,
            algorithms=allowed_algorithms,
            options={"require": ["exp", "iat", "sub"]},
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError("Access token has expired.") from e
    except (InvalidSignatureError, InvalidAlgorithmError) as e:
        raise TokenTamperedError("Access token signature is invalid or tampered.") from e
    except InvalidTokenError as e:
        raise TokenTamperedError(f"Malformed access token: {str(e)}") from e

    # Validate required claims
    missing_claims = REQUIRED_CLAIMS - set(payload.keys())
    if missing_claims:
        raise TokenClaimsError(f"Missing required JWT claims: {', '.join(sorted(missing_claims))}")

    # Validate subject UUID format
    try:
        UUID(payload["sub"])
    except (ValueError, TypeError) as e:
        raise TokenClaimsError("Claim 'sub' must be a valid UUID string.") from e

    # Validate roles list
    if not isinstance(payload.get("roles"), list):
        raise TokenClaimsError("Claim 'roles' must be a list of strings.")

    return payload
