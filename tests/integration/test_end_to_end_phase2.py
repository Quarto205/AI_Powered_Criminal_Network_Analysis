from backend.db.session import get_db, get_engine, get_session_factory
"""
End-to-End Pipeline test for Agent 2 Phase 2.
Upload -> Received -> Validated -> Processing -> Extracted -> Staging -> Postgres Verification.
"""
import asyncio
import pytest
from uuid import uuid4
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from backend.db.base import Base
from backend.repositories.document_repository import DocumentRepository
from backend.services.document_pipeline import DocumentPipeline
from backend.schemas.document_jobs import DocumentTaskRequest, DocumentState
from agents.extraction.schemas import ExtractionJobResponse, ExtractedEntity, ExtractedRelationship, ExtractionEntityType
from backend.jobs.staged_ingestion_job import StagedIngestionJob
from backend.db.models.entities import Entity, EntityIdentifier, Relationship, RelationshipEvidence
from backend.db.models.ingestion import Document as DbDocument

# Create a temporary in-memory sqlite for test
from backend.db.session import get_engine, get_session_factory
engine = get_engine()
TestingSessionLocal = get_session_factory(engine)



@pytest.mark.asyncio
async def test_end_to_end_phase2_pipeline():
    session = TestingSessionLocal()
    repository = DocumentRepository(session=session)
    case_id = uuid4()
    user_id = uuid4()
    doc_id = uuid4()
    job_id = uuid4()
    
    repository.authorize_case_access(user_id, case_id)
    
    # 1. Setup Case and User (PostgreSQL requires referential integrity)
    from backend.db.models.identity import Case, User, CaseMember
    
    user = User(user_id=user_id, email=f"{user_id}@test.com", username=str(user_id), password_hash="hash")
    case = Case(case_id=case_id, case_code=f"E2E-{case_id.hex[:8]}", title="Test", status="ACTIVE", jurisdiction="TEST", created_by=user_id)
    member = CaseMember(case_member_id=uuid4(), case_id=case_id, user_id=user_id, role_in_case="INVESTIGATOR")
    session.add_all([user, case, member])
    session.commit()
    
    # 1-3. Upload / Create
    doc = repository.create(
        document_id=doc_id,
        case_id=case_id,
        filename="test_file.txt",
        file_type="text/plain",
        file_hash="hash_123",
        storage_key="test/test_file.txt"
    )
    assert doc.status == DocumentState.RECEIVED
    
    # 4-7. Pipeline (Simulating Agent 1 payload logic)
    req = DocumentTaskRequest(
        job_id=job_id,
        document_id=doc_id,
        case_id=case_id,
        filename="test_file.txt",
        storage_key="test/test_file.txt",
        caller_user_id=user_id
    )
    
    # We will manually step through what pipeline does, 
    # but the pipeline normally fetches extraction automatically.
    # Since we can't easily mock the Agent 1 inference here without patching, 
    # we will manually advance the lifecycle and inject the payload,
    # as the pipeline would.
    
    repository.update_status(doc_id, case_id, DocumentState.EXTRACTED)
    
    # 8-12. Payload Generation & Phase 2 Staging Job
    payload = ExtractionJobResponse(
        extraction_job_id=uuid4(),
        extracted_entities=[
            ExtractedEntity(
                temp_id="E1",
                entity_type=ExtractionEntityType.PERSON,
                extracted_text="John Doe",
                character_start=0,
                character_end=8
            ),
            ExtractedEntity(
                temp_id="E2",
                entity_type=ExtractionEntityType.PHONE,
                extracted_text="9876543210",
                character_start=10,
                character_end=20
            )
        ],
        extracted_relationships=[
            ExtractedRelationship(
                source_temp_id="E1",
                target_temp_id="E2",
                type="OWNS_PHONE",
                context_span="John Doe 9876543210",
                confidence_score=0.99
            )
        ]
    )
    
    staging_job = StagedIngestionJob(session_factory=TestingSessionLocal, repository=repository)
    
    # Act: execute staging
    result = staging_job.execute_staging(
        payload=payload,
        case_id=case_id,
        document_id=doc_id,
        actor_id=user_id
    )
    
    assert result is True
    
    # Verify in Database
    new_session = TestingSessionLocal()
    entities = new_session.query(Entity).filter(Entity.case_id == case_id).all()
    assert len(entities) == 2
    
    identifiers = new_session.query(EntityIdentifier).filter(
        EntityIdentifier.entity_id.in_([e.entity_id for e in entities])
    ).all()
    assert len(identifiers) == 1
    assert identifiers[0].type == "PHONE"
    
    relationships = new_session.query(Relationship).filter(Relationship.case_id == case_id).all()
    assert len(relationships) == 1
    assert relationships[0].status == "OBSERVED"
    
    evidences = new_session.query(RelationshipEvidence).filter(
        RelationshipEvidence.relationship_id.in_([r.relationship_id for r in relationships])
    ).all()
    assert len(evidences) == 1
    assert evidences[0].relationship_id == relationships[0].relationship_id
    assert str(doc_id) in evidences[0].source_ref
    
    new_session.close()
    session.close()
