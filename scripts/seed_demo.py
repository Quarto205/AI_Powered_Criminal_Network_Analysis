#!/usr/bin/env python3
"""
Seed Deterministic Canonical Demo Data for SIH26189.
Creates the minimal valid canonical dataset in PostgreSQL required for
Agent 2 Phase 5 Graph Projection and subsequent verification.

Strictly adheres to canonical contracts:
- Deterministic UUIDs via uuid.uuid5
- Referential integrity across User, Case, Membership, Document, Version, Chunk,
  Entities, Identifiers, Relationship, and Evidence.
- Idempotent and safe to re-run (detects existing records, honors immutability listeners).
"""

import hashlib
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

# Ensure project root is in sys.path for standalone script execution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db.session import SessionLocal
from backend.db.models.identity import User, Case, CaseMember
from backend.db.models.ingestion import Document, DocumentVersion, DocumentChunk
from backend.db.models.entities import (
    Entity,
    EntityIdentifier,
    Relationship,
    RelationshipEvidence,
    RelationshipEvidenceState,
    hash_identifier,
    normalize_identifier,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_demo")

# Deterministic namespace for all demo identifiers
DEMO_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "sih26189.demo.canonical")

# Deterministic UUIDs
USER_ID = uuid.uuid5(DEMO_NAMESPACE, "user:demo_investigator")
CASE_ID = uuid.uuid5(DEMO_NAMESPACE, "case:DEMO-CASE-2026-0001")
CASE_MEMBER_ID = uuid.uuid5(DEMO_NAMESPACE, "case_member:demo_investigator:DEMO-CASE-2026-0001")
DOCUMENT_ID = uuid.uuid5(DEMO_NAMESPACE, "document:demo_cdr_report")
DOCUMENT_VERSION_ID = uuid.uuid5(DEMO_NAMESPACE, "document_version:demo_cdr_report:v1")
DOCUMENT_CHUNK_ID = uuid.uuid5(DEMO_NAMESPACE, "document_chunk:demo_cdr_report:v1:chunk1")
ENTITY_PERSON_ID = uuid.uuid5(DEMO_NAMESPACE, "entity:person:vikram_singh")
ENTITY_PHONE_ID = uuid.uuid5(DEMO_NAMESPACE, "entity:phone:9876543210")
IDENTIFIER_PERSON_ID = uuid.uuid5(DEMO_NAMESPACE, "identifier:person:vikram_singh")
IDENTIFIER_PHONE_ID = uuid.uuid5(DEMO_NAMESPACE, "identifier:phone:9876543210")
RELATIONSHIP_ID = uuid.uuid5(DEMO_NAMESPACE, "relationship:vikram_singh:owns:9876543210")
RELATIONSHIP_EVIDENCE_ID = uuid.uuid5(DEMO_NAMESPACE, "evidence:vikram_singh:owns:9876543210:chunk1")


def compute_sha256(content: str) -> str:
    """Helper to compute standard SHA-256 hex string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def seed_demo_data() -> Tuple[uuid.UUID, Dict[str, str]]:
    """
    Idempotently seeds the minimum valid canonical dataset into PostgreSQL.
    Returns the deterministic case_id and summary dictionary of table statuses.
    """
    summary: Dict[str, str] = {}
    session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        # 1. User
        user = session.query(User).filter(User.user_id == USER_ID).first()
        if not user:
            user = User(
                user_id=USER_ID,
                email="demo_investigator@sih.synthetic",
                username="demo_investigator",
                password_hash="$2b$12$syntheticpasswordhashfordemoinvestigatoronly000",
                account_status="ACTIVE",
                created_at=now,
            )
            session.add(user)
            summary["users"] = "INSERTED"
        else:
            summary["users"] = "EXISTING"

        # Flush to satisfy foreign key for Case
        session.flush()

        # 2. Case
        case = session.query(Case).filter(Case.case_id == CASE_ID).first()
        if not case:
            case = Case(
                case_id=CASE_ID,
                case_code="DEMO-CASE-2026-0001",
                title="[DEMO] Synthetic Network Investigation",
                description="Synthetic dataset for Agent 2 Phase 5 Graph Projection verification.",
                status="ACTIVE",
                jurisdiction="DELHI_SPECIAL_CELL",
                created_by=USER_ID,
                created_at=now,
            )
            session.add(case)
            summary["cases"] = "INSERTED"
        else:
            summary["cases"] = "EXISTING"

        session.flush()

        # 3. CaseMember
        member = session.query(CaseMember).filter(CaseMember.case_member_id == CASE_MEMBER_ID).first()
        if not member:
            member = CaseMember(
                case_member_id=CASE_MEMBER_ID,
                case_id=CASE_ID,
                user_id=USER_ID,
                role_in_case="LEAD_INVESTIGATOR",
            )
            session.add(member)
            summary["case_members"] = "INSERTED"
        else:
            summary["case_members"] = "EXISTING"

        # 4. Document (append-only)
        doc = session.query(Document).filter(Document.document_id == DOCUMENT_ID).first()
        doc_hash = compute_sha256("SYNTHETIC_CDR_DOCUMENT_SOURCE_DATA_V1")
        if not doc:
            doc = Document(
                document_id=DOCUMENT_ID,
                case_id=CASE_ID,
                file_type="application/pdf",
                file_hash=doc_hash,
                storage_key="cases/DEMO-CASE-2026-0001/documents/cdr_report.pdf",
                status="PARSED",
                created_at=now,
            )
            session.add(doc)
            summary["documents"] = "INSERTED"
        else:
            summary["documents"] = "EXISTING"

        session.flush()

        # 5. DocumentVersion (append-only)
        doc_version = session.query(DocumentVersion).filter(DocumentVersion.version_id == DOCUMENT_VERSION_ID).first()
        ver_hash = compute_sha256("SYNTHETIC_CDR_DOCUMENT_VERSION_1")
        if not doc_version:
            doc_version = DocumentVersion(
                version_id=DOCUMENT_VERSION_ID,
                document_id=DOCUMENT_ID,
                version_hash=ver_hash,
                meta={"source": "demo_seed", "parser": "cdr_parser_v1"},
                created_at=now,
            )
            session.add(doc_version)
            summary["document_versions"] = "INSERTED"
        else:
            summary["document_versions"] = "EXISTING"

        session.flush()

        # 6. DocumentChunk (append-only)
        chunk = session.query(DocumentChunk).filter(DocumentChunk.chunk_id == DOCUMENT_CHUNK_ID).first()
        chunk_text = "Subscriber Vikram Singh registered with MSISDN 9876543210 on 2026-01-15."
        chunk_hash = compute_sha256(chunk_text)
        if not chunk:
            chunk = DocumentChunk(
                chunk_id=DOCUMENT_CHUNK_ID,
                version_id=DOCUMENT_VERSION_ID,
                page_number=1,
                character_span="0-77",
                text_hash=chunk_hash,
                storage_ref="cases/DEMO-CASE-2026-0001/chunks/chunk_001.txt",
            )
            session.add(chunk)
            summary["document_chunks"] = "INSERTED"
        else:
            summary["document_chunks"] = "EXISTING"

        # 7. Entities (PERSON and PHONE)
        e_person = session.query(Entity).filter(Entity.entity_id == ENTITY_PERSON_ID).first()
        if not e_person:
            e_person = Entity(
                entity_id=ENTITY_PERSON_ID,
                case_id=CASE_ID,
                entity_type="PERSON",
                canonical_name="Vikram Singh [DEMO]",
                status="ACTIVE",
                created_at=now,
            )
            session.add(e_person)
            summary["entities_person"] = "INSERTED"
        else:
            summary["entities_person"] = "EXISTING"

        e_phone = session.query(Entity).filter(Entity.entity_id == ENTITY_PHONE_ID).first()
        if not e_phone:
            e_phone = Entity(
                entity_id=ENTITY_PHONE_ID,
                case_id=CASE_ID,
                entity_type="PHONE",
                canonical_name="+919876543210",
                status="ACTIVE",
                created_at=now,
            )
            session.add(e_phone)
            summary["entities_phone"] = "INSERTED"
        else:
            summary["entities_phone"] = "EXISTING"

        session.flush()

        # 8. EntityIdentifiers (Masked / Hashed canonical identifiers)
        id_person = session.query(EntityIdentifier).filter(EntityIdentifier.identifier_id == IDENTIFIER_PERSON_ID).first()
        norm_person_hash = hash_identifier(normalize_identifier("NAME", "Vikram Singh"))
        if not id_person:
            id_person = EntityIdentifier(
                identifier_id=IDENTIFIER_PERSON_ID,
                entity_id=ENTITY_PERSON_ID,
                type="PERSON_NAME",
                normalized_value_hash=norm_person_hash,
                value_policy="DEMO_POLICY",
            )
            session.add(id_person)
            summary["identifiers_person"] = "INSERTED"
        else:
            summary["identifiers_person"] = "EXISTING"

        id_phone = session.query(EntityIdentifier).filter(EntityIdentifier.identifier_id == IDENTIFIER_PHONE_ID).first()
        norm_phone_hash = hash_identifier(normalize_identifier("PHONE", "9876543210"))
        if not id_phone:
            id_phone = EntityIdentifier(
                identifier_id=IDENTIFIER_PHONE_ID,
                entity_id=ENTITY_PHONE_ID,
                type="PHONE",
                normalized_value_hash=norm_phone_hash,
                value_policy="MASKED_DISPLAY",
            )
            session.add(id_phone)
            summary["identifiers_phone"] = "INSERTED"
        else:
            summary["identifiers_phone"] = "EXISTING"

        # 9. Relationship (OWNS: Vikram Singh -> +919876543210)
        rel = session.query(Relationship).filter(Relationship.relationship_id == RELATIONSHIP_ID).first()
        if not rel:
            rel = Relationship(
                relationship_id=RELATIONSHIP_ID,
                case_id=CASE_ID,
                source_entity_uuid=ENTITY_PERSON_ID,
                target_entity_uuid=ENTITY_PHONE_ID,
                type="OWNS",
                status=RelationshipEvidenceState.OBSERVED.value,
                belief=1.0,
                disbelief=0.0,
                uncertainty=0.0,
                conflict_mass=0.0,
                evidence_count=1,
                relationship_confidence=1.0,
                created_at=now,
            )
            session.add(rel)
            summary["relationships"] = "INSERTED"
        else:
            summary["relationships"] = "EXISTING"

        session.flush()

        # 10. RelationshipEvidence (Provenanced to DocumentChunk)
        ev = session.query(RelationshipEvidence).filter(RelationshipEvidence.evidence_id == RELATIONSHIP_EVIDENCE_ID).first()
        if not ev:
            ev = RelationshipEvidence(
                evidence_id=RELATIONSHIP_EVIDENCE_ID,
                relationship_id=RELATIONSHIP_ID,
                source_ref=str(DOCUMENT_CHUNK_ID),
                support_type="DOCUMENT_CHUNK",
            )
            session.add(ev)
            summary["relationship_evidence"] = "INSERTED"
        else:
            summary["relationship_evidence"] = "EXISTING"

        session.commit()
        logger.info(f"Canonical demo dataset seeded successfully for case: {CASE_ID}")
        return CASE_ID, summary

    except Exception as e:
        session.rollback()
        logger.error(f"Error during demo data seeding: {e}", exc_info=True)
        raise
    finally:
        session.close()


def main():
    logger.info("Starting deterministic demo data seeding...")
    case_id, summary = seed_demo_data()
    print("\n" + "=" * 60)
    print("DEMO SEED EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Deterministic Case ID: {case_id}")
    for table, status in summary.items():
        print(f"  {table:24}: {status}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
