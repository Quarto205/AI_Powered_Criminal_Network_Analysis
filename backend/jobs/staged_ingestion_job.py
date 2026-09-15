"""
Asynchronous staging job for Phase 2.
Executes the staging of an Agent 1 payload within a database transaction,
along with security audit logging and document state management.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from agents.evidence.staging import stage_extraction_payload
from agents.extraction.schemas import ExtractionJobResponse
from backend.repositories.document_repository import DocumentRepository
from backend.security.audit import SecurityAuditAction, record_security_event
from backend.schemas.document_jobs import DocumentState

logger = logging.getLogger("sih26189.backend.staging_job")

class StagedIngestionJob:
    """
    Worker job that encapsulates the database transaction, staging logic,
    and audit logging for Agent 1 payload ingestion.
    """

    def __init__(self, session_factory: sessionmaker, repository: DocumentRepository):
        self.session_factory = session_factory
        self.repository = repository

    def execute_staging(
        self,
        payload: ExtractionJobResponse,
        case_id: UUID,
        document_id: UUID,
        actor_id: Optional[UUID] = None,
    ) -> bool:
        """
        Executes the staging in a single transaction.
        Returns True if successful, False if it failed.
        Updates the document state and logs audit events.
        """
        session = self.session_factory()
        try:
            # Execute Phase 3 Entity Resolution & Staging
            from agents.evidence.resolution import resolve_and_stage_payload
            batch_result = resolve_and_stage_payload(
                db_session=session,
                payload=payload,
                case_id=case_id,
                document_id=document_id,
                actor_id=actor_id,
            )
            
            # Commit the transaction to persist canonical relational records
            session.commit()

            # Update document state based on resolution results (ACCEPTED vs REVIEW_REQUIRED)
            if self.repository:
                try:
                    self.repository.update_status(
                        document_id=document_id,
                        case_id=case_id,
                        status=batch_result.recommended_doc_state,
                    )
                except Exception as status_err:
                    logger.warning("Could not update document state in repository: %s", status_err)
            
            # Audit success
            record_security_event(
                db=session,
                action_code="STAGING_SUCCESS",
                actor_uuid=actor_id,
                case_id=case_id,
                target_item=f"doc:{document_id}|job:{payload.extraction_job_id}|state:{batch_result.recommended_doc_state.value}",
                outcome="SUCCESS",
            )
            return True
            
        except Exception as exc:
            # Complete rollback of all partial records to maintain data integrity
            session.rollback()
            logger.error("Failed to stage extraction payload for document %s: %s", document_id, exc, exc_info=True)
            
            # Audit failure
            record_security_event(
                db=session,
                action_code="STAGING_FAILURE",
                actor_uuid=actor_id,
                case_id=case_id,
                target_item=f"doc:{document_id}|job:{payload.extraction_job_id}",
                outcome="FAILED",
            )
            
            # Re-raise to let the pipeline handle FAILED state transition
            raise
        finally:
            session.close()
