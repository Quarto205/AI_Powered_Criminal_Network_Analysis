"""
Document Domain Service for SIH26189.
Encapsulates business rules, magic byte inspection, SHA-256 hashing,
case-scoped deduplication, asynchronous worker dispatch, document listing,
detail querying with aggregate counts, chunk retrieval, and soft-delete/archival.
"""

from datetime import datetime, timezone
import hashlib
import os
import re
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from agents.extraction.ocr.security import (
    DEFAULT_MAX_FILE_SIZE,
    inspect_file_signature,
    sanitize_filename,
    validate_document_security,
)
from backend.db.models.identity import User
from backend.db.models.ingestion import Document, DocumentChunk, DocumentVersion
from backend.jobs.worker_bridge import WorkerBridge
from backend.repositories.document_repository import (
    DocumentNotFoundError,
    DocumentRecord,
    DocumentRepository,
    DuplicateDocumentError,
)
from backend.repositories.storage import BaseDocumentStorage
from backend.schemas.document_jobs import DocumentState
from backend.schemas.documents import (
    DocumentArchiveResponse,
    DocumentChunkItem,
    DocumentChunkListResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadData,
    DocumentVersionInfo,
)
from backend.security.audit import SecurityAuditAction, record_security_event


class DocumentService:
    """
    High-level business service for document ingestion and management.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        storage: BaseDocumentStorage,
        worker_bridge: WorkerBridge,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    ):
        self.repository = repository
        self.storage = storage
        self.worker_bridge = worker_bridge
        self.max_file_size = max_file_size

    def validate_and_upload(
        self,
        case_id: UUID,
        filename: str,
        data: bytes,
        user: Optional[User] = None,
        db: Optional[Session] = None,
        is_legacy_auth: bool = False,
    ) -> DocumentUploadData:
        """
        Validates uploaded file payload, enforces magic bytes and size limits,
        checks case-scoped deduplication, persists initial RECEIVED state,
        stores binary content, dispatches async background worker task,
        and logs the audit event.
        """
        # 1. Enforce file size limit
        if len(data) > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"Document payload exceeds maximum allowed size of {self.max_file_size // (1024 * 1024)}MB.",
            )

        # 2. Check for empty payload
        if len(data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document payload is empty (0 bytes).",
            )

        # 3. Path sanitization and directory traversal prevention
        try:
            clean_filename = sanitize_filename(filename or "document.pdf")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename: {exc}",
            )

        # 4. Magic-byte inspection
        try:
            doc_type, detected_mime = inspect_file_signature(data)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {exc}",
            )

        # 5. Compute canonical SHA-256 hash
        file_hash = hashlib.sha256(data).hexdigest()

        # 6. Case-scoped duplicate check
        # Check in repository
        hash_key = (case_id, file_hash)
        if hash_key in self.repository._case_hashes:
            if is_legacy_auth:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document with hash '{file_hash[:12]}...' already exists in case {case_id}.",
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document with hash '{file_hash[:12]}...' already exists in case {case_id}.",
            )

        # Check in DB if session is available
        if db is not None:
            existing_db_doc = (
                db.query(Document)
                .filter(Document.case_id == case_id, Document.file_hash == file_hash)
                .first()
            )
            if existing_db_doc:
                if is_legacy_auth:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document with hash '{file_hash[:12]}...' already exists in case {case_id}.",
                    )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Document with hash '{file_hash[:12]}...' already exists in case {case_id}.",
                )

        document_id = uuid4()
        job_id = uuid4()
        storage_key = f"cases/{case_id}/docs/{document_id}/{clean_filename}"

        # 7. Persist binary payload into storage abstraction
        self.storage.put(storage_key, data)

        # 8. Persist in DocumentRepository
        if user is not None:
            self.repository.authorize_case_access(user.user_id, case_id)

        self.repository.create(
            document_id=document_id,
            case_id=case_id,
            filename=clean_filename,
            file_type=detected_mime,
            file_hash=file_hash,
            storage_key=storage_key,
            initial_status=DocumentState.RECEIVED,
        )

        # 9. Persist in SQLAlchemy DB if available
        if db is not None:
            db_doc = Document(
                document_id=document_id,
                case_id=case_id,
                file_type=detected_mime,
                file_hash=file_hash,
                storage_key=storage_key,
                status=DocumentState.RECEIVED.value,
            )
            db.add(db_doc)
            db.flush()

        # 10. Dispatch asynchronous worker job
        caller_uuid = user.user_id if user else None
        self.worker_bridge.submit_document_job(
            document_id=document_id,
            case_id=case_id,
            filename=clean_filename,
            storage_key=storage_key,
            caller_user_id=caller_uuid,
            job_id=job_id,
        )

        # 11. Audit state mutation
        if db is not None and user is not None:
            record_security_event(
                db=db,
                action_code=SecurityAuditAction.DOCUMENT_UPLOAD,
                actor_uuid=user.user_id,
                case_id=case_id,
                target_item=f"DOCUMENT:{document_id}",
                outcome="SUCCESS",
            )
            db.commit()

        now = datetime.now(timezone.utc)
        return DocumentUploadData(
            document_id=document_id,
            job_id=job_id,
            case_id=case_id,
            file_name=clean_filename,
            file_type=detected_mime,
            file_hash=file_hash,
            status=DocumentState.RECEIVED.value,
            created_at=now,
        )

    def list_documents(
        self,
        case_id: UUID,
        status_filter: Optional[str] = None,
        file_type_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None,
    ) -> DocumentListResponse:
        """
        Retrieves paginated document summaries within the case tenant boundary.
        """
        if limit <= 0 or limit > 200:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Limit must be between 1 and 200.",
            )
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Offset must be greater than or equal to 0.",
            )

        # Query PostgreSQL DB if available
        if db is not None:
            query = db.query(Document).filter(Document.case_id == case_id)
            if status_filter:
                query = query.filter(Document.status == status_filter)
            if file_type_filter:
                query = query.filter(Document.file_type == file_type_filter)

            total = query.count()
            docs = (
                query.order_by(Document.created_at.desc(), Document.document_id.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            # Map to summaries; lookup filename from repository if available
            items = []
            for d in docs:
                repo_rec = self.repository.get(d.document_id, case_id)
                fname = repo_rec.filename if repo_rec else os.path.basename(d.storage_key)
                items.append(
                    DocumentSummary(
                        document_id=d.document_id,
                        case_id=d.case_id,
                        file_name=fname,
                        file_type=d.file_type,
                        file_hash=d.file_hash,
                        status=d.status,
                        created_at=d.created_at,
                    )
                )
            return DocumentListResponse(items=items, total=total, limit=limit, offset=offset)

        # Fallback to DocumentRepository
        repo_docs = self.repository.list_by_case(case_id)
        if status_filter:
            repo_docs = [d for d in repo_docs if d.status.value == status_filter or d.status == status_filter]
        if file_type_filter:
            repo_docs = [d for d in repo_docs if d.file_type == file_type_filter]

        total = len(repo_docs)
        # Deterministic sorting: created_at desc, document_id asc
        sorted_docs = sorted(repo_docs, key=lambda d: (-d.created_at.timestamp(), str(d.document_id)))
        paginated = sorted_docs[offset : offset + limit]

        items = [
            DocumentSummary(
                document_id=d.document_id,
                case_id=d.case_id,
                file_name=d.filename,
                file_type=d.file_type,
                file_hash=d.file_hash,
                status=d.status.value if hasattr(d.status, "value") else str(d.status),
                created_at=d.created_at,
            )
            for d in paginated
        ]
        return DocumentListResponse(items=items, total=total, limit=limit, offset=offset)

    def get_document_detail(
        self,
        case_id: UUID,
        document_id: UUID,
        db: Optional[Session] = None,
    ) -> DocumentDetailResponse:
        """
        Retrieves full document metadata, version info, and chunk count.
        Enforces case isolation (404 for non-existent or cross-case document).
        """
        repo_doc = self.repository.get(document_id, case_id)
        db_doc = None

        if db is not None:
            db_doc = (
                db.query(Document)
                .filter(Document.document_id == document_id, Document.case_id == case_id)
                .first()
            )

        if not repo_doc and not db_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        # Resolve fields prioritizing latest repository/worker state
        status_val = repo_doc.status.value if repo_doc and hasattr(repo_doc.status, "value") else (
            repo_doc.status if repo_doc else db_doc.status
        )
        file_name = repo_doc.filename if repo_doc else os.path.basename(db_doc.storage_key)
        file_type = repo_doc.file_type if repo_doc else db_doc.file_type
        file_hash = repo_doc.file_hash if repo_doc else db_doc.file_hash
        storage_key = repo_doc.storage_key if repo_doc else db_doc.storage_key
        created_at = repo_doc.created_at if repo_doc else db_doc.created_at
        updated_at = repo_doc.updated_at if repo_doc else created_at
        error_msg = repo_doc.error_message if repo_doc else None

        # Resolve latest version
        latest_ver_info = None
        ver_rec = self.repository.get_latest_version(document_id)
        if ver_rec:
            latest_ver_info = DocumentVersionInfo(
                version_id=ver_rec.version_id,
                version_hash=ver_rec.version_hash,
                created_at=ver_rec.created_at,
                metadata=ver_rec.metadata,
            )
        elif db is not None:
            db_ver = (
                db.query(DocumentVersion)
                .filter(DocumentVersion.document_id == document_id)
                .order_by(DocumentVersion.created_at.desc())
                .first()
            )
            if db_ver:
                latest_ver_info = DocumentVersionInfo(
                    version_id=db_ver.version_id,
                    version_hash=db_ver.version_hash,
                    created_at=db_ver.created_at,
                    metadata=db_ver.meta,
                )

        # Resolve chunk count
        chunk_count = self.repository.get_chunk_count(document_id)
        if chunk_count == 0 and db is not None:
            chunk_count = (
                db.query(DocumentChunk)
                .join(DocumentVersion, DocumentChunk.version_id == DocumentVersion.version_id)
                .filter(DocumentVersion.document_id == document_id)
                .count()
            )

        error_category = None
        if status_val == DocumentState.FAILED.value or status_val == "FAILED":
            error_category = "PROCESSING_FAILED"
            if error_msg:
                if "corrupt" in error_msg.lower():
                    error_category = "CORRUPTED_FILE"
                elif "password" in error_msg.lower():
                    error_category = "PASSWORD_PROTECTED"
                elif "empty" in error_msg.lower():
                    error_category = "EMPTY_DOCUMENT"
                elif "unsupported" in error_msg.lower():
                    error_category = "UNSUPPORTED_FORMAT"

        return DocumentDetailResponse(
            document_id=document_id,
            case_id=case_id,
            file_name=file_name,
            file_type=file_type,
            file_hash=file_hash,
            storage_key=storage_key,
            status=status_val,
            created_at=created_at,
            updated_at=updated_at,
            latest_version=latest_ver_info,
            chunk_count=chunk_count,
            error_category=error_category,
            error_message=error_msg,
        )

    def get_document_chunks(
        self,
        case_id: UUID,
        document_id: UUID,
        db: Optional[Session] = None,
    ) -> DocumentChunkListResponse:
        """
        Returns deterministically ordered chunk list for a document in a case.
        """
        # Verify document exists in case
        repo_doc = self.repository.get(document_id, case_id)
        db_doc = None
        if db is not None:
            db_doc = (
                db.query(Document)
                .filter(Document.document_id == document_id, Document.case_id == case_id)
                .first()
            )

        if not repo_doc and not db_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        # Retrieve chunks from repository
        repo_chunks = self.repository.list_chunks(document_id)
        if repo_chunks:
            items = [
                DocumentChunkItem(
                    chunk_id=c.chunk_id,
                    version_id=c.version_id,
                    page_number=c.page_number,
                    character_span=c.character_span,
                    text_hash=c.text_hash,
                    storage_ref=c.storage_ref,
                )
                for c in repo_chunks
            ]
            return DocumentChunkListResponse(items=items, total=len(items))

        # Retrieve from DB if repository has none
        if db is not None:
            db_chunks = (
                db.query(DocumentChunk)
                .join(DocumentVersion, DocumentChunk.version_id == DocumentVersion.version_id)
                .filter(DocumentVersion.document_id == document_id)
                .order_by(DocumentChunk.page_number.asc(), DocumentChunk.chunk_id.asc())
                .all()
            )
            items = [
                DocumentChunkItem(
                    chunk_id=c.chunk_id,
                    version_id=c.version_id,
                    page_number=c.page_number,
                    character_span=c.character_span,
                    text_hash=c.text_hash,
                    storage_ref=c.storage_ref,
                )
                for c in db_chunks
            ]
            return DocumentChunkListResponse(items=items, total=len(items))

        return DocumentChunkListResponse(items=[], total=0)

    def archive_document(
        self,
        case_id: UUID,
        document_id: UUID,
        user: User,
        db: Optional[Session] = None,
    ) -> DocumentArchiveResponse:
        """
        Soft-deletes/archives a document by updating its status to REJECTED.
        Historical evidence records are strictly preserved.
        Audits DOCUMENT_DELETE.
        """
        repo_doc = self.repository.get(document_id, case_id)
        db_doc = None
        if db is not None:
            db_doc = (
                db.query(Document)
                .filter(Document.document_id == document_id, Document.case_id == case_id)
                .first()
            )

        if not repo_doc and not db_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        # Update in repository (lifecycle state management)
        if repo_doc:
            self.repository.archive_document(document_id, case_id)

        # Audit event (persisted in immutable audit_logs)
        if db is not None:
            record_security_event(
                db=db,
                action_code=SecurityAuditAction.DOCUMENT_DELETE,
                actor_uuid=user.user_id,
                case_id=case_id,
                target_item=f"DOCUMENT:{document_id}",
                outcome="SUCCESS",
            )
            db.commit()

        return DocumentArchiveResponse(
            document_id=document_id,
            case_id=case_id,
            status=DocumentState.REJECTED.value,
            archived_at=datetime.now(timezone.utc),
        )
