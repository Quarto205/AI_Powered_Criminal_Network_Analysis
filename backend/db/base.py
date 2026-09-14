"""
Declarative base and metadata registry for SIH26189.
Configures canonical constraint naming conventions for deterministic migrations.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# Canonical naming convention ensures deterministic index and constraint names across engines
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

Base = declarative_base(metadata=metadata)
