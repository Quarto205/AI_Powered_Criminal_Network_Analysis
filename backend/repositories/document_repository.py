"""
Document Repository for SIH26189.
Manages transactional document entity records, versioning, case isolation,
status transitions, and unique content hash deduplication per case.
Conforms to 02_DATABASE_SCHEMA.md (Section 2.1 documents table) and 06_WORKFLOWS.md.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

try:
    from backend.db.models.ingestion import (
        Document as DbDocument,
        DocumentVersion as DbDocumentVersion,
        DocumentChunk as DbDocumentChunk,
    )
except ImportError:
    DbDocument = None  # type: ignore
    DbDocumentVersion = None  # type: ignore
    DbDocumentChunk = None  # type: ignore

from backend.schemas.document_jobs import DocumentRecord, DocumentState


class DocumentRepositoryError(Exception):
    """Base repository error."""
    pass


class CaseIsolationViolationError(DocumentRepositoryError):
    """Raised when an operation attempts to access a document across case boundaries."""
    pass


class DuplicateDocumentError(DocumentRepositoryError):
    """Raised when an identical document hash is uploaded to the same case."""
    pass


class DocumentNotFoundError(DocumentRepositoryError):
    """Raised when a document record does not exist within the specified case."""
    pass


class DocumentVersionRecord(BaseModel):
    version_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    version_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentChunkRecord(BaseModel):
    chunk_id: UUID = Field(default_factory=uuid4)
    version_id: UUID
    document_id: UUID
    page_number: Optional[int] = None
    character_span: Optional[str] = None
    text_hash: str
    storage_ref: str


class DocumentRepository:
    """
    Repository for managing documents and enforcing multi-tenant case isolation.
    Maintains an in-memory cache and persists records to PostgreSQL when a session
    or session_factory is supplied.
    """

    def __init__(
        self,
        session: Optional[Any] = None,
        session_factory: Optional[Any] = None,
    ):
        self.session = session
        self.session_factory = session_factory
        # Primary store: (case_id, document_id) -> DocumentRecord
        self._documents: Dict[Tuple[UUID, UUID], DocumentRecord] = {}
        # Case hash set: (case_id, file_hash) -> document_id (enforces unique file_hash per case)
        self._case_hashes: Dict[Tuple[UUID, str], UUID] = {}
        # Authorized case memberships: user_id -> Set[case_id]
        self._case_memberships: Dict[UUID, Set[UUID]] = {}
        # Stored extraction results: document_id -> extraction_payload dict
        self._extraction_results: Dict[UUID, Dict] = {}
        # Stored versions: document_id -> List[DocumentVersionRecord]
        self._document_versions: Dict[UUID, List[DocumentVersionRecord]] = {}
        # Stored chunks: document_id -> List[DocumentChunkRecord]
        self._document_chunks: Dict[UUID, List[DocumentChunkRecord]] = {}

    @contextmanager
    def _session_scope(self):
        if self.session is not None:
            yield self.session
            return
        if self.session_factory is not None and DbDocument is not None:
            factory = self.session_factory
            if callable(factory):
                res = factory()
                from sqlalchemy.orm import Session as SqlAlchemySession, sessionmaker
                if isinstance(res, sessionmaker):
                    sess = res()
                elif isinstance(res, SqlAlchemySession):
                    sess = res
                else:
                    yield None
                    return
                try:
                    yield sess
                    sess.commit()
                except Exception:
                    sess.rollback()
                    raise
                finally:
                    sess.close()
                return
        yield None

    def authorize_case_access(self, user_id: UUID, case_id: UUID) -> None:
        """Registers authorized membership for a user in a case."""
        if user_id not in self._case_memberships:
            self._case_memberships[user_id] = set()
        self._case_memberships[user_id].add(case_id)

    def check_user_access(self, user_id: UUID, case_id: UUID) -> bool:
        """Checks if a user is an authorized member of a case."""
        return case_id in self._case_memberships.get(user_id, set())

    @staticmethod
    def calculate_file_hash(data: bytes) -> str:
        """Calculates canonical SHA-256 hash of binary content."""
        return hashlib.sha256(data).hexdigest()

    def create(
        self,
        document_id: UUID,
        case_id: UUID,
        filename: str,
        file_type: str,
        file_hash: str,
        storage_key: str,
        initial_status: DocumentState = DocumentState.RECEIVED,
    ) -> DocumentRecord:
        """
        Creates a new document record.
        Enforces unique file_hash within the case_id boundary.
        """
        hash_key = (case_id, file_hash)
        if hash_key in self._case_hashes:
            existing_doc_id = self._case_hashes[hash_key]
            raise DuplicateDocumentError(
                f"Document with hash '{file_hash[:12]}...' already exists in case {case_id} (doc_id: {existing_doc_id})."
            )

        now = datetime.now(timezone.utc)
        record = DocumentRecord(
            document_id=document_id,
            case_id=case_id,
            filename=filename,
            file_type=file_type,
            file_hash=file_hash,
            storage_key=storage_key,
            status=initial_status,
            created_at=now,
            updated_at=now,
        )

        self._documents[(case_id, document_id)] = record
        self._case_hashes[hash_key] = document_id

        # Authoritative persistence to PostgreSQL
        with self._session_scope() as sess:
            if sess is not None and DbDocument is not None:
                try:
                    existing = sess.query(DbDocument).filter(DbDocument.document_id == document_id).first()
                    if not existing:
                        status_str = initial_status.value if hasattr(initial_status, "value") else str(initial_status)
                        db_doc = DbDocument(
                            document_id=document_id,
                            case_id=case_id,
                            file_type=file_type,
                            file_hash=file_hash,
                            storage_key=storage_key,
                            status=status_str,
                            created_at=now,
                        )
                        sess.add(db_doc)
                        sess.flush()
                except Exception:
                    raise

        return record

    def get(self, document_id: UUID, case_id: UUID) -> Optional[DocumentRecord]:
        """
        Retrieves a document strictly bounded by case_id.
        Returns None if not found in that case (enforcing case isolation).
        """
        doc = self._documents.get((case_id, document_id))
        if doc is not None:
            return doc

        with self._session_scope() as sess:
            if sess is not None and DbDocument is not None:
                try:
                    db_doc = sess.query(DbDocument).filter(
                        DbDocument.document_id == document_id,
                        DbDocument.case_id == case_id
                    ).first()
                    if db_doc:
                        try:
                            st = DocumentState(db_doc.status)
                        except (ValueError, KeyError):
                            st = DocumentState.RECEIVED
                        filename = db_doc.storage_key.split("/")[-1] if db_doc.storage_key else "document"
                        rec = DocumentRecord(
                            document_id=db_doc.document_id,
                            case_id=db_doc.case_id,
                            filename=filename,
                            file_type=db_doc.file_type,
                            file_hash=db_doc.file_hash,
                            storage_key=db_doc.storage_key,
                            status=st,
                            created_at=db_doc.created_at or datetime.now(timezone.utc),
                            updated_at=db_doc.created_at or datetime.now(timezone.utc),
                        )
                        self._documents[(case_id, document_id)] = rec
                        self._case_hashes[(case_id, db_doc.file_hash)] = document_id
                        return rec
                except Exception:
                    raise

        return None

    def get_or_raise(self, document_id: UUID, case_id: UUID) -> DocumentRecord:
        """Retrieves a document strictly bounded by case_id or raises DocumentNotFoundError."""
        doc = self.get(document_id, case_id)
        if not doc:
            raise DocumentNotFoundError(f"Document {document_id} not found in case {case_id}.")
        return doc

    def update_status(
        self,
        document_id: UUID,
        case_id: UUID,
        status: DocumentState,
        error_message: Optional[str] = None,
        extraction_job_id: Optional[UUID] = None,
    ) -> DocumentRecord:
        """
        Atomically updates document lifecycle status and timestamps.
        Strictly verifies case boundaries.
        """
        key = (case_id, document_id)
        doc = self.get(document_id, case_id)
        if not doc:
            raise DocumentNotFoundError(f"Cannot update status: document {document_id} not found in case {case_id}.")

        record = self._documents[key]
        now = datetime.now(timezone.utc)
        updated = record.model_copy(
            update={
                "status": status,
                "error_message": error_message,
                "extraction_job_id": extraction_job_id or record.extraction_job_id,
                "updated_at": now,
            }
        )
        self._documents[key] = updated

        with self._session_scope() as sess:
            if sess is not None and DbDocument is not None:
                try:
                    db_doc = sess.query(DbDocument).filter(
                        DbDocument.document_id == document_id,
                        DbDocument.case_id == case_id
                    ).first()
                    if db_doc:
                        status_str = status.value if hasattr(status, "value") else str(status)
                        db_doc.status = status_str
                        sess.flush()
                except Exception:
                    raise

        return updated

    def save_extraction_result(self, document_id: UUID, result_dict: Dict) -> None:
        """Stores the validated extraction result payload associated with a document."""
        self._extraction_results[document_id] = result_dict

    def get_extraction_result(self, document_id: UUID) -> Optional[Dict]:
        """Retrieves the validated extraction result payload for a document."""
        return self._extraction_results.get(document_id)

    def list_by_case(self, case_id: UUID) -> List[DocumentRecord]:
        """Lists all document records within a single case tenant."""
        return [doc for (c_id, _), doc in self._documents.items() if c_id == case_id]

    def create_version(
        self,
        document_id: UUID,
        version_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentVersionRecord:
        """Creates and stores a new document version."""
        version = DocumentVersionRecord(
            document_id=document_id,
            version_hash=version_hash,
            metadata=metadata or {},
        )
        if document_id not in self._document_versions:
            self._document_versions[document_id] = []
        self._document_versions[document_id].append(version)

        with self._session_scope() as sess:
            if sess is not None and DbDocumentVersion is not None:
                try:
                    db_ver = DbDocumentVersion(
                        version_id=version.version_id,
                        document_id=document_id,
                        version_hash=version_hash,
                        meta=metadata or {},
                        created_at=version.created_at,
                    )
                    sess.add(db_ver)
                    sess.flush()
                except Exception:
                    raise

        return version

    def get_latest_version(self, document_id: UUID) -> Optional[DocumentVersionRecord]:
        """Retrieves the most recent version record for a document."""
        versions = self._document_versions.get(document_id, [])
        if versions:
            return versions[-1]

        with self._session_scope() as sess:
            if sess is not None and DbDocumentVersion is not None:
                try:
                    db_ver = (
                        sess.query(DbDocumentVersion)
                        .filter(DbDocumentVersion.document_id == document_id)
                        .order_by(DbDocumentVersion.created_at.desc())
                        .first()
                    )
                    if db_ver:
                        ver = DocumentVersionRecord(
                            version_id=db_ver.version_id,
                            document_id=db_ver.document_id,
                            version_hash=db_ver.version_hash,
                            metadata=db_ver.meta or {},
                            created_at=db_ver.created_at or datetime.now(timezone.utc),
                        )
                        if document_id not in self._document_versions:
                            self._document_versions[document_id] = []
                        self._document_versions[document_id].append(ver)
                        return ver
                except Exception:
                    raise

        return None

    def create_chunk(
        self,
        version_id: UUID,
        document_id: UUID,
        page_number: Optional[int],
        character_span: Optional[str],
        text_hash: str,
        storage_ref: str,
    ) -> DocumentChunkRecord:
        """Creates and stores an ordered document chunk record."""
        chunk = DocumentChunkRecord(
            version_id=version_id,
            document_id=document_id,
            page_number=page_number,
            character_span=character_span,
            text_hash=text_hash,
            storage_ref=storage_ref,
        )
        if document_id not in self._document_chunks:
            self._document_chunks[document_id] = []
        self._document_chunks[document_id].append(chunk)

        with self._session_scope() as sess:
            if sess is not None and DbDocumentChunk is not None:
                try:
                    db_chunk = DbDocumentChunk(
                        chunk_id=chunk.chunk_id,
                        version_id=version_id,
                        page_number=page_number,
                        character_span=character_span,
                        text_hash=text_hash,
                        storage_ref=storage_ref,
                    )
                    sess.add(db_chunk)
                    sess.flush()
                except Exception:
                    raise

        return chunk

    def list_chunks(self, document_id: UUID) -> List[DocumentChunkRecord]:
        """Lists chunks for a document ordered deterministically by page_number, then chunk_id."""
        chunks = self._document_chunks.get(document_id, [])
        if chunks:
            return sorted(chunks, key=lambda c: (c.page_number or 0, str(c.chunk_id)))

        with self._session_scope() as sess:
            if sess is not None and DbDocumentChunk is not None and DbDocumentVersion is not None:
                try:
                    db_chunks = (
                        sess.query(DbDocumentChunk)
                        .join(DbDocumentVersion, DbDocumentChunk.version_id == DbDocumentVersion.version_id)
                        .filter(DbDocumentVersion.document_id == document_id)
                        .order_by(DbDocumentChunk.page_number.asc(), DbDocumentChunk.chunk_id.asc())
                        .all()
                    )
                    if db_chunks:
                        recs = [
                            DocumentChunkRecord(
                                chunk_id=c.chunk_id,
                                version_id=c.version_id,
                                document_id=document_id,
                                page_number=c.page_number,
                                character_span=c.character_span,
                                text_hash=c.text_hash,
                                storage_ref=c.storage_ref,
                            )
                            for c in db_chunks
                        ]
                        self._document_chunks[document_id] = recs
                        return recs
                except Exception:
                    raise

        return []

    def get_chunk_count(self, document_id: UUID) -> int:
        """Returns total number of chunks created for a document."""
        return len(self._document_chunks.get(document_id, []))

    def archive_document(self, document_id: UUID, case_id: UUID) -> DocumentRecord:
        """Soft-deletes/archives a document by setting its status to REJECTED."""
        return self.update_status(
            document_id=document_id,
            case_id=case_id,
            status=DocumentState.REJECTED,
        )

    def clear(self) -> None:
        """Clears records between test runs."""
        self._documents.clear()
        self._case_hashes.clear()
        self._case_memberships.clear()
        self._extraction_results.clear()
        self._document_versions.clear()
        self._document_chunks.clear()
