"""
Evidence Repository for SIH26189.
Authoritative data access layer for relationship evidence, source document provenance,
and chunk offsets. Strictly enforces tenant/case boundary isolation.
Raw source artifacts and chunks remain immutable.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from backend.db.models.entities import Relationship, RelationshipEvidence
from backend.db.models.ingestion import Document, DocumentChunk, DocumentVersion
from backend.domain.errors import CaseIsolationViolationError
from backend.schemas.evidence_analysis import EvidenceDetailResponse


def parse_character_span(span_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """Parses character span format (e.g. '120-450' or '120:450') into (start, end)."""
    if not span_str:
        return None, None
    match = re.search(r"(\d+)\s*[-:]\s*(\d+)", span_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    digits = re.findall(r"\d+", span_str)
    if len(digits) >= 2:
        return int(digits[0]), int(digits[1])
    return None, None


class EvidenceRepository:
    """
    Authoritative repository managing relationship evidence and provenance chains.
    Every query enforces case isolation via case_id.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_evidence_by_id(
        self, case_id: UUID, evidence_id: UUID
    ) -> Optional[RelationshipEvidence]:
        """
        Retrieves a single relationship evidence record strictly scoped to case_id.
        Returns None if record does not exist or belongs to another case.
        """
        return (
            self.session.query(RelationshipEvidence)
            .join(Relationship, Relationship.relationship_id == RelationshipEvidence.relationship_id)
            .filter(
                Relationship.case_id == case_id,
                RelationshipEvidence.evidence_id == evidence_id,
            )
            .first()
        )

    def list_relationship_evidence(
        self, case_id: UUID, relationship_id: UUID
    ) -> List[RelationshipEvidence]:
        """
        Retrieves all evidence citations supporting a relationship within case_id.
        Enforces that the relationship belongs to case_id.
        """
        return (
            self.session.query(RelationshipEvidence)
            .join(Relationship, Relationship.relationship_id == RelationshipEvidence.relationship_id)
            .filter(
                Relationship.case_id == case_id,
                Relationship.relationship_id == relationship_id,
            )
            .all()
        )

    def get_chunk_provenance(
        self, case_id: UUID, chunk_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves parsed document chunk details and source metadata strictly scoped to case_id.
        Returns character offsets (character_start, character_end), page number,
        and immutable version/file hashes.
        """
        row = (
            self.session.query(DocumentChunk, DocumentVersion, Document)
            .join(DocumentVersion, DocumentVersion.version_id == DocumentChunk.version_id)
            .join(Document, Document.document_id == DocumentVersion.document_id)
            .filter(
                Document.case_id == case_id,
                DocumentChunk.chunk_id == chunk_id,
            )
            .first()
        )
        if not row:
            return None

        chunk, version, document = row
        start_offset, end_offset = parse_character_span(chunk.character_span)

        return {
            "chunk_id": chunk.chunk_id,
            "version_id": version.version_id,
            "document_id": document.document_id,
            "case_id": document.case_id,
            "page_number": chunk.page_number,
            "character_start": start_offset,
            "character_end": end_offset,
            "character_span": chunk.character_span,
            "storage_ref": chunk.storage_ref,
            "text_hash": chunk.text_hash,
            "version_hash": version.version_hash,
            "file_type": document.file_type,
            "file_hash": document.file_hash,
            "storage_key": document.storage_key,
        }

    def get_evidence_provenance(
        self, case_id: UUID, evidence_id: UUID
    ) -> Optional[EvidenceDetailResponse]:
        """
        Resolves a full evidence provenance response with document/chunk traceability.
        Guarantees cross-case isolation.
        """
        evidence = self.get_evidence_by_id(case_id=case_id, evidence_id=evidence_id)
        if not evidence:
            return None

        doc_id: Optional[UUID] = None
        chk_id: Optional[UUID] = None
        file_name: Optional[str] = None
        version_hash: Optional[str] = None
        page_number: Optional[int] = None
        char_start: Optional[int] = None
        char_end: Optional[int] = None
        snippet: Optional[str] = None

        # Check if source_ref points to a chunk UUID or document
        try:
            potential_uuid = UUID(evidence.source_ref.strip())
            chunk_data = self.get_chunk_provenance(case_id=case_id, chunk_id=potential_uuid)
            if chunk_data:
                chk_id = chunk_data["chunk_id"]
                doc_id = chunk_data["document_id"]
                version_hash = chunk_data["version_hash"]
                page_number = chunk_data["page_number"]
                char_start = chunk_data["character_start"]
                char_end = chunk_data["character_end"]
                snippet = f"Excerpt from chunk {chk_id}"
        except (ValueError, TypeError, AttributeError):
            pass

        return EvidenceDetailResponse(
            evidence_id=evidence.evidence_id,
            case_id=case_id,
            relationship_id=evidence.relationship_id,
            source_ref=evidence.source_ref,
            support_type=evidence.support_type,
            document_id=doc_id,
            chunk_id=chk_id,
            file_name=file_name,
            version_hash=version_hash,
            page_number=page_number,
            character_start=char_start,
            character_end=char_end,
            snippet=snippet,
            created_at=evidence.relationship.created_at if evidence.relationship else None,
        )

    def list_case_evidence(
        self, case_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[RelationshipEvidence]:
        """
        Lists relationship evidence records strictly within the specified case boundary.
        """
        return (
            self.session.query(RelationshipEvidence)
            .join(Relationship, Relationship.relationship_id == RelationshipEvidence.relationship_id)
            .filter(Relationship.case_id == case_id)
            .order_by(RelationshipEvidence.evidence_id)
            .limit(limit)
            .offset(offset)
            .all()
        )
