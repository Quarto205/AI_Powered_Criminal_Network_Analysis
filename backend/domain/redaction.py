"""
Redaction and defensive data masking utilities for SIH26189.
Ensures no raw PII (phone numbers, account numbers, card numbers)
or secrets (tokens, passwords) are logged into the append-only audit trail.
"""

import re
from typing import Optional

# Regex for JWT tokens (header.payload.signature)
JWT_REGEX = re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")

# Regex for Bearer tokens
BEARER_REGEX = re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.~+/]+=*", re.IGNORECASE)

# Regex for common secret key-values
SECRET_REGEX = re.compile(
    r"(password|secret|token|api[_-]?key|access[_-]?token|auth)\s*[:=]\s*([^\s,;]+)",
    re.IGNORECASE,
)

# Regex for 10 to 12 digit phone numbers (optionally prefixed with country code)
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

# Regex for bank account / card numbers (12 to 16 consecutive digits or separated by spaces/hyphens)
ACCOUNT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{12,18}\b")


def mask_phone_number(match: re.Match) -> str:
    """Masks all but the first 2 and last 3 characters of a phone number."""
    val = match.group(0)
    digits = [c for c in val if c.isdigit()]
    if len(digits) < 7:
        return val
    # Preserve prefix/punctuation structure if possible, or produce standard mask
    prefix = val[:4]
    suffix = val[-3:]
    return f"{prefix}*****{suffix}"


def mask_account_number(match: re.Match) -> str:
    """Masks all but the last 4 digits of an account or card number."""
    val = match.group(0)
    clean = re.sub(r"[-\s]", "", val)
    if len(clean) < 8:
        return val
    suffix = clean[-4:]
    return f"****-****-****-{suffix}"


def redact_sensitive_text(text: Optional[str]) -> Optional[str]:
    """
    Sanitizes text by redacting auth tokens, passwords, and masking PII.
    Safe for storing in audit_logs, error messages, and external responses.
    """
    if not text:
        return text

    sanitized = text

    # 1. Redact JWTs
    sanitized = JWT_REGEX.sub("[REDACTED_JWT]", sanitized)

    # 2. Redact Bearer tokens
    sanitized = BEARER_REGEX.sub("Bearer [REDACTED_TOKEN]", sanitized)

    # 3. Redact explicit secrets
    sanitized = SECRET_REGEX.sub(r"\1=[REDACTED]", sanitized)

    # 4. Mask credit card / bank account numbers
    sanitized = ACCOUNT_CARD_REGEX.sub(mask_account_number, sanitized)

    # 5. Mask phone numbers
    sanitized = PHONE_REGEX.sub(mask_phone_number, sanitized)

    return sanitized
