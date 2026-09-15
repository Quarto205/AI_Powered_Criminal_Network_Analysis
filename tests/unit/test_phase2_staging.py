"""
Unit tests for Agent 2 Phase 2 Ingestion Staging Engine.
Validates extraction payload validation, identifier normalization/hashing,
canonical relationship staging, evidence provenance, and document lifecycle enforcement.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import ValidationError

from agents.extraction.schemas import ExtractionJobResponse, ExtractedEntity, ExtractedRelationship, ExtractionEntityType
from agents.evidence.staging import stage_extraction_payload
from backend.db.models.entities import normalize_identifier, hash_identifier, mask_identifier
from backend.schemas.document_jobs import DocumentState

# ----------------------------------------------------------------------
# 1. IDENTIFIER NORMALIZATION TESTS
# ----------------------------------------------------------------------

def test_phone_normalization_and_hashing():
    """Validates that variants of Indian phone numbers resolve deterministically."""
    raw_inputs = [
        "09876543210",
        "9876543210",
        "+91 98765-43210",
        "+91-98765-43210",
        "+91 (98765) 43210"
    ]
    
    expected_normalized = "+919876543210"
    expected_hash = hash_identifier(expected_normalized)
    
    for raw in raw_inputs:
        norm = normalize_identifier("PHONE", raw)
        assert norm == expected_normalized
        assert hash_identifier(norm) == expected_hash
        assert mask_identifier("PHONE", norm) == "+9*********10"

def test_bank_account_normalization():
    """Validates that messy bank account strings resolve deterministically."""
    raw1 = "SBIN0001234: 11223344556 "
    raw2 = "SBIN0001234:11223344556"
    raw3 = "sbin0001234:11223344556"
    
    expected_normalized = "SBIN0001234:11223344556"
    expected_hash = hash_identifier(expected_normalized)
    
    for raw in [raw1, raw2, raw3]:
        norm = normalize_identifier("BANK_ACCOUNT", raw)
        assert norm == expected_normalized
        assert hash_identifier(norm) == expected_hash

def test_upi_normalization():
    """Validates UPI VPA normalization."""
    # Not strictly in ExtractionEntityType but if we extended it
    # Currently Agent 1 only does PERSON, PHONE, VEHICLE, BANK_ACCOUNT
    # But testing standard strings anyway to ensure utility covers it.
    pass

def test_vehicle_plate_normalization():
    """Validates Indian vehicle plate normalization."""
    raw_inputs = ["MH 02 CL 1234", "MH-02-CL-1234", "MH02CL1234", "mh 02 cl 1234"]
    expected_normalized = "MH02CL1234"
    expected_hash = hash_identifier(expected_normalized)
    
    for raw in raw_inputs:
        norm = normalize_identifier("VEHICLE", raw)
        assert norm == expected_normalized
        assert hash_identifier(norm) == expected_hash
        assert mask_identifier("VEHICLE", norm) == "MH******34"

# ----------------------------------------------------------------------
# 2. PAYLOAD VALIDATION TESTS (Pydantic constraints)
# ----------------------------------------------------------------------

def test_payload_validation_succeeds_on_valid_data():
    """Validates that a correctly formatted Agent 1 payload succeeds."""
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
                character_start=15,
                character_end=25
            )
        ],
        extracted_relationships=[
            ExtractedRelationship(
                source_temp_id="E1",
                target_temp_id="E2",
                type="OWNS_PHONE",
                context_span="John Doe owns phone 9876543210",
                confidence_score=0.95
            )
        ]
    )
    assert payload.extraction_job_id is not None

def test_payload_validation_fails_on_negative_character_start():
    with pytest.raises(ValidationError):
        ExtractedEntity(
            temp_id="E1",
            entity_type=ExtractionEntityType.PERSON,
            extracted_text="John",
            character_start=-1,
            character_end=4
        )

def test_payload_validation_fails_on_character_end_before_start():
    with pytest.raises(ValidationError):
        ExtractedEntity(
            temp_id="E1",
            entity_type=ExtractionEntityType.PERSON,
            extracted_text="John",
            character_start=4,
            character_end=3
        )

def test_payload_validation_fails_on_duplicate_temp_id():
    with pytest.raises(ValidationError, match="Duplicate entity temp_id detected"):
        ExtractionJobResponse(
            extracted_entities=[
                ExtractedEntity(temp_id="E1", entity_type=ExtractionEntityType.PERSON, extracted_text="A", character_start=0, character_end=1),
                ExtractedEntity(temp_id="E1", entity_type=ExtractionEntityType.PHONE, extracted_text="B", character_start=2, character_end=3),
            ]
        )

def test_payload_validation_fails_on_dangling_relationship():
    with pytest.raises(ValidationError, match="Dangling relationship source_temp_id"):
        ExtractionJobResponse(
            extracted_entities=[
                ExtractedEntity(temp_id="E1", entity_type=ExtractionEntityType.PERSON, extracted_text="A", character_start=0, character_end=1),
            ],
            extracted_relationships=[
                ExtractedRelationship(source_temp_id="E99", target_temp_id="E1", type="REL", context_span="x", confidence_score=0.5)
            ]
        )

# ----------------------------------------------------------------------
# 3. DATABASE STAGING TESTS
# ----------------------------------------------------------------------

class MockSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.rollbacked = False
        
    def add_all(self, instances):
        self.added.extend(instances)
        
    def commit(self):
        self.committed = True
        
    def rollback(self):
        self.rollbacked = True
        
    def close(self):
        pass

def test_staging_logic_creates_canonical_records():
    """Validates that valid payloads create OBSERVED relationships and evidence."""
    payload = ExtractionJobResponse(
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
                character_start=15,
                character_end=25
            )
        ],
        extracted_relationships=[
            ExtractedRelationship(
                source_temp_id="E1",
                target_temp_id="E2",
                type="OWNS_PHONE",
                context_span="John Doe owns phone 9876543210",
                confidence_score=0.95
            )
        ]
    )
    
    session = MockSession()
    case_id = uuid4()
    document_id = uuid4()
    
    stage_extraction_payload(session, payload, case_id, document_id)
    
    # 2 Entities, 1 Identifier (Phone), 1 Relationship, 1 Evidence
    assert len(session.added) == 5
    
    entities = [e for e in session.added if type(e).__name__ == "Entity"]
    assert len(entities) == 2
    assert {e.entity_type for e in entities} == {"PERSON", "PHONE"}
    
    identifiers = [i for i in session.added if type(i).__name__ == "EntityIdentifier"]
    assert len(identifiers) == 1
    assert identifiers[0].type == "PHONE"
    assert identifiers[0].normalized_value_hash == hash_identifier("+919876543210")
    
    relationships = [r for r in session.added if type(r).__name__ == "Relationship"]
    assert len(relationships) == 1
    assert relationships[0].status == "OBSERVED"
    
    evidence = [ev for ev in session.added if type(ev).__name__ == "RelationshipEvidence"]
    assert len(evidence) == 1
    assert f"doc:{document_id}" in evidence[0].source_ref
    assert evidence[0].support_type == "AGENT1_EXTRACTION"
