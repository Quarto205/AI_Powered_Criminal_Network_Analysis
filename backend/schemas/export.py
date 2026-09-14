"""
Export and report schemas for SIH26189.
Conforms to 02_DATABASE_SCHEMA.md (exports table), 04_API_SPEC.md (Section 4.2),
and frontend contracts.ts.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


ExportFormat = Literal["PDF", "CSV"]


class ExportRequest(BaseModel):
    """Case report generation request payload."""
    export_format: ExportFormat = Field(..., description="PDF or CSV")
    include_audit_trail: bool = Field(default=False, description="Whether to include immutable audit logs")


class ExportResponse(BaseModel):
    """Case report export receipt."""
    model_config = ConfigDict(from_attributes=True)

    export_id: UUID
    case_id: UUID
    artifact_ref: str
    version_hash: str
    created_at: datetime
    download_url: Optional[str] = None
    hash: Optional[str] = None

    @model_validator(mode="after")
    def sync_hash_field(self) -> "ExportResponse":
        if not self.hash and self.version_hash:
            self.hash = self.version_hash
        return self


class ExportCreate(BaseModel):
    """Payload to insert an immutable export ledger record."""
    case_id: UUID
    user_uuid: UUID
    artifact_ref: str
    version_hash: str
