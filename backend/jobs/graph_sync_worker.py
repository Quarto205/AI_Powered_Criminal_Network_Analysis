"""
Lightweight Asynchronous Graph Sync Worker for SIH26189.
Executes graph projection in the background using asyncio task management.
Guarantees PostgreSQL transaction decoupling from Neo4j.
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, Optional, Set
from uuid import UUID

from backend.services.graph_projection import GraphProjectionService, GraphProjectionError
from sqlalchemy.orm import Session

logger = logging.getLogger("sih26189.backend.graph_sync_worker")


class GraphSyncWorker:
    """
    In-process async task worker managing Neo4j graph projection jobs.
    """

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self._active_case_ids: Set[UUID] = set()
        self._tasks: Dict[UUID, asyncio.Task] = {}
        self._results: Dict[UUID, Dict] = {}

    async def execute_task(self, case_id: UUID) -> Dict:
        """
        Executes a case rebuild task request through the graph projection service.
        Catches and records unhandled exceptions to prevent crashing the worker loop.
        Uses asyncio.to_thread to avoid blocking the event loop with synchronous DB calls.
        """
        if case_id in self._active_case_ids:
            logger.warning(f"Case {case_id} is already actively projecting. Skipping redundant concurrent run.")
            return {"status": "SKIPPED", "case_id": str(case_id)}

        self._active_case_ids.add(case_id)
        
        try:
            # We run the synchronous projection in a separate thread
            result = await asyncio.to_thread(self._run_projection_sync, case_id)
            self._results[case_id] = result
            return result
        except Exception as exc:
            logger.error(f"Unhandled exception in graph sync worker for case {case_id}: {exc}", exc_info=True)
            failure_result = {
                "status": "FAILED",
                "case_id": str(case_id),
                "error": str(exc)
            }
            self._results[case_id] = failure_result
            return failure_result
        finally:
            self._active_case_ids.discard(case_id)
            
    def _run_projection_sync(self, case_id: UUID) -> Dict:
        """Synchronous wrapper to get a new DB session and run the projection."""
        db: Session = self.db_session_factory()
        try:
            service = GraphProjectionService(db=db)
            result = service.rebuild_case_graph(case_id)
            result["status"] = "SUCCESS"
            return result
        except GraphProjectionError as e:
            logger.warning(f"Graph projection skipped for case {case_id}: {e}")
            return {"status": "OFFLINE", "case_id": str(case_id), "error": str(e)}
        finally:
            db.close()

    def submit_job(self, case_id: UUID) -> asyncio.Task:
        """
        Submits a graph sync request to execute asynchronously in the background.
        Returns the task immediately.
        """
        task = asyncio.create_task(self.execute_task(case_id))
        self._tasks[case_id] = task
        return task

    async def wait_for_job(self, case_id: UUID, timeout: float = 30.0) -> Optional[Dict]:
        """
        Waits for a submitted background task to finish. Useful for integration testing.
        """
        task = self._tasks.get(case_id)
        if task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Graph sync for case {case_id} timed out waiting for completion.")
        return self._results.get(case_id)

    def clear(self) -> None:
        """Clears job tracker state."""
        self._active_case_ids.clear()
        self._tasks.clear()
        self._results.clear()
