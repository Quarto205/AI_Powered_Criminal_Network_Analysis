import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import os

from backend.db.session import get_engine, get_session_factory
from backend.db.models.identity import Case, User
from backend.db.models.entities import Entity, Transaction, Communication, Event
from backend.db.models.analytics import Alert
from agents.intelligence.temporal import validate_timestamps, safe_time_difference_hours, TemporalSafetyError, INSUFFICIENT_TEMPORAL_DATA
from agents.intelligence.pattern_engine import PatternEngine
from backend.repositories.alert_repository import AlertRepository

POSTGRES_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:your_secure_postgres_password@localhost:5432/sih26189"
)

@pytest.fixture(scope="module")
def db_session():
    engine = get_engine(custom_url=POSTGRES_URL)
    session = get_session_factory(engine)()
    yield session
    session.close()

@pytest.fixture
def test_case_id(db_session: Session):
    user_id = uuid4()
    u = User(user_id=user_id, email=f"test{user_id}@test.com", username=f"user{user_id}", password_hash="dummy")
    db_session.add(u)
    db_session.flush()

    case_id = uuid4()
    c = Case(
        case_id=case_id, 
        case_code=f"TC-{str(case_id)[:8]}", 
        title="Test Pattern Case", 
        status="OPEN", 
        description="For testing",
        jurisdiction="TEST",
        created_by=user_id
    )
    db_session.add(c)
    db_session.commit()
    return case_id

@pytest.fixture
def setup_pattern_data(db_session: Session, test_case_id):
    # Create Entities
    e1_id = uuid4()
    e2_id = uuid4()
    e3_id = uuid4()
    e4_id = uuid4()
    e5_id = uuid4()
    e6_id = uuid4()
    
    e1 = Entity(entity_id=e1_id, case_id=test_case_id, canonical_name="E1", entity_type="PERSON")
    e2 = Entity(entity_id=e2_id, case_id=test_case_id, canonical_name="E2", entity_type="PERSON")
    e3 = Entity(entity_id=e3_id, case_id=test_case_id, canonical_name="E3", entity_type="PERSON")
    e4 = Entity(entity_id=e4_id, case_id=test_case_id, canonical_name="E4", entity_type="PERSON")
    e5 = Entity(entity_id=e5_id, case_id=test_case_id, canonical_name="E5", entity_type="PERSON")
    e6 = Entity(entity_id=e6_id, case_id=test_case_id, canonical_name="E6", entity_type="PERSON")
    
    db_session.add_all([e1, e2, e3, e4, e5, e6])
    db_session.commit()
    
    # Create Transaction Cycle: E1 -> E2 -> E3 -> E1
    t1 = datetime.now(timezone.utc) - timedelta(hours=5)
    t2 = t1 + timedelta(hours=1)
    t3 = t2 + timedelta(hours=1)
    
    tx1 = Transaction(transaction_id=uuid4(), sender_ref=e1_id, receiver_ref=e2_id, amount=100.0, currency="USD", channel="BANK", time=t1)
    tx2 = Transaction(transaction_id=uuid4(), sender_ref=e2_id, receiver_ref=e3_id, amount=100.0, currency="USD", channel="BANK", time=t2)
    tx3 = Transaction(transaction_id=uuid4(), sender_ref=e3_id, receiver_ref=e1_id, amount=100.0, currency="USD", channel="BANK", time=t3)
    
    db_session.add_all([tx1, tx2, tx3])
    
    # Create Fan-Out: E4 -> E1, E2, E3, E5, E6 (to meet degree=5 threshold) within short window
    t4 = datetime.now(timezone.utc) - timedelta(hours=1)
    for rec in [e1_id, e2_id, e3_id, e5_id, e6_id]:
        db_session.add(Transaction(transaction_id=uuid4(), sender_ref=e4_id, receiver_ref=rec, amount=50.0, currency="USD", channel="BANK", time=t4))
        t4 += timedelta(minutes=5)
            
    # Create Communication Burst
    inc_time = datetime.now(timezone.utc) - timedelta(hours=10)
    db_session.add(Event(event_id=uuid4(), case_id=test_case_id, event_type="ARREST", timestamp=inc_time))
    
    # Burst 10 comms right after
    burst_time = inc_time + timedelta(minutes=10)
    for _ in range(12):
        db_session.add(Communication(communication_id=uuid4(), caller_ref=e1_id, receiver_ref=e2_id, timestamps=burst_time, channel="SMS"))
        burst_time += timedelta(minutes=1)
        
    db_session.commit()
    return test_case_id, e1_id, e2_id, e3_id, e4_id

def test_temporal_safety():
    # Valid
    ts1 = datetime.now(timezone.utc)
    ts2 = ts1 + timedelta(hours=2)
    valid = validate_timestamps([ts1, ts1.isoformat(), ts2])
    assert len(valid) == 3
    assert safe_time_difference_hours(valid[0], valid[2]) == 2.0
    
    # Missing/null
    with pytest.raises(TemporalSafetyError) as exc:
        validate_timestamps([ts1, None])
    assert str(exc.value) == INSUFFICIENT_TEMPORAL_DATA
    
    # Unparseable
    with pytest.raises(TemporalSafetyError) as exc:
        validate_timestamps([ts1, "2024-invalid"])
    assert str(exc.value) == INSUFFICIENT_TEMPORAL_DATA
    
    # Out of order difference
    with pytest.raises(TemporalSafetyError):
        safe_time_difference_hours(ts2, ts1)

def test_pattern_engine_e2e(db_session: Session, setup_pattern_data):
    case_id, *_ = setup_pattern_data
    
    engine = PatternEngine(db_session)
    result = engine.run_all_detectors(case_id)
    
    assert result["total_candidates"] > 0
    assert result["new_alerts_persisted"] > 0
    
    repo = AlertRepository(db_session)
    alerts = repo.list_case_alerts(case_id)
    
    # Should have TX_CYCLE, RAPID_FAN_OUT, COMMUNICATION_BURST
    alert_types = [a.alert_type for a in alerts]
    assert "TRANSACTION_CYCLE" in alert_types
    assert "RAPID_FAN_OUT" in alert_types
    assert "COMMUNICATION_BURST" in alert_types
    
    # Test idempotency
    result_dup = engine.run_all_detectors(case_id)
    assert result_dup["new_alerts_persisted"] == 0
    
    alerts_after = repo.list_case_alerts(case_id)
    assert len(alerts_after) == len(alerts)
