"""
Graph API Pydantic Schemas for SIH26189.
Conforms strictly to 03_GRAPH_SCHEMA.md, 04_API_SPEC.md, and 08_UI_DATA_CONTRACT.md.
Cytoscape.js compatible payload structure with factual/predicted edge styling.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CytoscapeNodeData(BaseModel):
    """Internal data dictionary of a Cytoscape.js node."""
    id: str = Field(..., description="Unique entity UUID string")
    label: str = Field(..., description="Human-readable canonical name")
    entity_type: str = Field(..., description="Canonical entity type (e.g. PERSON, PHONE)")
    case_id: str = Field(..., description="Case tenant boundary UUID string")
    status: str = Field(default="ACTIVE", description="Entity status")
    risk_score: Optional[float] = Field(default=None, description="Analytical risk score if present")


class CytoscapeNode(BaseModel):
    """Cytoscape.js node format: {'data': {...}}"""
    data: CytoscapeNodeData


class CytoscapeEdgeData(BaseModel):
    """Internal data dictionary of a Cytoscape.js edge."""
    id: str = Field(..., description="Unique relationship UUID string")
    source: str = Field(..., description="Source entity UUID string")
    target: str = Field(..., description="Target entity UUID string")
    type: str = Field(..., description="Canonical relationship type (e.g. CONTACTED, OWNS)")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    is_predicted: bool = Field(default=False, description="True for AI-inferred links, False for hard facts")
    provenance_count: int = Field(default=1, ge=0, description="Number of independent supporting evidence items")
    style_line: str = Field(default="solid", description="'solid' for observed evidence, 'dashed' for predictions")


class CytoscapeEdge(BaseModel):
    """Cytoscape.js edge format: {'data': {...}}"""
    data: CytoscapeEdgeData


class GraphStats(BaseModel):
    """Statistical summary of the retrieved graph topology."""
    node_count: int = Field(default=0, ge=0)
    edge_count: int = Field(default=0, ge=0)
    predicted_edge_count: int = Field(default=0, ge=0)


class CaseGraphResponse(BaseModel):
    """Cytoscape-compatible response payload returned by GET /api/v1/cases/{case_id}/graph."""
    nodes: List[CytoscapeNode] = Field(default_factory=list)
    edges: List[CytoscapeEdge] = Field(default_factory=list)
    stats: GraphStats = Field(default_factory=GraphStats)


class GraphRebuildResponse(BaseModel):
    """Asynchronous receipt returned by POST /api/v1/cases/{case_id}/graph/rebuild (HTTP 202 Accepted)."""
    case_id: UUID = Field(..., description="Case UUID")
    job_id: UUID = Field(..., description="Asynchronous rebuild job UUID-v4")
    status: str = Field(default="REBUILDING", description="Initial rebuild state")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
