"""
Custom and dialect-aware SQLAlchemy column types for SIH26189.
Guarantees PostgreSQL-native UUID, JSONB, and Decimal types with seamless
cross-dialect fallback for SQLite testing.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Numeric, Uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

# 1. UUID Primary Key / Foreign Key Type
# In SQLAlchemy 2.0, Uuid(as_uuid=True) generates native PostgreSQL UUID on Postgres
# and CHAR(32)/CHAR(36) on SQLite while consistently handling python uuid.UUID objects.
GUIDType = Uuid(as_uuid=True)

# 2. JSONB / Structured JSON Type
# Compiles to PostgreSQL JSONB in production, and standard JSON in SQLite.
JSONBType = JSONB().with_variant(JSON(), "sqlite")

# 3. Monetary Precision Decimal Type
# Invariant: absolute fixed-point decimal only; binary float types are forbidden.
MONETARY_PRECISION = 18
MONETARY_SCALE = 2
AmountType = Numeric(precision=MONETARY_PRECISION, scale=MONETARY_SCALE, asdecimal=True)
