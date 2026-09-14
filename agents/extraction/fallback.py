"""
Deterministic Fallback Extraction Engine for Agent 1.
Operates when primary LLM provider is offline, unreachable, or produces unrecoverable output.
Uses rigorous regex patterns for Indian domain context and guarantees exact character-offset integrity.
"""

import re
from typing import List, Tuple
from uuid import UUID, uuid4

from agents.extraction.schemas import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionEntityType,
    ExtractionJobResponse,
)


class DeterministicFallbackExtractor:
    """
    Deterministic rule-based extractor for degraded operation.
    Extracts PHONE, VEHICLE, BANK_ACCOUNT, and PERSON entities with strict character coordinate tracking.
    """

    # 1. Indian Phone numbers: +91 / 91 / 0 prefix, 10-digit mobile starting with 6-9
    PHONE_REGEX = re.compile(
        r"(?:(?:\+91|91|0)[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b"
    )

    # 2. Indian Vehicle Registration: 2-letter state code + 1-2 digit district + 1-3 letters + 4 digits
    VEHICLE_REGEX = re.compile(
        r"\b(?:AN|AP|AR|AS|BR|CH|CG|DD|DL|DN|GA|GJ|HP|HR|JH|JK|KA|KL|LA|LD|MH|ML|MN|MP|MZ|NL|OD|PB|PY|RJ|SK|TN|TR|TS|UK|UP|WB)[\s-]?[0-9]{1,2}[\s-]?(?:[A-Z]{1,3}[\s-]?)?[0-9]{4}\b",
        re.IGNORECASE,
    )

    # 3. Bank Account: 9 to 18 digits with contextual prefix/suffix
    BANK_ACCOUNT_REGEX = re.compile(
        r"(?i:\b(?:a/c|acct|acc(?:ount)?(?:\s+no\.?|(?:\s+number)?))[\s:]+)([0-9]{9,18})\b"
    )

    # 4. Person names with formal honorifics
    PERSON_HONORIFIC_REGEX = re.compile(
        r"\b(?:Shri|Smt\.?|Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
    )

    def extract(self, text: str, job_id: UUID | None = None) -> ExtractionJobResponse:
        """
        Runs deterministic pattern-matching extraction over the source text.
        Guarantees source span integrity and canonical schema compliance.
        """
        if job_id is None:
            job_id = uuid4()

        if not text or not text.strip():
            return ExtractionJobResponse(
                extraction_job_id=job_id,
                extracted_entities=[],
                extracted_relationships=[],
            )

        raw_entities: List[Tuple[int, int, ExtractionEntityType, str]] = []

        # Find Phones
        for match in self.PHONE_REGEX.finditer(text):
            raw_entities.append((
                match.start(),
                match.end(),
                ExtractionEntityType.PHONE,
                match.group(0),
            ))

        # Find Vehicles
        for match in self.VEHICLE_REGEX.finditer(text):
            raw_entities.append((
                match.start(),
                match.end(),
                ExtractionEntityType.VEHICLE,
                match.group(0),
            ))

        # Find Bank Accounts
        for match in self.BANK_ACCOUNT_REGEX.finditer(text):
            # Capture the actual account digits as the entity mention
            start, end = match.start(1), match.end(1)
            raw_entities.append((
                start,
                end,
                ExtractionEntityType.BANK_ACCOUNT,
                match.group(1),
            ))

        # Find Persons with honorifics
        for match in self.PERSON_HONORIFIC_REGEX.finditer(text):
            # Capture full match or name part
            raw_entities.append((
                match.start(),
                match.end(),
                ExtractionEntityType.PERSON,
                match.group(0),
            ))

        # Sort entities by character_start, then character_end to maintain stable order
        raw_entities.sort(key=lambda x: (x[0], x[1]))

        # Filter overlapping matches (prefer longer/earlier match)
        filtered_entities: List[Tuple[int, int, ExtractionEntityType, str]] = []
        last_end = -1
        for start, end, etype, matched_text in raw_entities:
            if start >= last_end:
                filtered_entities.append((start, end, etype, matched_text))
                last_end = end

        # Construct ExtractedEntity models
        extracted_entities: List[ExtractedEntity] = []
        for idx, (start, end, etype, matched_text) in enumerate(filtered_entities, start=1):
            temp_id = f"E{idx}"
            # Ensure text slice exact match
            assert text[start:end] == matched_text
            extracted_entities.append(
                ExtractedEntity(
                    temp_id=temp_id,
                    entity_type=etype,
                    extracted_text=matched_text,
                    character_start=start,
                    character_end=end,
                )
            )

        # Simple deterministic relationship detection within the same sentence
        extracted_relationships: List[ExtractedRelationship] = []
        # Find explicit relationships: e.g. Person driving Vehicle
        for i, ent1 in enumerate(extracted_entities):
            for ent2 in extracted_entities[i + 1:]:
                # Only check within small character distance (< 120 chars) and no sentence break
                if ent2.character_start - ent1.character_end > 120:
                    continue
                span = text[ent1.character_start:ent2.character_end]
                if "." in span[:-1]:  # cross sentence boundary
                    continue

                span_lower = span.lower()
                rel_type = None
                if ent1.entity_type == ExtractionEntityType.PERSON and ent2.entity_type == ExtractionEntityType.VEHICLE:
                    if any(w in span_lower for w in ["driving", "drove", "vehicle", "car", "traveling in", "seen in"]):
                        rel_type = "OPERATES_VEHICLE"
                elif ent1.entity_type == ExtractionEntityType.PERSON and ent2.entity_type == ExtractionEntityType.PHONE:
                    if any(w in span_lower for w in ["called", "phone", "contact", "number", "mobile", "dialed"]):
                        rel_type = "ASSOCIATED_PHONE"
                elif ent1.entity_type == ExtractionEntityType.PERSON and ent2.entity_type == ExtractionEntityType.BANK_ACCOUNT:
                    if any(w in span_lower for w in ["account", "transferred", "received", "deposited"]):
                        rel_type = "HOLDS_ACCOUNT"

                if rel_type:
                    extracted_relationships.append(
                        ExtractedRelationship(
                            source_temp_id=ent1.temp_id,
                            target_temp_id=ent2.temp_id,
                            type=rel_type,
                            context_span=span,
                            confidence_score=0.75,
                        )
                    )

        return ExtractionJobResponse(
            extraction_job_id=job_id,
            extracted_entities=extracted_entities,
            extracted_relationships=extracted_relationships,
        )
