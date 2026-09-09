"""
Document Repository for SIH26189.
Manages transactional document entity records, versioning, case isolation,
status transitions, and unique content hash deduplication per case.
Conforms to 02_DATABASE_SCHEMA.md (Section 2.1 documents table) and 06_WORKFLOWS.md.
"""

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

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
    """

    def __init__(self):
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
        return record

    def get(self, document_id: UUID, case_id: UUID) -> Optional[DocumentRecord]:
        """
        Retrieves a document strictly bounded by case_id.
        Returns None if not found in that case (enforcing case isolation).
        """
        return self._documents.get((case_id, document_id))

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
        if key not in self._documents:
            raise DocumentNotFoundError(f"Cannot update status: document {document_id} not found in case {case_id}.")

        record = self._documents[key]
        updated = record.model_copy(
            update={
                "status": status,
                "error_message": error_message,
                "extraction_job_id": extraction_job_id or record.extraction_job_id,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._documents[key] = updated
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
        return version

    def get_latest_version(self, document_id: UUID) -> Optional[DocumentVersionRecord]:
        """Retrieves the most recent version record for a document."""
        versions = self._document_versions.get(document_id, [])
        return versions[-1] if versions else None

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
        return chunk

    def list_chunks(self, document_id: UUID) -> List[DocumentChunkRecord]:
        """Lists chunks for a document ordered deterministically by page_number, then chunk_id."""
        chunks = self._document_chunks.get(document_id, [])
        return sorted(chunks, key=lambda c: (c.page_number or 0, str(c.chunk_id)))

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
