"""
Phase 5 Tests: Asynchronous Graph Synchronization Worker and Bridge.
Validates:
- Worker executes synchronously in a separate thread.
- Worker intercepts Neo4j offline errors without failing PostgreSQL transaction.
- Bridge correctly submits jobs.
- Duplicate case rebuilds are skipped when one is active.
"""

import pytest
import asyncio
from uuid import uuid4

from backend.jobs.graph_sync_worker import GraphSyncWorker
from backend.jobs.graph_worker_bridge import GraphWorkerBridge
from backend.services.graph_projection import GraphProjectionError

# Mock DB Session factory
class MockDBSessionFactory:
    def __call__(self):
        return MockSession()

class MockSession:
    def close(self):
        pass

@pytest.fixture
def worker():
    return GraphSyncWorker(db_session_factory=MockDBSessionFactory())

@pytest.fixture
def bridge(worker):
    return GraphWorkerBridge(worker=worker)


@pytest.mark.asyncio
async def test_worker_bridge_submits_job(bridge, worker, monkeypatch):
    case_id = uuid4()
    
    # Mock the internal sync function to avoid actual DB/Neo4j calls
    def mock_run_sync(cid):
        return {"nodes_projected": 10, "edges_projected": 5, "checksum": "abc"}
    
    monkeypatch.setattr(worker, "_run_projection_sync", mock_run_sync)
    
    bridge.submit_sync_job(case_id)
    
    # Wait for the task
    result = await worker.wait_for_job(case_id)
    
    assert result is not None
    assert result["nodes_projected"] == 10
    assert result["edges_projected"] == 5


@pytest.mark.asyncio
async def test_worker_skips_concurrent_jobs(worker, monkeypatch):
    case_id = uuid4()
    
    async def slow_sync(cid):
        await asyncio.sleep(0.5)
        return {"status": "SUCCESS"}
        
    # Manually patch execute_task to simulate slow execution
    monkeypatch.setattr(asyncio, "to_thread", lambda f, c: slow_sync(c))
    
    task1 = worker.submit_job(case_id)
    task2 = worker.submit_job(case_id)
    
    res2 = await task2
    assert res2["status"] == "SKIPPED"
    
    res1 = await task1
    assert res1["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_worker_handles_neo4j_offline(worker, monkeypatch):
    case_id = uuid4()
    
    def offline_sync(self, cid):
        raise GraphProjectionError("Neo4j analytical database is currently unavailable.")
        
    from backend.services.graph_projection import GraphProjectionService
    monkeypatch.setattr(GraphProjectionService, "rebuild_case_graph", offline_sync)
    
    worker.submit_job(case_id)
    result = await worker.wait_for_job(case_id)
    
    # Must not raise an exception to the caller (PostgreSQL transaction decoupled)
    assert result["status"] == "OFFLINE"
    assert "unavailable" in result["error"]
