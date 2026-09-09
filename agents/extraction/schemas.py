"""
Pydantic schemas for Agent 1: Intelligence Extraction / NLP Extraction Engine.
Strictly compliant with Section 5.2 of canonical 05_AI_CONTRACTS.md.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ExtractionEntityType(str, Enum):
    """
    Canonical entity types allowed in Agent 1 output per Section 5.2 contract.
    Historical enums (LOCATION, WEAPON, ORGANIZATION, FINANCIAL_ID) are strictly excluded.
    """
    PERSON = "PERSON"
    PHONE = "PHONE"
    VEHICLE = "VEHICLE"
    BANK_ACCOUNT = "BANK_ACCOUNT"


class ExtractedEntity(BaseModel):
    """
    Entity extracted from source text with local temporary ID and character coordinates.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    temp_id: str = Field(
        ...,
        min_length=1,
        description="Temporary entity-local identifier (e.g., 'E1', 'E2'). Not a database UUID."
    )
    entity_type: ExtractionEntityType = Field(
        ...,
        description="Canonical entity type: PERSON, PHONE, VEHICLE, or BANK_ACCOUNT."
    )
    extracted_text: str = Field(
        ...,
        min_length=1,
        description="Exact text slice from the source text representing the entity mention."
    )
    character_start: int = Field(
        ...,
        ge=0,
        description="Zero-indexed start character offset in original source text."
    )
    character_end: int = Field(
        ...,
        ge=0,
        description="Zero-indexed exclusive end character offset in original source text."
    )

    @model_validator(mode="after")
    def validate_offsets(self) -> "ExtractedEntity":
        if self.character_end < self.character_start:
            raise ValueError(
                f"character_end ({self.character_end}) cannot be less than character_start ({self.character_start})"
            )
        return self


class ExtractedRelationship(BaseModel):
    """
    Relationship between two extracted entities grounded in source text context.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_temp_id: str = Field(
        ...,
        min_length=1,
        description="Local temp_id of the source entity."
    )
    target_temp_id: str = Field(
        ...,
        min_length=1,
        description="Local temp_id of the target entity."
    )
    type: str = Field(
        ...,
        min_length=1,
        description="Relationship type (e.g., 'COMMUNICATED_WITH', 'TRANSFERRED_FUNDS_TO', 'OPERATED')."
    )
    context_span: str = Field(
        ...,
        min_length=1,
        description="Exact source text excerpt providing context and provenance for the relationship."
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score between 0.0 and 1.0."
    )


class ExtractionJobResponse(BaseModel):
    """
    The canonical output contract for Agent 1 extraction jobs.
    Directly conforms to Section 5.2 of 05_AI_CONTRACTS.md.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    extraction_job_id: UUID = Field(
        default_factory=uuid4,
        description="Canonical UUIDv4 identifying the extraction job."
    )
    extracted_entities: List[ExtractedEntity] = Field(
        default_factory=list,
        description="List of extracted entities with local temp_ids and exact character spans."
    )
    extracted_relationships: List[ExtractedRelationship] = Field(
        default_factory=list,
        description="List of extracted relationships between entities with source context."
    )

    @model_validator(mode="after")
    def validate_referential_integrity_and_uniqueness(self) -> "ExtractionJobResponse":
        # 1. Ensure entity temp_ids are unique
        entity_ids = set()
        for entity in self.extracted_entities:
            if entity.temp_id in entity_ids:
                raise ValueError(f"Duplicate entity temp_id detected: '{entity.temp_id}'")
            entity_ids.add(entity.temp_id)

        # 2. Ensure relationship source_temp_id and target_temp_id resolve to existing entities
        for rel in self.extracted_relationships:
            if rel.source_temp_id not in entity_ids:
                raise ValueError(
                    f"Dangling relationship source_temp_id: '{rel.source_temp_id}' does not exist in extracted_entities"
                )
            if rel.target_temp_id not in entity_ids:
                raise ValueError(
                    f"Dangling relationship target_temp_id: '{rel.target_temp_id}' does not exist in extracted_entities"
                )

        return self

    def verify_source_spans(self, source_text: str) -> None:
        """
        Validates that every extracted entity matches the exact slice of source text:
        source_text[character_start:character_end] == extracted_text.
        """
        for entity in self.extracted_entities:
            if entity.character_end > len(source_text):
                raise ValueError(
                    f"Entity '{entity.temp_id}' end offset {entity.character_end} exceeds source text length {len(source_text)}"
                )
            actual_slice = source_text[entity.character_start:entity.character_end]
            if actual_slice != entity.extracted_text:
                raise ValueError(
                    f"Source span mismatch for entity '{entity.temp_id}': expected '{entity.extracted_text}', "
                    f"found '{actual_slice}' at [{entity.character_start}:{entity.character_end}]"
                )


class ExtractionJobRequest(BaseModel):
    """
    Standard input contract for Agent 1 extraction jobs.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: UUID = Field(
        default_factory=uuid4,
        description="Unique job identifier."
    )
    text: str = Field(
        ...,
        description="Raw untrusted text chunk to extract intelligence from."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata such as document_id, case_id, chunk_index, or page_number."
    )
