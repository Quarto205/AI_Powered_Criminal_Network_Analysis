"""
Domain A: Identity, RBAC, and Multi-Tenant Models for SIH26189.
Tables:
1. users
2. roles
3. permissions
4. user_roles
5. cases
6. case_members
"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from backend.db.base import Base
from backend.db.types import GUIDType


class User(Base):
    """
    users table: System identity and account credentials.
    """
    __tablename__ = "users"

    user_id = Column(GUIDType, primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    account_status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())

    # Relationships
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    case_memberships = relationship("CaseMember", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    """
    roles table: Role-Based Access Control definitions.
    """
    __tablename__ = "roles"

    role_id = Column(GUIDType, primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    users = relationship("User", secondary="user_roles", back_populates="roles")


class Permission(Base):
    """
    permissions table: RBAC action and resource permission grants.
    """
    __tablename__ = "permissions"

    permission_id = Column(GUIDType, primary_key=True, default=uuid4)
    permission_code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)


class UserRole(Base):
    """
    user_roles table: Pure join table mapping users to roles.
    """
    __tablename__ = "user_roles"

    user_id = Column(GUIDType, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(GUIDType, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)


class Case(Base):
    """
    cases table: Multi-tenant investigation boundary.
    """
    __tablename__ = "cases"

    case_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_code = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")
    jurisdiction = Column(String(100), nullable=False)
    created_by = Column(GUIDType, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    __table_args__ = (
        Index("idx_cases_case_code", "case_code", unique=True),
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("CaseMember", back_populates="case", cascade="all, delete-orphan")


class CaseMember(Base):
    """
    case_members table: Authorization map binding users to case tenancy.
    """
    __tablename__ = "case_members"

    case_member_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUIDType, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role_in_case = Column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint("case_id", "user_id", name="uq_case_members_case_user"),
        Index("idx_case_members_case_user", "case_id", "user_id"),
    )

    case = relationship("Case", back_populates="members")
    user = relationship("User", back_populates="case_memberships")
