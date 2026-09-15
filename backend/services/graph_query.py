"""
Graph Query Service for SIH26189.
Executes parameterized case-scoped graph retrievals, applies hop depth, confidence,
and prediction filters, and normalizes output into Cytoscape.js format.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.db.models.entities import Entity
from backend.graph.connection import Neo4jConnectionManager, get_graph_manager
from backend.graph.cypher_builder import CypherBuilder
from backend.schemas.graph import (
    CaseGraphResponse,
    CytoscapeEdge,
    CytoscapeEdgeData,
    CytoscapeNode,
    CytoscapeNodeData,
    GraphStats,
)

logger = logging.getLogger("backend.services.graph_query")


class GraphQueryError(Exception):
    """Raised on graph query execution failures."""
    pass


class GraphQueryService:
    """
    Service managing analytical graph queries against Neo4j.
    Guarantees strict case boundary enforcement and Cytoscape.js payload formatting.
    """
    def __init__(self, db: Session, graph_manager: Optional[Neo4jConnectionManager] = None):
        self.db = db
        self.graph_manager = graph_manager or get_graph_manager()

    def get_case_graph(
        self,
        case_id: UUID,
        depth: int = 2,
        focus_entity_id: Optional[UUID] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        include_predicted: bool = True,
        limit: int = 300,
    ) -> CaseGraphResponse:
        """
        Retrieves the case graph projection from Neo4j formatted for Cytoscape.js.
        Steps:
        1. If focus_entity_id is given, verify server-side that it belongs to case_id (IDOR defense).
        2. Build parameterized Cypher query with bounded depth (1-3) and limit.
        3. Execute query and normalize Neo4j record structures into JSON primitives.
        4. Apply solid/dashed styling based on factual vs. predicted state.
        5. Return CaseGraphResponse with node/edge counts and predicted edge stats.
        """
        # Step 1: IDOR verification on focus_entity_id
        if focus_entity_id is not None:
            focus_entity = (
                self.db.query(Entity)
                .filter(Entity.entity_id == focus_entity_id, Entity.case_id == case_id)
                .first()
            )
            if not focus_entity:
                # Entity does not belong to this case: return empty graph to prevent cross-case leakage
                logger.warning(
                    f"IDOR check blocked focus_entity_id {focus_entity_id} - does not belong to case {case_id}"
                )
                return CaseGraphResponse(nodes=[], edges=[], stats=GraphStats())

        # Step 2: Ensure Neo4j connectivity
        if not self.graph_manager.is_healthy():
            raise GraphQueryError("Neo4j analytical database is currently unavailable.")

        # Step 3: Build parameterized Cypher
        query, params = CypherBuilder.build_case_graph_query(
            case_id=case_id,
            depth=depth,
            focus_entity_id=focus_entity_id,
            allowed_entity_types=entity_types,
            min_confidence=min_confidence,
            include_predicted=include_predicted,
            limit=limit,
        )

        raw_nodes: List[Dict[str, Any]] = []
        raw_edges: List[Dict[str, Any]] = []

        try:
            with self.graph_manager.get_session(access_mode="READ") as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    raw_nodes = record.get("nodes") or []
                    raw_edges = record.get("edges") or []
        except Exception as e:
            logger.error(f"Neo4j query execution failed: {type(e).__name__}", exc_info=True)
            raise GraphQueryError("Failed to execute analytical graph query.")

        # Step 4: Normalize and deduplicate nodes into Cytoscape format
        seen_node_ids = set()
        cytoscape_nodes: List[CytoscapeNode] = []
        for n in raw_nodes:
            # Handle both dict (from mock or driver) and Neo4j Node objects
            node_props = dict(n) if not isinstance(n, dict) else n
            nid = str(node_props.get("id"))
            if not nid or nid in seen_node_ids:
                continue
            seen_node_ids.add(nid)

            node_data = CytoscapeNodeData(
                id=nid,
                label=str(node_props.get("canonical_name", "")),
                entity_type=str(node_props.get("entity_type", "PERSON")).upper(),
                case_id=str(node_props.get("case_id", case_id)),
                status=str(node_props.get("status", "ACTIVE")),
                risk_score=float(node_props["risk_score"]) if "risk_score" in node_props and node_props["risk_score"] is not None else None,
            )
            cytoscape_nodes.append(CytoscapeNode(data=node_data))

        # Step 5: Normalize and deduplicate edges into Cytoscape format
        seen_edge_ids = set()
        cytoscape_edges: List[CytoscapeEdge] = []
        predicted_count = 0

        for r in raw_edges:
            if not r:
                continue
            edge_props = dict(r) if not isinstance(r, dict) else r
            eid = str(edge_props.get("id"))
            if not eid or eid in seen_edge_ids:
                continue
            seen_edge_ids.add(eid)

            is_pred = bool(edge_props.get("is_predicted", False))
            if is_pred:
                predicted_count += 1

            source_id = str(edge_props.get("source_id", ""))
            target_id = str(edge_props.get("target_id", ""))

            # If edges are Neo4j relationship objects with start_node/end_node
            if hasattr(r, "start_node") and hasattr(r.start_node, "get"):
                source_id = str(r.start_node.get("id", source_id))
            if hasattr(r, "end_node") and hasattr(r.end_node, "get"):
                target_id = str(r.end_node.get("id", target_id))

            edge_data = CytoscapeEdgeData(
                id=eid,
                source=source_id,
                target=target_id,
                type=str(edge_props.get("type", "RELATIONSHIP")).upper(),
                confidence_score=float(edge_props.get("confidence_score", 1.0)),
                is_predicted=is_pred,
                provenance_count=int(edge_props.get("provenance_count", 1)),
                style_line="dashed" if is_pred else "solid",
            )
            cytoscape_edges.append(CytoscapeEdge(data=edge_data))

        # Step 6: Assemble stats and response
        stats = GraphStats(
            node_count=len(cytoscape_nodes),
            edge_count=len(cytoscape_edges),
            predicted_edge_count=predicted_count,
        )

        return CaseGraphResponse(
            nodes=cytoscape_nodes,
            edges=cytoscape_edges,
            stats=stats,
        )
