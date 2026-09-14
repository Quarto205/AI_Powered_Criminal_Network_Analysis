"""
Domain B: Document and Ingestion Models for SIH26189.
Tables:
7. documents
8. document_versions
9. document_chunks

All tables in this domain represent immutable source artifacts and are append-only.
"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from backend.db.base import Base
from backend.db.types import GUIDType, JSONBType


class Document(Base):
    """
    documents table: Immutable source artifact metadata.
    Enforces unique file_hash per case_id.
    """
    __tablename__ = "documents"

    document_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="RESTRICT"), nullable=False, index=True)
    file_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False)
    storage_key = Column(String(512), nullable=False)
    status = Column(String(50), nullable=False, default="RECEIVED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("case_id", "file_hash", name="uq_documents_case_hash"),
        Index("idx_documents_case_hash", "case_id", "file_hash", unique=True),
    )

    # Relationships
    case = relationship("Case")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """
    document_versions table: Traceability and immutable versions of source documents.
    """
    __tablename__ = "document_versions"

    version_id = Column(GUIDType, primary_key=True, default=uuid4)
    document_id = Column(GUIDType, ForeignKey("documents.document_id", ondelete="RESTRICT"), nullable=False, index=True)
    version_hash = Column(String(64), nullable=False)
    meta = Column("metadata", JSONBType, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    document = relationship("Document", back_populates="versions")
    chunks = relationship("DocumentChunk", back_populates="version", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """
    document_chunks table: Parsed text chunks and provenance spans from source documents.
    """
    __tablename__ = "document_chunks"

    chunk_id = Column(GUIDType, primary_key=True, default=uuid4)
    version_id = Column(GUIDType, ForeignKey("document_versions.version_id", ondelete="RESTRICT"), nullable=False, index=True)
    page_number = Column(Integer, nullable=True)
    character_span = Column(String(100), nullable=True)
    text_hash = Column(String(64), nullable=False)
    storage_ref = Column(String(512), nullable=False)

    version = relationship("DocumentVersion", back_populates="chunks")
