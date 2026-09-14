"""
Database persistence package for SIH26189.
"""

from backend.db.base import Base, metadata
from backend.db.session import (
    create_all_tables,
    drop_all_tables,
    get_db,
    get_engine,
    get_session_factory,
)

__all__ = [
    "Base",
    "create_all_tables",
    "drop_all_tables",
    "get_db",
    "get_engine",
    "get_session_factory",
    "metadata",
]
