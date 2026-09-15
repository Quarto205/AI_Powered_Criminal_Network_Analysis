"""
Agent 2 Phase 7: Regression Pipeline Test (Idempotency & Rebuildability)
Verifies the GraphSyncWorker is idempotent and the graph can be completely rebuilt.
"""
import pytest
import uuid
import time
from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.db.models.identity import Case, CaseMember, User
from backend.jobs.graph_sync_worker import GraphSyncWorker
from backend.services.graph_projection import GraphProjectionService
from backend.repositories.neo4j_repository import Neo4jRepository
from scripts.seed_demo import seed_demo_data

# Deterministic test namespace
REGRESSION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "sih26189.regression_test")
USER_ID = uuid.uuid5(REGRESSION_NAMESPACE, "user:regression_tester")

@pytest.fixture(scope="module")
def regression_db_session():
    db = SessionLocal()
    # Ensure test user
    user = db.query(User).filter(User.user_id == USER_ID).first()
    if not user:
        user = User(
            user_id=USER_ID,
            email="regression@sih.synthetic",
            username="regression",
            password_hash="fake",
            account_status="ACTIVE"
        )
        db.add(user)
        db.commit()

    # Create canonical deterministic data using the real demo seeder
    # Note: seed_demo_data itself uses SessionLocal which connects to the same DB
    case_id, _ = seed_demo_data()
    
    yield db, case_id
    
    # Cleanup case and graph projection
    service = GraphProjectionService(db=db)
    with service.graph_manager.get_session() as session:
        session.run("MATCH (n {case_id: $case_id}) DETACH DELETE n", case_id=str(case_id))
    
    # Let DB handle case data or wipe case data correctly if needed.
    # To avoid fk restrict violations, we just skip deleting the case.
    db.commit()
    db.close()


def test_regression_idempotency_and_rebuild(regression_db_session):
    db, case_id = regression_db_session
    repo = Neo4jRepository()
    
    def get_counts():
        with repo.graph_manager.get_session() as session:
            n = session.run("MATCH (n {case_id: $case_id}) RETURN count(n) as c", case_id=str(case_id)).single()["c"]
            r = session.run("MATCH ()-[r {case_id: $case_id}]->() RETURN count(r) as c", case_id=str(case_id)).single()["c"]
        return n, r

    # RUN 1: Initial Projection
    worker1 = GraphSyncWorker(db_session_factory=SessionLocal)
    worker1._run_projection_sync(case_id)
    
    nodes_run1, edges_run1 = get_counts()
    
    # Check that *something* was projected
    assert nodes_run1 > 0
    assert edges_run1 > 0
    
    # RUN 2: Idempotency Projection
    worker2 = GraphSyncWorker(db_session_factory=SessionLocal)
    worker2._run_projection_sync(case_id)
    
    nodes_run2, edges_run2 = get_counts()
    
    # IDEMPOTENCY INVARIANT: Counts must exactly match, no duplicates created.
    assert nodes_run1 == nodes_run2
    assert edges_run1 == edges_run2
    
    # TASK 4: REBUILDABILITY
    # Safely clear the graph ONLY for this case
    with repo.graph_manager.get_session() as session:
        session.run("MATCH (n {case_id: $case_id}) DETACH DELETE n", case_id=str(case_id))
        
    nodes_cleared, edges_cleared = get_counts()
    assert nodes_cleared == 0
    assert edges_cleared == 0
    
    # Execute Rebuild
    service = GraphProjectionService(db=db)
    result = service.rebuild_case_graph(case_id)
    assert "checksum" in result
    
    nodes_rebuilt, edges_rebuilt = get_counts()
    
    # REBUILDABILITY INVARIANT: Counts must exactly match the original projection
    assert nodes_rebuilt == nodes_run1
    assert edges_rebuilt == edges_run1
