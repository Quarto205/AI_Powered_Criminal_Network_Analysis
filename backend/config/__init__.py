"""
Configuration package for SIH26189.
"""

from backend.config.database import DatabaseSettings, get_db_settings, set_db_settings

__all__ = [
    "DatabaseSettings",
    "get_db_settings",
    "set_db_settings",
]

try:
    from backend.config.security import (
        SecuritySettings,
        get_security_settings,
        set_security_settings,
    )
    __all__.extend([
        "SecuritySettings",
        "get_security_settings",
        "set_security_settings",
    ])
except ImportError:
    pass
