"""
Export Repository for SIH26189.
Authoritative ledger for generated case report jobs and artifact references.
Enforces strict case boundary isolation and preserves immutable hashes and artifact references.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.db.models.analytics import Export
from backend.domain.errors import CaseIsolationViolationError

logger = logging.getLogger("backend.repositories.export_repository")


class ExportRepository:
    """
    Repository managing case export ledger records.
    Stores only fields defined by 02_DATABASE_SCHEMA.md:
    export_id, case_id, user_uuid, artifact_ref, version_hash, created_at.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_export(
        self,
        case_id: UUID,
        user_uuid: UUID,
        artifact_ref: str,
        version_hash: str,
        export_id: Optional[UUID] = None,
    ) -> Export:
        """
        Creates an export job ledger entry strictly scoped to case_id.
        Preserves artifact reference and version hash.
        """
        export_entry = Export(
            export_id=export_id or uuid4(),
            case_id=case_id,
            user_uuid=user_uuid,
            artifact_ref=artifact_ref,
            version_hash=version_hash,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(export_entry)
        self.session.commit()
        self.session.refresh(export_entry)
        return export_entry

    def get_export_by_id(
        self, case_id: UUID, export_id: UUID
    ) -> Optional[Export]:
        """
        Retrieves an export ledger entry strictly within the specified case boundary.
        Returns None if record does not exist or belongs to another case.
        """
        return (
            self.session.query(Export)
            .filter(
                Export.case_id == case_id,
                Export.export_id == export_id,
            )
            .first()
        )

    def list_case_exports(
        self, case_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Export]:
        """
        Retrieves export records strictly scoped to case_id.
        """
        return (
            self.session.query(Export)
            .filter(Export.case_id == case_id)
            .order_by(Export.created_at.desc(), Export.export_id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
