"""
Domain C: Entities, Relationships, and Evidence Models for SIH26189.
Tables:
10. entities
11. entity_aliases
12. entity_identifiers
13. relationships
14. relationship_evidence
15. events (append-only)
16. communications (append-only)
17. transactions (append-only, fixed-decimal currency)
18. locations
19. vehicles
20. organizations
21. phones
22. accounts
23. investigation_notes
"""

from enum import Enum
import hashlib
import re
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from backend.db.base import Base
from backend.db.types import AmountType, GUIDType, JSONBType


class RelationshipEvidenceState(str, Enum):
    """
    Canonical relationship evidence states per 01_SHARED_TYPES.md (Section 1.4).
    OBSERVED: Explicitly found in raw, unprocessed source files.
    CORROBORATED: Confirmed by multiple independent source files or data categories.
    CONFIRMED: Manually verified and locked by an investigator.
    REJECTED: Explicitly flagged as false or untrustworthy by an investigator.
    INFERRED: Machine-learning generated (GATv2 or heuristic link prediction).
    """
    OBSERVED = "OBSERVED"
    CORROBORATED = "CORROBORATED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    INFERRED = "INFERRED"

    # Backward-compatible alias
    PREDICTED = "INFERRED"


def normalize_identifier(id_type: str, raw_val: str) -> str:
    """
    Normalizes sensitive external identifiers (Phone, Bank Account, Vehicle Plate)
    prior to hashing, enforcing strict canonical formats.
    """
    if not raw_val:
        return ""
    clean = raw_val.strip()
    id_upper = id_type.strip().upper()
    if id_upper in ("PHONE", "PHONE_NUMBER"):
        digits = re.sub(r"\D", "", clean)
        if clean.startswith("+"):
            return f"+{digits}"
        if len(digits) == 10:
            return f"+91{digits}"
        if len(digits) == 11 and digits.startswith("0"):
            return f"+91{digits[1:]}"
        return digits
    elif id_upper in ("BANK_ACCOUNT", "BANK_ACCOUNT_NUM", "ACCOUNT"):
        return re.sub(r"\s+", "", clean).upper()
    elif id_upper in ("VEHICLE", "VEHICLE_PLATE"):
        return re.sub(r"[\s\-]+", "", clean).upper()
    elif id_upper in ("UPI", "UPI_VPA", "VPA"):
        return re.sub(r"\s+", "", clean).lower()
    return clean


def hash_identifier(normalized_val: str) -> str:
    """Computes deterministic SHA-256 hex digest of a normalized identifier."""
    if not normalized_val:
        return ""
    return hashlib.sha256(normalized_val.encode("utf-8")).hexdigest()


def mask_identifier(id_type: str, raw_val: str) -> str:
    """Defensive masking for human-readable display of sensitive values."""
    if not raw_val:
        return "****"
    clean = raw_val.strip()
    if len(clean) <= 4:
        return "****"
    return f"{clean[:2]}{'*' * (len(clean) - 4)}{clean[-2:]}"


class Entity(Base):
    """
    entities table: Canonical domain objects resolved within a case.
    """
    __tablename__ = "entities"

    entity_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="RESTRICT"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    __table_args__ = (
        Index("idx_entities_case_type", "case_id", "entity_type"),
    )

    case = relationship("Case")
    aliases = relationship("EntityAlias", back_populates="entity", cascade="all, delete-orphan")
    identifiers = relationship("EntityIdentifier", back_populates="entity", cascade="all, delete-orphan")


class EntityAlias(Base):
    """
    entity_aliases table: Observed names and aliases for canonical entities.
    """
    __tablename__ = "entity_aliases"

    alias_id = Column(GUIDType, primary_key=True, default=uuid4)
    entity_id = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="CASCADE"), nullable=False, index=True)
    alias_text = Column(String(255), nullable=False)
    source_ref = Column(String(255), nullable=True)

    entity = relationship("Entity", back_populates="aliases")


class EntityIdentifier(Base):
    """
    entity_identifiers table: Normalized hashes and target values for entities.
    Never stores plaintext sensitive credentials as system primary keys.
    """
    __tablename__ = "entity_identifiers"

    identifier_id = Column(GUIDType, primary_key=True, default=uuid4)
    entity_id = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    normalized_value_hash = Column(String(64), nullable=False)
    value_policy = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("entity_id", "type", "normalized_value_hash", name="uq_entity_identifiers_entity_type_hash"),
        Index("idx_entity_identifiers_type_hash", "type", "normalized_value_hash"),
    )

    entity = relationship("Entity", back_populates="identifiers")


class Relationship(Base):
    """
    relationships table: Authoritative associations between canonical entities.
    """
    __tablename__ = "relationships"

    relationship_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="RESTRICT"), nullable=False)
    source_entity_uuid = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False)
    target_entity_uuid = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=RelationshipEvidenceState.OBSERVED.value)
    
    # Dempster-Shafer / Subjective Logic Fields
    belief = Column(Float, nullable=False, default=0.0)
    disbelief = Column(Float, nullable=False, default=0.0)
    uncertainty = Column(Float, nullable=False, default=1.0)
    conflict_mass = Column(Float, nullable=False, default=0.0)
    evidence_count = Column(Integer, nullable=False, default=0)
    relationship_confidence = Column(Float, nullable=False, default=0.0)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    __table_args__ = (
        Index("idx_relationships_case_source_target", "case_id", "source_entity_uuid", "target_entity_uuid"),
        CheckConstraint(
            "status IN ('OBSERVED', 'CORROBORATED', 'CONFIRMED', 'REJECTED', 'INFERRED', 'MERGED_SELF_LOOP')",
            name="ck_relationships_status",
        ),
    )

    case = relationship("Case")
    source_entity = relationship("Entity", foreign_keys=[source_entity_uuid])
    target_entity = relationship("Entity", foreign_keys=[target_entity_uuid])
    evidence = relationship("RelationshipEvidence", back_populates="relationship", cascade="all, delete-orphan")


class RelationshipEvidence(Base):
    """
    relationship_evidence table: Provenance chain and supporting evidence for relationships.
    """
    __tablename__ = "relationship_evidence"

    evidence_id = Column(GUIDType, primary_key=True, default=uuid4)
    relationship_id = Column(GUIDType, ForeignKey("relationships.relationship_id", ondelete="CASCADE"), nullable=False, index=True)
    source_ref = Column(String(255), nullable=False)
    support_type = Column(String(100), nullable=False)

    relationship = relationship("Relationship", back_populates="evidence")


class Event(Base):
    """
    events table: Append-only temporal log of case events.
    """
    __tablename__ = "events"

    event_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="RESTRICT"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    entity_refs = Column(JSONBType, nullable=True)
    source = Column(String(255), nullable=True)

    case = relationship("Case")


class Communication(Base):
    """
    communications table: Append-only CDR rows and telecom interaction events.
    """
    __tablename__ = "communications"

    communication_id = Column(GUIDType, primary_key=True, default=uuid4)
    caller_ref = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False, index=True)
    receiver_ref = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False, index=True)
    duration = Column(Integer, nullable=True)
    timestamps = Column(DateTime(timezone=True), nullable=False)
    channel = Column(String(50), nullable=False)

    caller = relationship("Entity", foreign_keys=[caller_ref])
    receiver = relationship("Entity", foreign_keys=[receiver_ref])


class Transaction(Base):
    """
    transactions table: Append-only financial transaction records.
    Invariant: absolute fixed-decimal precision; binary float types are forbidden.
    """
    __tablename__ = "transactions"

    transaction_id = Column(GUIDType, primary_key=True, default=uuid4)
    sender_ref = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False, index=True)
    receiver_ref = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(AmountType, nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    channel = Column(String(50), nullable=False)
    time = Column(DateTime(timezone=True), nullable=False)

    sender = relationship("Entity", foreign_keys=[sender_ref])
    receiver = relationship("Entity", foreign_keys=[receiver_ref])


class Location(Base):
    """
    locations table: Canonical geographical coordinates and place data.
    """
    __tablename__ = "locations"

    location_id = Column(GUIDType, primary_key=True, default=uuid4)
    normalized_label = Column(String(255), nullable=False)
    geography = Column(String(255), nullable=True)
    lat_lon_policy = Column(String(100), nullable=True)


class Vehicle(Base):
    """
    vehicles table: Transport entity metadata with masked license plate values.
    """
    __tablename__ = "vehicles"

    vehicle_id = Column(GUIDType, primary_key=True, default=uuid4)
    masked_plate = Column(String(50), nullable=False)
    type = Column(String(50), nullable=True)
    source_refs = Column(JSONBType, nullable=True)


class Organization(Base):
    """
    organizations table: Corporate and institutional entity records.
    """
    __tablename__ = "organizations"

    organization_id = Column(GUIDType, primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    registry_type = Column(String(100), nullable=True)
    identifiers = Column(JSONBType, nullable=True)


class Phone(Base):
    """
    phones table: SIM card and telecommunication profile records.
    """
    __tablename__ = "phones"

    phone_id = Column(GUIDType, primary_key=True, default=uuid4)
    normalized_number = Column(String(50), nullable=False)
    active_status = Column(String(50), nullable=False, default="ACTIVE")


class Account(Base):
    """
    accounts table: Payment profiles and bank accounts.
    """
    __tablename__ = "accounts"

    account_id = Column(GUIDType, primary_key=True, default=uuid4)
    masked_identifier = Column(String(100), nullable=False)
    bank_type = Column(String(50), nullable=True)
    provider = Column(String(100), nullable=True)


class InvestigationNote(Base):
    """
    investigation_notes table: Case-scoped human notes and entity references.
    """
    __tablename__ = "investigation_notes"

    note_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    author_uuid = Column(GUIDType, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    notes_text = Column(Text, nullable=False)
    entity_refs = Column(JSONBType, nullable=True)

    case = relationship("Case")
    author = relationship("User")
