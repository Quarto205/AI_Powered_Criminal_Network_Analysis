"""
Agent 2 Phase 2: Ingestion Staging & Identifier Normalization Engine.
Implements deterministic staging of Agent 1 ExtractionJobResponse into canonical relational structures.
"""

from typing import Dict
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from agents.extraction.schemas import ExtractionJobResponse, ExtractedEntity, ExtractedRelationship
from backend.db.models.entities import (
    Entity,
    EntityIdentifier,
    Relationship,
    RelationshipEvidence,
    RelationshipEvidenceState,
    normalize_identifier,
    hash_identifier,
    mask_identifier,
)

SUPPORT_TYPE_AGENT1_EXTRACTION = "AGENT1_EXTRACTION"

def _wrap_untrusted_input(text: str) -> str:
    """
    Wraps extracted text in the project's established untrusted-input delimiter convention
    to prevent prompt injection in downstream LLM consumers.
    """
    if not text:
        return text
    return f'"""untrusted_input\n{text}\n"""untrusted_input'


def stage_extraction_payload(
    db_session: Session,
    payload: ExtractionJobResponse,
    case_id: UUID,
    document_id: UUID,
) -> None:
    """
    Stages the extracted entities and relationships into the PostgreSQL relational schema.
    This function is strictly deterministic and does not perform Phase 3 entity resolution.
    It executes within the provided SQLAlchemy session transaction.
    """

    # 1. Temporary Entity Mapping: map Agent 1 temp_id to the new canonical Entity UUID
    temp_id_to_uuid: Dict[str, UUID] = {}
    staged_entities = []
    staged_identifiers = []

    for entity_ref in payload.extracted_entities:
        entity_uuid = uuid4()
        temp_id_to_uuid[entity_ref.temp_id] = entity_uuid
        
        # We do not do fuzzy matching. Every extracted mention becomes a temporary observed entity.
        canonical_name = entity_ref.extracted_text
        if len(canonical_name) > 255:
            canonical_name = canonical_name[:252] + "..."

        entity_record = Entity(
            entity_id=entity_uuid,
            case_id=case_id,
            entity_type=entity_ref.entity_type.value,
            canonical_name=canonical_name,
            status="ACTIVE",
        )
        staged_entities.append(entity_record)

        # 2. Identifier Normalization
        # For PHONE, BANK_ACCOUNT, VEHICLE, we perform exact normalization and hashing.
        if entity_ref.entity_type.value in ("PHONE", "BANK_ACCOUNT", "VEHICLE"):
            normalized_val = normalize_identifier(entity_ref.entity_type.value, entity_ref.extracted_text)
            if normalized_val:
                val_hash = hash_identifier(normalized_val)
                val_policy = mask_identifier(entity_ref.entity_type.value, normalized_val)

                identifier_record = EntityIdentifier(
                    identifier_id=uuid4(),
                    entity_id=entity_uuid,
                    type=entity_ref.entity_type.value,
                    normalized_value_hash=val_hash,
                    value_policy=val_policy,
                )
                staged_identifiers.append(identifier_record)

    # Insert entities and identifiers
    if staged_entities:
        db_session.add_all(staged_entities)
    if staged_identifiers:
        db_session.add_all(staged_identifiers)

    # 3. Relationship Staging
    staged_relationships = []
    staged_evidence = []

    for rel in payload.extracted_relationships:
        source_uuid = temp_id_to_uuid.get(rel.source_temp_id)
        target_uuid = temp_id_to_uuid.get(rel.target_temp_id)

        if not source_uuid or not target_uuid:
            raise ValueError(f"Relationship references unknown temp_ids: {rel.source_temp_id} -> {rel.target_temp_id}")

        rel_uuid = uuid4()
        relationship_record = Relationship(
            relationship_id=rel_uuid,
            case_id=case_id,
            source_entity_uuid=source_uuid,
            target_entity_uuid=target_uuid,
            type=rel.type[:50],  # Ensure fits in column
            status=RelationshipEvidenceState.OBSERVED.value,
        )
        staged_relationships.append(relationship_record)

        # 4. Evidence Creation
        # Format source_ref to preserve document provenance (since we don't have chunk_id in this payload directly,
        # we reference the document_id and the extraction job, plus the specific text span).
        safe_span_ref = f"doc:{document_id}|job:{payload.extraction_job_id}"
        
        evidence_record = RelationshipEvidence(
            evidence_id=uuid4(),
            relationship_id=rel_uuid,
            source_ref=safe_span_ref,
            support_type=SUPPORT_TYPE_AGENT1_EXTRACTION,
        )
        staged_evidence.append(evidence_record)

    # Insert relationships and evidence
    if staged_relationships:
        db_session.add_all(staged_relationships)
    if staged_evidence:
        db_session.add_all(staged_evidence)

    # The caller is responsible for db_session.commit()
