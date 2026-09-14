"""
Lightweight Asynchronous Document Worker for SIH26189.
Executes document task requests in the background using asyncio task management,
tracks job results, enforces idempotency, and avoids distributed queues (Celery/Kafka).
Conforms to the project's modular monolith architecture.
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, Optional, Set
from uuid import UUID

from backend.schemas.document_jobs import (
    DocumentState,
    DocumentTaskRequest,
    DocumentTaskResult,
)
from backend.services.document_pipeline import DocumentPipeline

logger = logging.getLogger("sih26189.backend.worker")


class DocumentWorker:
    """
    In-process async task worker managing document processing jobs.
    """

    def __init__(self, pipeline: DocumentPipeline):
        self.pipeline = pipeline
        self._jobs: Dict[UUID, DocumentTaskResult] = {}
        self._active_doc_ids: Set[UUID] = set()
        self._tasks: Dict[UUID, asyncio.Task] = {}

    def get_job(self, job_id: UUID) -> Optional[DocumentTaskResult]:
        """Retrieves the latest execution result or progress for a given job_id."""
        return self._jobs.get(job_id)

    async def execute_task(self, request: DocumentTaskRequest) -> DocumentTaskResult:
        """
        Executes a single document task request through the pipeline.
        Catches and records unhandled exceptions to prevent crashing the worker loop.
        """
        doc_id = request.document_id
        job_id = request.job_id
        case_id = request.case_id

        # Concurrency / Idempotency guard for simultaneous duplicate submissions
        if doc_id in self._active_doc_ids:
            logger.warning("Document %s is already actively processing. Skipping redundant concurrent run.", doc_id)
            existing_job = self._jobs.get(job_id)
            if existing_job:
                return existing_job
            return DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.PROCESSING,
                error_message="Document is currently being processed by another active task.",
                completed_at=None,
            )

        self._active_doc_ids.add(doc_id)
        # Mark initial processing state in job tracking
        self._jobs[job_id] = DocumentTaskResult(
            job_id=job_id,
            document_id=doc_id,
            case_id=case_id,
            status=DocumentState.RECEIVED,
            created_at=datetime.now(timezone.utc),
        )

        try:
            result = await self.pipeline.process_document_job(request)
            self._jobs[job_id] = result
            return result
        except Exception as exc:
            logger.error("Unhandled exception in document worker for job %s: %s", job_id, exc, exc_info=True)
            failure_result = DocumentTaskResult(
                job_id=job_id,
                document_id=doc_id,
                case_id=case_id,
                status=DocumentState.FAILED,
                error_message=f"Worker failure: {exc}",
                error_category="WORKER_EXCEPTION",
                completed_at=datetime.now(timezone.utc),
            )
            self._jobs[job_id] = failure_result
            return failure_result
        finally:
            self._active_doc_ids.discard(doc_id)

    def submit_job(self, request: DocumentTaskRequest) -> UUID:
        """
        Submits a document task request to execute asynchronously in the background.
        Returns the job_id immediately.
        """
        job_id = request.job_id
        task = asyncio.create_task(self.execute_task(request))
        self._tasks[job_id] = task
        return job_id

    async def wait_for_job(self, job_id: UUID, timeout: float = 30.0) -> Optional[DocumentTaskResult]:
        """
        Waits for a submitted background task to finish. Useful for integration testing.
        """
        task = self._tasks.get(job_id)
        if task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Job %s timed out waiting for completion.", job_id)
        return self.get_job(job_id)

    def clear(self) -> None:
        """Clears job tracker state."""
        self._jobs.clear()
        self._active_doc_ids.clear()
        self._tasks.clear()
