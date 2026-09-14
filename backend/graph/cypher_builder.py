"""
Secure Parameterized Cypher Query Builder for SIH26189.
Guarantees 100% parameterization with ZERO user-controlled string interpolation.
Enforces closed allow-lists for entity labels and relationship types.
"""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID


# Closed Allow-List for Canonical Entity Node Labels
CANONICAL_ENTITY_LABELS: Dict[str, str] = {
    "PERSON": "Person",
    "PHONE": "Phone",
    "BANK_ACCOUNT": "BankAccount",
    "VEHICLE": "Vehicle",
    "ORGANIZATION": "Organization",
    "LOCATION": "Location",
    "CASE": "Case",
    "EVIDENCE": "Evidence",
    "OFFENSE": "Offense",
}

# Closed Allow-List for Canonical Relationship Types
CANONICAL_RELATIONSHIP_TYPES: Set[str] = {
    "CONTACTED",
    "COMMUNICATED_WITH",
    "TRANSFERRED_TO",
    "OWNS",
    "OWNED_BY",
    "USED_BY",
    "ACCUSED_IN",
    "ASSOCIATED_WITH",
    "LOCATED_AT",
    "PINGED_TOWER",
    "REGISTERED_TO",
    "SCANNED_AT",
    "AFFILIATED_WITH",
    "CONTAINS",
    "SUPPORTS",
    "REFUTES",
    "KNOWS",
    "HAS_INCIDENT",
}


class CypherValidationError(ValueError):
    """Raised when an unallowlisted or malicious label or relationship type is provided."""
    pass


def get_safe_label(entity_type: str) -> str:
    """
    Validates and maps an entity type string to a safe canonical PascalCase label.
    Raises CypherValidationError if entity_type is not strictly in the allow-list.
    """
    normalized = entity_type.strip().upper()
    if normalized not in CANONICAL_ENTITY_LABELS:
        raise CypherValidationError(
            f"Invalid entity type '{entity_type}'. Must be one of: {sorted(CANONICAL_ENTITY_LABELS.keys())}"
        )
    return CANONICAL_ENTITY_LABELS[normalized]


def get_safe_rel_type(rel_type: str) -> str:
    """
    Validates a relationship type string against the canonical allow-list.
    Raises CypherValidationError if rel_type is not strictly in the allow-list.
    """
    normalized = rel_type.strip().upper()
    if normalized not in CANONICAL_RELATIONSHIP_TYPES:
        raise CypherValidationError(
            f"Invalid relationship type '{rel_type}'. Must be one of: {sorted(CANONICAL_RELATIONSHIP_TYPES)}"
        )
    return normalized


# Static Idempotent Cypher Templates for Entity Node MERGE
ENTITY_MERGE_CYPHER_TEMPLATES: Dict[str, str] = {
    label: (
        f"MERGE (n:Entity:{label} {{id: $entity_id, case_id: $case_id}}) "
        "ON CREATE SET "
        "  n.canonical_name = $canonical_name, "
        "  n.entity_type = $entity_type, "
        "  n.status = $status, "
        "  n.created_at = $created_at "
        "ON MATCH SET "
        "  n.canonical_name = $canonical_name, "
        "  n.status = $status"
    )
    for label in CANONICAL_ENTITY_LABELS.values()
}

# Static Idempotent Cypher Templates for Relationship Edge MERGE
# Enforces typed edge labels without string interpolation at runtime
RELATIONSHIP_MERGE_CYPHER_TEMPLATES: Dict[str, str] = {
    rel_type: (
        "MATCH (src:Entity {id: $source_id, case_id: $case_id}) "
        "MATCH (tgt:Entity {id: $target_id, case_id: $case_id}) "
        f"MERGE (src)-[r:{rel_type} {{id: $relationship_id, case_id: $case_id}}]->(tgt) "
        "ON CREATE SET "
        "  r.type = $rel_type, "
        "  r.status = $status, "
        "  r.confidence_score = $confidence_score, "
        "  r.is_predicted = $is_predicted, "
        "  r.provenance_count = $provenance_count, "
        "  r.created_at = $created_at "
        "ON MATCH SET "
        "  r.status = $status, "
        "  r.confidence_score = $confidence_score, "
        "  r.provenance_count = $provenance_count"
    )
    for rel_type in CANONICAL_RELATIONSHIP_TYPES
}


class CypherBuilder:
    """
    Builder generating fixed, parameterized Cypher statements and parameter dicts.
    Guarantees that user inputs never reach the Cypher statement text.
    """

    @staticmethod
    def build_entity_upsert(
        entity_id: UUID,
        case_id: UUID,
        entity_type: str,
        canonical_name: str,
        status: str,
        created_at: str,
    ) -> (str, Dict[str, Any]):
        """Generates parameterized Cypher query and parameters for single entity upsert."""
        safe_label = get_safe_label(entity_type)
        query = ENTITY_MERGE_CYPHER_TEMPLATES[safe_label]
        params = {
            "entity_id": str(entity_id),
            "case_id": str(case_id),
            "entity_type": entity_type.upper(),
            "canonical_name": str(canonical_name),
            "status": str(status),
            "created_at": str(created_at),
        }
        return query, params

    @staticmethod
    def build_relationship_upsert(
        relationship_id: UUID,
        case_id: UUID,
        source_id: UUID,
        target_id: UUID,
        rel_type: str,
        status: str,
        confidence_score: float,
        is_predicted: bool,
        provenance_count: int,
        created_at: str,
    ) -> (str, Dict[str, Any]):
        """Generates parameterized Cypher query and parameters for relationship upsert."""
        safe_rel = get_safe_rel_type(rel_type)
        query = RELATIONSHIP_MERGE_CYPHER_TEMPLATES[safe_rel]
        params = {
            "relationship_id": str(relationship_id),
            "case_id": str(case_id),
            "source_id": str(source_id),
            "target_id": str(target_id),
            "rel_type": safe_rel,
            "status": str(status),
            "confidence_score": float(confidence_score),
            "is_predicted": bool(is_predicted),
            "provenance_count": int(provenance_count),
            "created_at": str(created_at),
        }
        return query, params

    @staticmethod
    def build_case_purge(case_id: UUID) -> (str, Dict[str, Any]):
        """
        Builds parameterized Cypher to purge exclusively the case's subgraph.
        STRICT INVARIANT: Never purges global graph (never MATCH (n) DETACH DELETE n).
        """
        query = "MATCH (n {case_id: $case_id}) DETACH DELETE n"
        params = {"case_id": str(case_id)}
        return query, params

    @staticmethod
    def build_batch_entity_upsert(safe_label: str) -> str:
        """
        Returns parameterized batch UNWIND Cypher for a safe canonical label.
        """
        if safe_label not in CANONICAL_ENTITY_LABELS.values():
            raise CypherValidationError(f"Invalid label '{safe_label}'")
        return (
            "UNWIND $batch AS row "
            f"MERGE (n:Entity:{safe_label} {{id: row.entity_id, case_id: row.case_id}}) "
            "ON CREATE SET "
            "  n.canonical_name = row.canonical_name, "
            "  n.entity_type = row.entity_type, "
            "  n.status = row.status, "
            "  n.created_at = row.created_at "
            "ON MATCH SET "
            "  n.canonical_name = row.canonical_name, "
            "  n.status = row.status"
        )

    @staticmethod
    def build_batch_relationship_upsert(safe_rel_type: str) -> str:
        """
        Returns parameterized batch UNWIND Cypher for a safe canonical relationship type.
        """
        if safe_rel_type not in CANONICAL_RELATIONSHIP_TYPES:
            raise CypherValidationError(f"Invalid relationship type '{safe_rel_type}'")
        return (
            "UNWIND $batch AS row "
            "MATCH (src:Entity {id: row.source_id, case_id: row.case_id}) "
            "MATCH (tgt:Entity {id: row.target_id, case_id: row.case_id}) "
            f"MERGE (src)-[r:{safe_rel_type} {{id: row.relationship_id, case_id: row.case_id}}]->(tgt) "
            "ON CREATE SET "
            "  r.type = row.rel_type, "
            "  r.status = row.status, "
            "  r.confidence_score = row.confidence_score, "
            "  r.is_predicted = row.is_predicted, "
            "  r.provenance_count = row.provenance_count, "
            "  r.created_at = row.created_at "
            "ON MATCH SET "
            "  r.status = row.status, "
            "  r.confidence_score = row.confidence_score, "
            "  r.provenance_count = row.provenance_count"
        )

    @staticmethod
    def build_case_graph_query(
        case_id: UUID,
        depth: int = 2,
        focus_entity_id: Optional[UUID] = None,
        allowed_entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        include_predicted: bool = True,
        limit: int = 300,
    ) -> (str, Dict[str, Any]):
        """
        Constructs a safe, bounded graph query strictly scoped to case_id.
        Depth is bounded between 1 and 3.
        """
        depth = max(1, min(3, depth))
        limit = max(1, min(1000, limit))

        params: Dict[str, Any] = {
            "case_id": str(case_id),
            "min_confidence": float(min_confidence),
            "limit": int(limit),
        }

        # Filter clauses
        pred_filter = "" if include_predicted else "AND r.is_predicted = false"

        type_filter = ""
        if allowed_entity_types:
            safe_types = [t.strip().upper() for t in allowed_entity_types if t.strip().upper() in CANONICAL_ENTITY_LABELS]
            if safe_types:
                params["allowed_types"] = safe_types
                type_filter = "AND n.entity_type IN $allowed_types"

        if focus_entity_id is not None:
            params["focus_id"] = str(focus_entity_id)
            # Neighborhood traversal around focus node up to specified depth
            query = (
                f"MATCH path = (start:Entity {{id: $focus_id, case_id: $case_id}})-[r*1..{depth}]-(target:Entity {{case_id: $case_id}}) "
                f"WHERE all(rel IN relationships(path) WHERE rel.case_id = $case_id AND rel.confidence_score >= $min_confidence {pred_filter}) "
                "WITH nodes(path) AS path_nodes, relationships(path) AS path_rels "
                "UNWIND path_nodes AS n "
                "WITH collect(DISTINCT n) AS all_nodes, path_rels "
                "UNWIND path_rels AS r "
                "RETURN all_nodes AS nodes, collect(DISTINCT r) AS edges "
                "LIMIT $limit"
            )
        else:
            # Whole case graph traversal up to limit
            query = (
                "MATCH (n:Entity {case_id: $case_id}) "
                f"WHERE 1=1 {type_filter} "
                "WITH n LIMIT $limit "
                "OPTIONAL MATCH (n)-[r {case_id: $case_id}]-(m:Entity {case_id: $case_id}) "
                f"WHERE r.confidence_score >= $min_confidence {pred_filter} "
                "RETURN collect(DISTINCT n) AS nodes, collect(DISTINCT r) AS edges"
            )

        return query, params
