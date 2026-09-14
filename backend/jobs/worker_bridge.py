"""
Worker Bridge for SIH26189.
Connects the FastAPI ingestion layer to the asynchronous in-process DocumentWorker.
Provides clean decoupling, guarantees non-blocking job dispatch (HTTP 202 Accepted),
and enforces stable UUID-v4 job tracking.
"""

from typing import Optional
from uuid import UUID, uuid4

from backend.jobs.document_worker import DocumentWorker
from backend.schemas.document_jobs import DocumentTaskRequest


class WorkerBridge:
    """
    Bridge service for submitting document processing tasks to DocumentWorker
    without blocking the calling HTTP request thread.
    """

    def __init__(self, worker: DocumentWorker):
        self.worker = worker

    def submit_document_job(
        self,
        document_id: UUID,
        case_id: UUID,
        filename: str,
        storage_key: str,
        caller_user_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
    ) -> UUID:
        """
        Dispatches a document task request to the worker in the background.
        Returns the assigned job_id immediately.
        """
        resolved_job_id = job_id or uuid4()
        task_request = DocumentTaskRequest(
            job_id=resolved_job_id,
            document_id=document_id,
            case_id=case_id,
            filename=filename,
            storage_key=storage_key,
            caller_user_id=caller_user_id,
        )
        return self.worker.submit_job(task_request)
