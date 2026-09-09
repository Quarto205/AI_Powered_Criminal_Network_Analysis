"""
Document Task Pipeline for SIH26189.
Orchestrates secure intake, security validation, OCR preprocessing,
Agent 1 intelligence extraction, provenance verification, and state transitions.

Canonical Workflow:
RECEIVED -> VALIDATED -> PROCESSING -> EXTRACTED -> (Ready for Agent 2)
Failure State: FAILED

Adheres strictly to AGENTS.md:
- No canonical graph or Neo4j writes (Agent 2 boundary).
- Full server-side case isolation.
- Preserves exact source spans: source_text[start:end] == extracted_text.
- Degraded operations & provider fallbacks preserved.
- Zero logging of unmasked PII, raw text, or secrets.
"""

from datetime import datetime, timezone
import hashlib
import logging
from typing import Optional
from uuid import UUID, uuid4

from agents.extraction.ocr.exceptions import (
    CorruptedFileError,
    EmptyDocumentError,
    OCREngineFailureError,
    PasswordProtectedError,
    PathTraversalError,
    ResourceLimitExceededError,
    UnsupportedFormatError,
)
from agents.extraction.ocr.preprocessor import OCRPreprocessor
from agents.extraction.ocr.schemas import (
    OCRDocumentResult,
    OCRProcessingStatus,
)
from agents.extraction.ocr.security import (
    DEFAULT_MAX_FILE_SIZE,
    validate_document_security,
)
from agents.extraction.parser import ExtractionEngine
from agents.extraction.schemas import ExtractionJobResponse
from backend.repositories.document_repository import (
    CaseIsolationViolationError,
    DocumentNotFoundError,
    DocumentRepository,
)
from backend.repositories.storage import BaseDocumentStorage, StorageError
from backend.schemas.document_jobs import (
    DocumentRecord,
    DocumentState,
    DocumentTaskRequest,
    DocumentTaskResult,
)

logger = logging.getLogger("sih26189.backend.pipeline")


class DocumentPipeline:
    """
    Central orchestration service for the document task pipeline.
    Connects binary validation, OCRPreprocessor, and Agent 1 ExtractionEngine.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        storage: BaseDocumentStorage,
        ocr_preprocessor: Optional[OCRPreprocessor] = None,
        extraction_engine: Optional[ExtractionEngine] = None,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    ):
        self.repository = repository
        self.storage = storage
        self.ocr_preprocessor = ocr_preprocessor or OCRPreprocessor()
        self.extraction_engine = extraction_engine or ExtractionEngine()
        self.max_file_size = max_file_size

    def _log_audit_event(
        self,
        action: str,
        case_id: UUID,
        document_id: UUID,
        outcome: str,
        actor_id: Optional[UUID] = None,
        details: Optional[str] = None,
    ) -> None:
        """
        Logs a sanitized operational audit event.
        Never logs full document text, unmasked PII, or secrets.
        """
        logger.info(
            "AUDIT: action=%s, case_id=%s, document_id=%s, actor=%s, outcome=%s, details=%s",
            action,
            case_id,
            document_id,
            actor_id or "SYSTEM",
            outcome,
            details or "OK",
        )

    async def process_document_job(self, request: DocumentTaskRequest) -> DocumentTaskResult:
        """
        Executes the end-to-end document processing pipeline asynchronously.
        Steps:
        1. Case Isolation Verification
        2. Binary Retrieval from Storage
        3. Sanitization & Security Validation (RECEIVED -> VALIDATED)
        4. Parsing & OCR Preprocessing (VALIDATED -> PROCESSING)
        5. Agent 1 NLP Intelligence Extraction
        6. Provenance & Offset Integrity Verification (PROCESSING -> EXTRACTED)
        7. State Persistence & Audit Event
        """
        start_time = datetime.now(timezone.utc)
        doc_id = request.document_id
        case_id = request.case_id
        job_id = request.job_id
        actor_id = request.caller_user_id

        # ----------------------------------------------------------------------
        # 1. CASE ISOLATION & AUTHORIZATION CHECK
        # ----------------------------------------------------------------------
        if actor_id is not None:
            if not self.repository.check_user_access(actor_id, case_id):
                self._log_audit_event(
                    action="CASE_AUTHORIZATION_CHECK",
                    case_id=case_id,
                    document_id=doc_id,
                    outcome="DENIED",
                    actor_id=actor_id,
                    details="Caller is not a member of the requested case.",
                )
                raise CaseIsolationViolationError(
                    f"User {actor_id} is unauthorized to access or process documents in case {case_id}."
                )

        # Verify document existence and case alignment in repository
        doc_record = self.repository.get(doc_id, case_id)
        if doc_record is None:
            # Check if document exists in ANY other case to prevent case traversal
            # per 06_WORKFLOWS.md Section 6.2 (return generic not found)
            raise DocumentNotFoundError(f"Document {doc_id} not found in case {case_id}.")

        if doc_record.case_id != case_id:
            raise CaseIsolationViolationError(
                f"Cross-case access rejected: document belongs to case {doc_record.case_id}, requested {case_id}."
            )

        # Idempotency check: if document is already EXTRACTED, return existing result safely
        if doc_record.status == DocumentState.EXTRACTED and doc_record.extraction_job_id:
            existing_result = self.repository.get_extraction_result(doc_id)
            if existing_result:
                logger.info(
                    "Document %s in case %s is already EXTRACTED. Returning idempotent cached result.",
                    doc_id,
                    case_id,
                )
                return DocumentTaskResult(
                    job_id=job_id,
                    document_id=doc_id,
                    case_id=case_id,
                    status=DocumentState.EXTRACTED,
                    full_text=existing_result.get("full_text"),
                    extraction_result=ExtractionJobResponse.model_validate(existing_result["extraction"]),
                    completed_at=datetime.now(timezone.utc),
                )

        # ----------------------------------------------------------------------
        # 2. RETRIEVE DOCUMENT BINARY BYTES FROM STORAGE
        # ----------------------------------------------------------------------
        storage_key = request.storage_key or doc_record.storage_key
        try:
            data = self.storage.get(storage_key)
        except StorageError as exc:
            logger.error("Failed to retrieve document %s from storage key '%s': %s", doc_id, storage_key, exc)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=f"Storage retrieval failed: {exc}",
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=f"Storage retrieval failed: {exc}",
                error_category="STORAGE_ERROR",
                completed_at=datetime.now(timezone.utc),
            )

        # ----------------------------------------------------------------------
        # 3. SECURITY VALIDATION & SANITIZATION (RECEIVED -> VALIDATED)
        # ----------------------------------------------------------------------
        self.repository.update_status(document_id=doc_id, case_id=case_id, status=DocumentState.RECEIVED)

        try:
            val_res = validate_document_security(
                data=data,
                original_filename=request.filename,
                max_file_size=self.max_file_size,
            )
            if not val_res.is_valid:
                logger.warning("Security validation rejected document %s: %s", doc_id, val_res.error_message)
                self.repository.update_status(
                    document_id=doc_id,
                    case_id=case_id,
                    status=DocumentState.FAILED,
                    error_message=val_res.error_message,
                )
                return DocumentTaskResult(
                    job_id=job_id,
                    document_id=doc_id,
                    case_id=case_id,
                    status=DocumentState.FAILED,
                    error_message=val_res.error_message,
                    error_category="SECURITY_VALIDATION_FAILED",
                    completed_at=datetime.now(timezone.utc),
                )
        except (UnsupportedFormatError, ResourceLimitExceededError, PathTraversalError) as exc:
            logger.warning("Security boundary error for document %s: %s", doc_id, exc)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=str(exc),
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=str(exc),
                error_category="SECURITY_BOUNDARY_VIOLATION",
                completed_at=datetime.now(timezone.utc),
            )

        # Security check passed -> transition to VALIDATED
        self.repository.update_status(document_id=doc_id, case_id=case_id, status=DocumentState.VALIDATED)

        # ----------------------------------------------------------------------
        # 4. PARSING & OCR PREPROCESSING (VALIDATED -> PROCESSING)
        # ----------------------------------------------------------------------
        self.repository.update_status(document_id=doc_id, case_id=case_id, status=DocumentState.PROCESSING)

        try:
            ocr_result = self.ocr_preprocessor.process_document(
                data=data,
                original_filename=request.filename,
                document_id=doc_id,
            )
        except Exception as exc:
            logger.error("Unexpected error in OCRPreprocessor for document %s: %s", doc_id, exc, exc_info=True)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=f"OCR processing failed: {exc}",
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=f"OCR processing failed: {exc}",
                error_category="OCR_ERROR",
                completed_at=datetime.now(timezone.utc),
            )

        # Check OCR Result Status
        if ocr_result.status == OCRProcessingStatus.EMPTY_DOCUMENT:
            logger.warning("Document %s contains empty/whitespace-only text. Terminating pipeline.", doc_id)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message="Document contains no extractable text.",
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                detected_type=ocr_result.detected_type.value,
                total_pages=ocr_result.total_pages,
                ocr_result=ocr_result,
                error_message="Document contains no extractable text.",
                error_category=OCRProcessingStatus.EMPTY_DOCUMENT.value,
                completed_at=datetime.now(timezone.utc),
            )

        if ocr_result.status != OCRProcessingStatus.SUCCESS:
            logger.warning("OCR failed for document %s with status %s: %s", doc_id, ocr_result.status, ocr_result.error_message)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=ocr_result.error_message or "OCR extraction failed.",
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                detected_type=ocr_result.detected_type.value,
                total_pages=ocr_result.total_pages,
                ocr_result=ocr_result,
                error_message=ocr_result.error_message or "OCR extraction failed.",
                error_category=ocr_result.status.value,
                completed_at=datetime.now(timezone.utc),
            )

        if not ocr_result.full_text or not ocr_result.full_text.strip():
            logger.warning("OCR returned success but empty text for document %s.", doc_id)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message="Document text is empty after preprocessing.",
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                detected_type=ocr_result.detected_type.value,
                total_pages=ocr_result.total_pages,
                ocr_result=ocr_result,
                error_message="Document text is empty after preprocessing.",
                error_category=OCRProcessingStatus.EMPTY_DOCUMENT.value,
                completed_at=datetime.now(timezone.utc),
            )

        # ----------------------------------------------------------------------
        # 5. AGENT 1 NLP INTELLIGENCE EXTRACTION
        # ----------------------------------------------------------------------
        extraction_job_id = uuid4()
        agent1_req = self.ocr_preprocessor.to_agent1_request(ocr_result)

        try:
            extraction_response = await self.extraction_engine.extract(
                text=agent1_req.text,
                job_id=extraction_job_id,
                metadata=agent1_req.metadata,
            )
        except Exception as exc:
            logger.error("Agent 1 extraction failed for document %s: %s", doc_id, exc, exc_info=True)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=f"Agent 1 extraction failed: {exc}",
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                detected_type=ocr_result.detected_type.value,
                total_pages=ocr_result.total_pages,
                full_text=ocr_result.full_text,
                ocr_result=ocr_result,
                error_message=f"Agent 1 extraction failed: {exc}",
                error_category="EXTRACTION_FAILED",
                completed_at=datetime.now(timezone.utc),
            )

        # ----------------------------------------------------------------------
        # 6. PROVENANCE & CHARACTER OFFSET INTEGRITY VERIFICATION
        # ----------------------------------------------------------------------
        try:
            extraction_response.verify_source_spans(ocr_result.full_text)
        except Exception as exc:
            logger.error("Provenance verification failed for document %s: %s", doc_id, exc)
            self.repository.update_status(
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=f"Provenance offset verification failed: {exc}",
            )
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                detected_type=ocr_result.detected_type.value,
                total_pages=ocr_result.total_pages,
                full_text=ocr_result.full_text,
                ocr_result=ocr_result,
                error_message=f"Provenance offset verification failed: {exc}",
                error_category="PROVENANCE_ERROR",
                completed_at=datetime.now(timezone.utc),
            )

        # ----------------------------------------------------------------------
        # 7. STATE TRANSITION TO EXTRACTED & AUDIT EVENT
        # ----------------------------------------------------------------------
        self.repository.update_status(
            document_id=doc_id,
            case_id=case_id,
            status=DocumentState.EXTRACTED,
            extraction_job_id=extraction_job_id,
        )

        # Create immutable document version
        version_hash = hashlib.sha256(ocr_result.full_text.encode("utf-8")).hexdigest()
        version = self.repository.create_version(
            document_id=doc_id,
            version_hash=version_hash,
            metadata={
                "total_pages": ocr_result.total_pages,
                "detected_type": ocr_result.detected_type.value,
                "entities_count": len(extraction_response.extracted_entities),
                "relations_count": len(extraction_response.extracted_relationships),
            },
        )

        # Create ordered document chunks from OCR pages
        for page in ocr_result.pages:
            page_text = page.text or ""
            page_hash = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
            span_str = f"{page.character_start}:{page.character_end}"
            storage_ref = f"{doc_record.storage_key}#page={page.page_number}"
            self.repository.create_chunk(
                version_id=version.version_id,
                document_id=doc_id,
                page_number=page.page_number,
                character_span=span_str,
                text_hash=page_hash,
                storage_ref=storage_ref,
            )

        # Store validated extraction for downstream Agent 2 access
        self.repository.save_extraction_result(
            document_id=doc_id,
            result_dict={
                "extraction_job_id": str(extraction_job_id),
                "full_text": ocr_result.full_text,
                "extraction": extraction_response.model_dump(),
            },
        )

        self._log_audit_event(
            action="DOCUMENT_EXTRACTED",
            case_id=case_id,
            document_id=doc_id,
            actor_id=actor_id,
            outcome="SUCCESS",
            details=f"Extracted {len(extraction_response.extracted_entities)} entities, {len(extraction_response.extracted_relationships)} relations.",
        )

        completed_at = datetime.now(timezone.utc)
        return DocumentTaskResult(
            job_id=job_id,
            document_id=doc_id,
            case_id=case_id,
            status=DocumentState.EXTRACTED,
            detected_type=ocr_result.detected_type.value,
            total_pages=ocr_result.total_pages,
            full_text=ocr_result.full_text,
            ocr_result=ocr_result,
            extraction_result=extraction_response,
            created_at=start_time,
            completed_at=completed_at,
        )
