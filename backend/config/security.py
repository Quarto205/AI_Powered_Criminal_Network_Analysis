"""
Security configuration settings for SIH26189.
Supports environment-based configuration for JWT signing and token lifetimes.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class SecuritySettings(BaseModel):
    """
    Security and authentication settings.
    Never hardcodes secret keys or credentials.
    """
    jwt_secret_key: str = Field(
        ...,
        description="HMAC SHA-256 secret key for signing JWTs",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Cryptographic algorithm for JWT signing",
    )
    jwt_access_token_expire_seconds: int = Field(
        default=28800,  # 8 hours = 28,800 seconds
        description="Access token validity duration in seconds",
    )

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        """Loads security settings from environment variables."""
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is missing but required.")

        algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        expire_seconds = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_SECONDS", "28800"))

        return cls(
            jwt_secret_key=secret_key,
            jwt_algorithm=algorithm,
            jwt_access_token_expire_seconds=expire_seconds,
        )


_security_settings: Optional[SecuritySettings] = None


def get_security_settings() -> SecuritySettings:
    """Singleton getter for security settings."""
    global _security_settings
    if _security_settings is None:
        _security_settings = SecuritySettings.from_env()
    return _security_settings


def set_security_settings(settings: Optional[SecuritySettings]) -> None:
    """Setter to override security settings (primarily for testing)."""
    global _security_settings
    _security_settings = settings
