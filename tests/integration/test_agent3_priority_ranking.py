import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from backend.db.models.analytics import Alert, NetworkMetric, Prediction, RiskScore
from backend.db.models.entities import Entity, Relationship
from agents.intelligence.priority_engine import PriorityEngine
from backend.db.session import get_engine, get_session_factory
import os

POSTGRES_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:your_secure_postgres_password@localhost:5432/sih26189")

@pytest.fixture
def db_session():
    engine = get_engine(custom_url=POSTGRES_URL)
    session = get_session_factory(engine)()
    yield session
    session.close()

@pytest.fixture
def ranking_test_case(db_session):
    from backend.db.models.identity import Case, User
    user_id = uuid4()
    u = User(user_id=user_id, username=f"test_{uuid4().hex[:8]}", email=f"test{uuid4().hex[:8]}@test.com", password_hash="hash", account_status="ACTIVE")
    
    case_id = uuid4()
    c = Case(case_id=case_id, case_code=f"TC-{str(case_id)[:8]}", title="Test", status="OPEN", created_by=user_id, jurisdiction="TEST")
    db_session.add_all([u, c])
    db_session.flush()

    # Case A
    e1 = Entity(entity_id=uuid4(), case_id=case_id, entity_type="PERSON", canonical_name="E1", status="ACTIVE")
    e2 = Entity(entity_id=uuid4(), case_id=case_id, entity_type="PHONE", canonical_name="E2", status="ACTIVE")
    
    from backend.db.models.analytics import ModelRun
    run_id_1 = uuid4()
    mr1 = ModelRun(run_id=run_id_1, model_name="test", version="1", task_type="SNA", input_snapshot_checksum="")
    db_session.add(mr1)
    
    # SNA
    m1 = NetworkMetric(metric_id=uuid4(), run_id=run_id_1, case_id=case_id, target_entity_uuid=e1.entity_id, metric_type="degree_centrality", value=0.5)
    
    # Alert
    a1 = Alert(alert_id=uuid4(), case_id=case_id, alert_type="CYCLE", severity="HIGH", rule_id="1", contributing_entities={str(e1.entity_id): {}})
    
    run_id_2 = uuid4()
    mr2 = ModelRun(run_id=run_id_2, model_name="test2", version="1", task_type="GAT", input_snapshot_checksum="")
    db_session.add(mr2)

    # Prediction
    p1 = Prediction(prediction_id=uuid4(), run_id=run_id_2, case_id=case_id, source_ref=e1.entity_id, target_ref=e2.entity_id, predicted_relationship_type="ASSOCIATED", score=0.8, calibration="RAW", status="INFERRED")
    
    # Temporal
    r1 = Relationship(relationship_id=uuid4(), case_id=case_id, source_entity_uuid=e1.entity_id, target_entity_uuid=e2.entity_id, type="CALLS", status="OBSERVED", created_at=datetime.now(timezone.utc) - timedelta(days=2))

    db_session.add_all([e1, e2, m1, a1, p1, r1])
    db_session.commit()
    
    # Case B (Isolation Test)
    case_b_id = uuid4()
    c2 = Case(case_id=case_b_id, case_code=f"TC-{str(case_b_id)[:8]}", title="Test B", status="OPEN", created_by=user_id, jurisdiction="TEST")
    e3 = Entity(entity_id=uuid4(), case_id=case_b_id, entity_type="PERSON", canonical_name="E3", status="ACTIVE")
    # Massive alert that should NOT affect Case A
    a2 = Alert(alert_id=uuid4(), case_id=case_b_id, alert_type="CYCLE", severity="CRITICAL", rule_id="1", contributing_entities={str(e3.entity_id): {}})
    
    db_session.add_all([c2, e3, a2])
    db_session.commit()
    
    return case_id, e1.entity_id, e2.entity_id, case_b_id, e3.entity_id

def test_priority_ranking_integration_case_isolation(db_session, ranking_test_case):
    case_a_id, e1_id, e2_id, case_b_id, e3_id = ranking_test_case
    
    engine = PriorityEngine(db_session, case_a_id)
    scores = engine.run_priority_ranking()
    
    assert len(scores) == 2
    for score in scores:
        assert score.target_entity_uuid in [e1_id, e2_id]
        
    engine_b = PriorityEngine(db_session, case_b_id)
    scores_b = engine_b.run_priority_ranking()
    
    assert len(scores_b) == 1
    assert scores_b[0].target_entity_uuid == e3_id

def test_priority_ranking_end_to_end_calculation(db_session, ranking_test_case):
    case_a_id, e1_id, e2_id, _, _ = ranking_test_case
    
    engine = PriorityEngine(db_session, case_a_id)
    scores = engine.run_priority_ranking()
    
    # E1 should have higher score than E2
    e1_score = next(s for s in scores if s.target_entity_uuid == e1_id)
    e2_score = next(s for s in scores if s.target_entity_uuid == e2_id)
    
    assert e1_score.value > e2_score.value
    
    # Verify DB persistence
    # We query by run_id
    run_id = e1_score.run_id
    db_scores = db_session.query(RiskScore).filter(RiskScore.run_id == run_id).all()
    assert len(db_scores) == 2
