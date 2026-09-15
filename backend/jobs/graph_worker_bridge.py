"""
Graph Worker Bridge for SIH26189.
Connects the ingestion layer to the asynchronous GraphSyncWorker.
Provides clean decoupling for non-blocking Neo4j synchronization.
"""

from uuid import UUID
from backend.jobs.graph_sync_worker import GraphSyncWorker

class GraphWorkerBridge:
    def __init__(self, worker: GraphSyncWorker):
        self.worker = worker

    def submit_sync_job(self, case_id: UUID) -> None:
        """
        Dispatches a graph sync request to the worker in the background.
        """
        self.worker.submit_job(case_id)
