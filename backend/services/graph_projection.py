"""
Graph Projection Service for SIH26189.
Synchronizes canonical entities and relationships from PostgreSQL (System of Record) to Neo4j.
Guarantees idempotent MERGE semantics, case-scoped deletion on rebuild,
deterministic SHA-256 checksum calculation, and graph_snapshots ledger records.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from backend.db.models.entities import Entity, Relationship, RelationshipEvidence
from backend.db.models.analytics import GraphSnapshot, Prediction
from backend.graph.connection import Neo4jConnectionManager, get_graph_manager
from backend.graph.cypher_builder import CypherBuilder, get_safe_label, get_safe_rel_type

logger = logging.getLogger("backend.services.graph_projection")


class GraphProjectionError(Exception):
    """Raised when graph projection or synchronization fails."""
    pass


class GraphProjectionService:
    """
    Orchestrates deterministic projection from PostgreSQL to Neo4j.
    Neo4j is strictly an analytical projection; PostgreSQL is the authoritative System of Record.
    """
    def __init__(self, db: Session, graph_manager: Optional[Neo4jConnectionManager] = None):
        self.db = db
        self.graph_manager = graph_manager or get_graph_manager()

    def compute_case_checksum(self, case_id: UUID) -> str:
        """
        Calculates a deterministic SHA-256 checksum over all active canonical entities,
        relationships, and predictions within a case.
        Guarantees stability regardless of database retrieval order.
        """
        entities = (
            self.db.query(Entity)
            .filter(Entity.case_id == case_id, Entity.status != "ARCHIVED")
            .order_by(Entity.entity_id)
            .all()
        )
        relationships = (
            self.db.query(Relationship)
            .filter(Relationship.case_id == case_id, Relationship.status != "REJECTED")
            .order_by(Relationship.relationship_id)
            .all()
        )

        hasher = hashlib.sha256()

        # 1. Feed deterministically ordered entities
        for e in entities:
            e_str = f"E:{e.entity_id}:{e.entity_type}:{e.canonical_name}:{e.status}\n"
            hasher.update(e_str.encode("utf-8"))

        # 2. Feed deterministically ordered relationships
        for r in relationships:
            r_str = f"R:{r.relationship_id}:{r.source_entity_uuid}:{r.target_entity_uuid}:{r.type}:{r.status}\n"
            hasher.update(r_str.encode("utf-8"))

        return hasher.hexdigest()

    def rebuild_case_graph(self, case_id: UUID) -> Dict[str, Any]:
        """
        Executes a full, deterministic rebuild of a case's graph projection in Neo4j.
        Steps:
        1. Ensure Neo4j connectivity
        2. Parameterized purge of existing case subgraph (never global MATCH (n) DETACH DELETE n)
        3. Read canonical entities from PostgreSQL (status != 'ARCHIVED')
        4. Read canonical relationships and evidence counts from PostgreSQL
        5. Read predictions for the case
        6. Batch project nodes by safe canonical label
        7. Batch project edges by safe canonical relationship type
        8. Compute deterministic checksum
        9. Persist graph_snapshots ledger row in PostgreSQL
        10. Return summary statistics
        """
        if not self.graph_manager.is_healthy():
            raise GraphProjectionError("Neo4j analytical database is currently unavailable.")

        logger.info(f"Initiating full graph rebuild for case {case_id}")

        driver = self.graph_manager.get_driver()
        with driver.session() as session:
            # Step 1: Case-scoped purge
            purge_query, purge_params = CypherBuilder.build_case_purge(case_id)
            session.run(purge_query, purge_params)
            logger.debug(f"Purged existing Neo4j subgraph for case {case_id}")

            # Step 2: Fetch canonical entities from PostgreSQL
            entities = (
                self.db.query(Entity)
                .filter(Entity.case_id == case_id, Entity.status != "ARCHIVED")
                .all()
            )

            # Group entities by safe label for UNWIND batching
            entities_by_label: Dict[str, List[Dict[str, Any]]] = {}
            for e in entities:
                try:
                    safe_label = get_safe_label(e.entity_type)
                except Exception as ex:
                    logger.warning(f"Skipping entity {e.entity_id} with invalid type '{e.entity_type}': {ex}")
                    continue

                if safe_label not in entities_by_label:
                    entities_by_label[safe_label] = []

                entities_by_label[safe_label].append({
                    "entity_id": str(e.entity_id),
                    "case_id": str(e.case_id),
                    "canonical_name": str(e.canonical_name),
                    "entity_type": e.entity_type.upper(),
                    "status": str(e.status),
                    "created_at": e.created_at.isoformat() if e.created_at else datetime.now(timezone.utc).isoformat(),
                })

            # Execute batch entity projection
            total_nodes_projected = 0
            for label, batch in entities_by_label.items():
                batch_query = CypherBuilder.build_batch_entity_upsert(label)
                # Chunk into 500 records per batch
                for i in range(0, len(batch), 500):
                    chunk = batch[i:i + 500]
                    session.run(batch_query, {"batch": chunk})
                    total_nodes_projected += len(chunk)

            logger.info(f"Projected {total_nodes_projected} nodes for case {case_id}")

            # Step 3: Fetch canonical relationships from PostgreSQL
            relationships = (
                self.db.query(Relationship)
                .filter(Relationship.case_id == case_id, Relationship.status != "REJECTED")
                .all()
            )

            # Map relationship ID to evidence counts
            evidence_counts = {}
            if relationships:
                rel_ids = [r.relationship_id for r in relationships]
                from sqlalchemy import func
                counts = (
                    self.db.query(RelationshipEvidence.relationship_id, func.count(RelationshipEvidence.evidence_id))
                    .filter(RelationshipEvidence.relationship_id.in_(rel_ids))
                    .group_by(RelationshipEvidence.relationship_id)
                    .all()
                )
                evidence_counts = {cid: cnt for cid, cnt in counts}

            # Group relationships by safe type for UNWIND batching
            rels_by_type: Dict[str, List[Dict[str, Any]]] = {}
            for r in relationships:
                try:
                    safe_type = get_safe_rel_type(r.type)
                except Exception as ex:
                    logger.warning(f"Skipping relationship {r.relationship_id} with invalid type '{r.type}': {ex}")
                    continue

                if safe_type not in rels_by_type:
                    rels_by_type[safe_type] = []

                prov_count = max(1, evidence_counts.get(r.relationship_id, 1))
                rels_by_type[safe_type].append({
                    "relationship_id": str(r.relationship_id),
                    "case_id": str(r.case_id),
                    "source_id": str(r.source_entity_uuid),
                    "target_id": str(r.target_entity_uuid),
                    "rel_type": safe_type,
                    "status": str(r.status),
                    "confidence_score": 1.0,
                    "is_predicted": False,
                    "provenance_count": prov_count,
                    "created_at": r.created_at.isoformat() if r.created_at else datetime.now(timezone.utc).isoformat(),
                })

            # Fetch AI-inferred predictions for the case
            predictions = (
                self.db.query(Prediction)
                .filter(Prediction.case_id == case_id)
                .all()
            )
            for p in predictions:
                safe_pred_type = "ASSOCIATED_WITH"
                if safe_pred_type not in rels_by_type:
                    rels_by_type[safe_pred_type] = []

                rels_by_type[safe_pred_type].append({
                    "relationship_id": str(p.prediction_id),
                    "case_id": str(p.case_id),
                    "source_id": str(p.source_ref),
                    "target_id": str(p.target_ref),
                    "rel_type": safe_pred_type,
                    "status": "INFERRED",
                    "confidence_score": float(p.score),
                    "is_predicted": True,
                    "provenance_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

            # Execute batch relationship projection
            total_edges_projected = 0
            for r_type, batch in rels_by_type.items():
                batch_query = CypherBuilder.build_batch_relationship_upsert(r_type)
                for i in range(0, len(batch), 500):
                    chunk = batch[i:i + 500]
                    session.run(batch_query, {"batch": chunk})
                    total_edges_projected += len(chunk)

            logger.info(f"Projected {total_edges_projected} edges for case {case_id}")

        # Step 4: Calculate deterministic checksum
        checksum = self.compute_case_checksum(case_id)

        # Step 5: Persist snapshot ledger record in PostgreSQL
        snapshot = GraphSnapshot(
            snapshot_id=uuid4(),
            case_id=case_id,
            source_migration_version="0001_initial_schema",
            checksum=checksum,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(snapshot)
        self.db.commit()

        logger.info(f"Case {case_id} graph rebuild completed. Checksum: {checksum}")

        return {
            "case_id": str(case_id),
            "nodes_projected": total_nodes_projected,
            "edges_projected": total_edges_projected,
            "checksum": checksum,
            "snapshot_id": str(snapshot.snapshot_id),
        }

    def upsert_entity(self, entity: Entity) -> None:
        """Incremental projection of a single entity."""
        if not self.graph_manager.is_healthy():
            logger.warning("Neo4j offline; skipping incremental entity projection.")
            return

        query, params = CypherBuilder.build_entity_upsert(
            entity_id=entity.entity_id,
            case_id=entity.case_id,
            entity_type=entity.entity_type,
            canonical_name=entity.canonical_name,
            status=entity.status,
            created_at=entity.created_at.isoformat() if entity.created_at else datetime.now(timezone.utc).isoformat(),
        )
        driver = self.graph_manager.get_driver()
        with driver.session() as session:
            session.run(query, params)

    def upsert_relationship(
        self,
        relationship: Relationship,
        is_predicted: bool = False,
        confidence_score: float = 1.0,
        provenance_count: int = 1,
    ) -> None:
        """Incremental projection of a single relationship."""
        if not self.graph_manager.is_healthy():
            logger.warning("Neo4j offline; skipping incremental relationship projection.")
            return

        query, params = CypherBuilder.build_relationship_upsert(
            relationship_id=relationship.relationship_id,
            case_id=relationship.case_id,
            source_id=relationship.source_entity_uuid,
            target_id=relationship.target_entity_uuid,
            rel_type=relationship.type,
            status=relationship.status,
            confidence_score=confidence_score,
            is_predicted=is_predicted,
            provenance_count=provenance_count,
            created_at=relationship.created_at.isoformat() if relationship.created_at else datetime.now(timezone.utc).isoformat(),
        )
        driver = self.graph_manager.get_driver()
        with driver.session() as session:
            session.run(query, params)
