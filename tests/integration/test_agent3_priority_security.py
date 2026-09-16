import pytest
import json
from uuid import uuid4
from fastapi.testclient import TestClient

from apps.api.routers.intelligence import router as intelligence_router
from agents.intelligence.explanation_engine import ExplanationEngine, FORBIDDEN_TERMS
from agents.extraction.providers import MockDeterministicProvider
from backend.db.models.analytics import RiskScore, Explanation, ModelRun
from backend.db.models.entities import Entity, Relationship
from backend.db.models.identity import Case, User
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
def security_test_case(db_session):
    case_id = uuid4()
    run_id = uuid4()
    user_id = uuid4()
    
    # Needs valid Case, User, Entity for API tests if we mock the auth.
    c = Case(case_id=case_id, case_code=f"TC-{str(case_id)[:8]}", title="Test", status="OPEN", created_by=user_id, jurisdiction="TEST")
    u = User(user_id=user_id, username=f"test_inv_{uuid4().hex[:8]}", email=f"test{user_id}@test.com", password_hash="hash", account_status="ACTIVE")
    
    mr = ModelRun(run_id=run_id, model_name="PriorityEngine", version="1.0", task_type="RANKING", input_snapshot_checksum="N/A")
    e1 = Entity(entity_id=uuid4(), case_id=case_id, entity_type="PERSON", canonical_name="E1", status="ACTIVE")
    
    db_session.add_all([c, u, mr, e1])
    
    rs = RiskScore(
        score_id=uuid4(),
        target_entity_uuid=e1.entity_id,
        run_id=run_id,
        score_type="PRIORITY_RANKING",
        value=0.75,
        features_summary={"components": {}, "contributions": {}}
    )
    db_session.add(rs)
    db_session.commit()
    return case_id, rs

@pytest.mark.asyncio
async def test_explanation_engine_rejects_forbidden_terminology(db_session, security_test_case):
    case_id, risk_score = security_test_case
    
    # LLM hallucinates forbidden word
    malicious_json = {
        "summary": "Entity has high probability of guilt.",
        "top_contributors": [],
        "evidence_context": "",
        "model_context": "",
        "confidence_semantics": "",
        "limitations": "",
        "human_review_note": ""
    }
    
    provider = MockDeterministicProvider(canned_response=json.dumps(malicious_json))
    engine = ExplanationEngine(db_session, provider)
    
    exp = await engine.async_generate_explanation(risk_score, case_id)
    
    # Must fallback to TEMPLATE because of forbidden terms
    assert exp.provider_type == "TEMPLATE"
    for term in FORBIDDEN_TERMS:
        assert term not in exp.explanation_text.lower()
