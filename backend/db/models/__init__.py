"""
Central models package for SIH26189.
Exports all 31 canonical relational models and activates cross-engine
append-only immutability listeners.
"""

from backend.db.base import Base, metadata
from backend.db.triggers import register_orm_immutability_listener

# Domain A: Identity, RBAC, and Multi-Tenant (6 tables)
from backend.db.models.identity import (
    Case,
    CaseMember,
    Permission,
    Role,
    User,
    UserRole,
)

# Domain B: Ingestion and Source Artifacts (3 tables)
from backend.db.models.ingestion import (
    Document,
    DocumentChunk,
    DocumentVersion,
)

# Domain C: Entities, Relationships, and Evidence (14 tables)
from backend.db.models.entities import (
    Account,
    Communication,
    Entity,
    EntityAlias,
    EntityIdentifier,
    Event,
    InvestigationNote,
    Location,
    Organization,
    Phone,
    Relationship,
    RelationshipEvidence,
    Transaction,
    Vehicle,
)

# Domain D: AI, Analytics, and Audit (8 tables)
from backend.db.models.analytics import (
    Alert,
    AuditLog,
    Export,
    GraphSnapshot,
    ModelRun,
    Prediction,
    RiskScore,
    SavedQuery,
)

# Register immutability listeners on all append-only tables
for model_cls in [
    Document,
    DocumentVersion,
    DocumentChunk,
    Event,
    Communication,
    Transaction,
    AuditLog,
]:
    register_orm_immutability_listener(model_cls)

__all__ = [
    "Base",
    "metadata",
    # Domain A (1-6)
    "User",
    "Role",
    "Permission",
    "UserRole",
    "Case",
    "CaseMember",
    # Domain B (7-9)
    "Document",
    "DocumentVersion",
    "DocumentChunk",
    # Domain C (10-23)
    "Entity",
    "EntityAlias",
    "EntityIdentifier",
    "Relationship",
    "RelationshipEvidence",
    "Event",
    "Communication",
    "Transaction",
    "Location",
    "Vehicle",
    "Organization",
    "Phone",
    "Account",
    "InvestigationNote",
    # Domain D (24-31)
    "ModelRun",
    "Prediction",
    "RiskScore",
    "Alert",
    "GraphSnapshot",
    "AuditLog",
    "SavedQuery",
    "Export",
]
