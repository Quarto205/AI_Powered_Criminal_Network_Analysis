"""
Password hashing and verification using Argon2id.
Enforces salted, computationally secure password storage and constant-time verification.
"""

import logging
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError

# Alias for backward compatibility
InvalidHashError = InvalidHash

logger = logging.getLogger("backend.security.password")

# Initialize Argon2id hasher (type=Type.ID is Argon2id, the current standard)
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)

# Pre-computed dummy hash to mitigate username enumeration timing attacks
_DUMMY_HASH = _hasher.hash("dummy_constant_time_password_for_timing_mitigation")


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id with a cryptographically secure random salt.
    Never stores or logs plaintext passwords.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a plaintext password against an Argon2id password hash in safe constant time.
    Returns True if match, False otherwise. Never throws on invalid credentials.
    """
    if not password or not password_hash:
        return False

    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during password verification: {type(e).__name__}")
        return False


def dummy_verify() -> None:
    """
    Performs a dummy password verification to equalize timing when a requested username
    does not exist, defeating timing-based username enumeration attacks.
    """
    try:
        _hasher.verify(_DUMMY_HASH, "dummy_attempt")
    except Exception:
        pass
