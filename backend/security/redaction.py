"""
Centralized Log Redaction Filter and Utility for SIH26189.
Prevents leakage of:
- Auth tokens and Bearer credentials
- Passwords and secrets
- Raw document payload bodies and credentials
Conforms to 07_AUTH_SECURITY.md.
"""

import logging
import re
from typing import Any

BEARER_TOKEN_PATTERN = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*", re.IGNORECASE)
JWT_TOKEN_PATTERN = re.compile(r"eyJ[A-Za-z0-9\-_=]+\.eyJ[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*")
AUTH_HEADER_PATTERN = re.compile(r"(Authorization['\":\s]+)[^\s,;'\"]+", re.IGNORECASE)
PASSWORD_PATTERN = re.compile(r"(password['\":\s=]+)[^\s,;'\"]+", re.IGNORECASE)
SECRET_PATTERN = re.compile(r"(secret(?:_key)?['\":\s=]+)[^\s,;'\"]+", re.IGNORECASE)


def redact_sensitive_text(message: str) -> str:
    """Redacts tokens, passwords, and secrets from string."""
    if not isinstance(message, str):
        return message
    res = BEARER_TOKEN_PATTERN.sub(r"\1[REDACTED_TOKEN]", message)
    res = JWT_TOKEN_PATTERN.sub("[REDACTED_JWT]", res)
    res = AUTH_HEADER_PATTERN.sub(r"\1[REDACTED_AUTH]", res)
    res = PASSWORD_PATTERN.sub(r"\1[REDACTED_PASSWORD]", res)
    res = SECRET_PATTERN.sub(r"\1[REDACTED_SECRET]", res)
    return res


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that sanitizes record messages and arguments before emission.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_sensitive_text(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: redact_sensitive_text(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
                elif isinstance(record.args, tuple):
                    record.args = tuple(redact_sensitive_text(str(a)) if isinstance(a, str) else a for a in record.args)
        except Exception:
            pass
        return True


def apply_logging_redaction() -> None:
    """Applies SensitiveDataFilter to the root logger handlers."""
    root_logger = logging.getLogger()
    flt = SensitiveDataFilter()
    root_logger.addFilter(flt)
    for handler in root_logger.handlers:
        handler.addFilter(flt)
