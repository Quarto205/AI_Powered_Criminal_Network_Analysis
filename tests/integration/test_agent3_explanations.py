import pytest
import json
from uuid import uuid4
from datetime import datetime, timezone

from backend.db.models.analytics import RiskScore, Explanation, ModelRun
from backend.db.models.entities import Entity
from agents.intelligence.explanation_engine import ExplanationEngine
from agents.extraction.providers import MockDeterministicProvider
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
def explanation_test_case(db_session):
    from backend.db.models.identity import Case, User
    user_id = uuid4()
    u = User(user_id=user_id, username=f"test_{uuid4().hex[:8]}", email=f"test{uuid4().hex[:8]}@test.com", password_hash="hash", account_status="ACTIVE")
    
    case_id = uuid4()
    c = Case(case_id=case_id, case_code=f"TC-{str(case_id)[:8]}", title="Test", status="OPEN", created_by=user_id, jurisdiction="TEST")
    db_session.add_all([u, c])
    db_session.flush()

    run_id = uuid4()
    
    mr = ModelRun(run_id=run_id, model_name="PriorityEngine", version="1.0", task_type="RANKING", input_snapshot_checksum="N/A")
    e1 = Entity(entity_id=uuid4(), case_id=case_id, entity_type="PERSON", canonical_name="E1", status="ACTIVE")
    db_session.add_all([mr, e1])
    
    rs = RiskScore(
        score_id=uuid4(),
        target_entity_uuid=e1.entity_id,
        run_id=run_id,
        score_type="PRIORITY_RANKING",
        value=0.75,
        features_summary={
            "components": {},
            "contributions": {"sna_centrality": 0.25, "alert_severity": 0.25}
        }
    )
    db_session.add(rs)
    db_session.commit()
    return case_id, rs

@pytest.mark.asyncio
async def test_explanation_engine_valid_llm_output(db_session, explanation_test_case):
    case_id, risk_score = explanation_test_case
    
    valid_json = {
        "summary": "High priority",
        "top_contributors": ["SNA"],
        "evidence_context": "2 alerts",
        "model_context": "GATv2",
        "confidence_semantics": "Scores are not guilt.",
        "limitations": "Incomplete data",
        "human_review_note": "For review"
    }
    
    provider = MockDeterministicProvider(canned_response=json.dumps(valid_json))
    engine = ExplanationEngine(db_session, provider)
    
    exp = await engine.async_generate_explanation(risk_score, case_id)
    
    assert exp.provider_type == "LLM"
    assert "High priority" in exp.explanation_text
    
@pytest.mark.asyncio
async def test_explanation_engine_jinja2_fallback_on_provider_error(db_session, explanation_test_case):
    case_id, risk_score = explanation_test_case
    
    provider = MockDeterministicProvider(should_fail=True)
    engine = ExplanationEngine(db_session, provider)
    
    exp = await engine.async_generate_explanation(risk_score, case_id)
    
    assert exp.provider_type == "TEMPLATE"
    assert "Investigative Lead" in exp.explanation_text
    assert "25.0" in exp.explanation_text  # Feature contribution
    assert "guilt" not in exp.explanation_text.lower()
