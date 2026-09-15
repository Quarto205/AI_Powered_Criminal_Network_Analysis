import pytest
from uuid import uuid4
from backend.db.models.entities import Relationship, RelationshipEvidenceState, Entity
from backend.db.models.analytics import AuditLog
from agents.evidence.provenance import register_relationship_evidence, get_independent_source_key

@pytest.fixture
def db_session():
    import os
    from backend.db.session import get_engine, get_session_factory
    from backend.db.base import Base

    db_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5433/sih26189_test")
    engine = get_engine(custom_url=db_url)
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory(engine=engine)
    db = factory()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_independent_source_key_extractor():
    assert get_independent_source_key("doc:123e4567-e89b-12d3-a456-426614174000|job:abcd") == "doc:123e4567-e89b-12d3-a456-426614174000"
    assert get_independent_source_key("fir:123e4567-e89b-12d3-a456-426614174000") == "fir:123e4567-e89b-12d3-a456-426614174000"
    assert get_independent_source_key("chunk:xyz|doc:123e4567-e89b-12d3-a456-426614174000") == "doc:123e4567-e89b-12d3-a456-426614174000"
    assert get_independent_source_key("unknown-format") == "unknown-format"
    assert get_independent_source_key(None) == "UNKNOWN"

def test_provenance_registration_promotes_to_corroborated(db_session):
    # This assumes db_session fixture yields a valid Postgres transaction
    case_id = uuid4()
    user_id = uuid4()
    e1_id = uuid4()
    e2_id = uuid4()
    
    # Need to insert base entities to satisfy FK
    # To avoid FK violations in full DB, we must create a case and entities.
    from backend.db.models.identity import User, Case
    
    # In a pure unit test, we might mock DB, but if db_session is a real test DB:
    # We will just insert them manually
    user = User(user_id=user_id, email=f"{uuid4()}@test.com", username=f"test_inv_{str(uuid4())[:8]}", password_hash="hash")
    case = Case(case_id=case_id, case_code=f"PH4-{str(uuid4())[:8]}", title="Test Case", jurisdiction="TEST", created_by=user_id)
    ent1 = Entity(entity_id=e1_id, case_id=case_id, canonical_name="E1", entity_type="PERSON")
    ent2 = Entity(entity_id=e2_id, case_id=case_id, canonical_name="E2", entity_type="PERSON")
    
    db_session.add_all([user, case, ent1, ent2])
    db_session.flush()

    # Add first evidence
    rel1 = register_relationship_evidence(
        db=db_session,
        case_id=case_id,
        user_id=user_id,
        source_entity_uuid=e1_id,
        target_entity_uuid=e2_id,
        relationship_type="ASSOCIATED_WITH",
        source_ref="doc:123e4567-e89b-12d3-a456-426614174000",
        support_type="TEXT_EXTRACTION"
    )
    
    assert rel1.status == "OBSERVED"
    assert rel1.evidence_count == 1
    assert rel1.belief > 0.0
    initial_belief = rel1.belief
    
    # Add second evidence from SAME doc
    rel2 = register_relationship_evidence(
        db=db_session,
        case_id=case_id,
        user_id=user_id,
        source_entity_uuid=e1_id,
        target_entity_uuid=e2_id,
        relationship_type="ASSOCIATED_WITH",
        source_ref="doc:123e4567-e89b-12d3-a456-426614174000|chunk:2",
        support_type="TEXT_EXTRACTION"
    )
    
    # Still OBSERVED because source is not independent
    assert rel2.status == "OBSERVED"
    assert rel2.evidence_count == 2
    
    # Add third evidence from DIFFERENT doc
    rel3 = register_relationship_evidence(
        db=db_session,
        case_id=case_id,
        user_id=user_id,
        source_entity_uuid=e1_id,
        target_entity_uuid=e2_id,
        relationship_type="ASSOCIATED_WITH",
        source_ref="doc:999e4567-e89b-12d3-a456-426614174000",
        support_type="TABULAR"
    )
    
    # Should promote to CORROBORATED
    assert rel3.status == "CORROBORATED"
    assert rel3.evidence_count == 3
    assert rel3.belief > initial_belief # Belief should grow
    
    # Check audits
    audits = db_session.query(AuditLog).filter_by(case_id=case_id).all()
    assert len(audits) == 3
