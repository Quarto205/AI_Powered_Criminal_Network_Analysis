"""
Neo4j Repository layer for SIH26189.
Handles initialization of graph schema constraints and basic operational queries.
"""

import logging
from neo4j.exceptions import ClientError
from backend.graph.connection import Neo4jConnectionManager, get_graph_manager
from backend.graph.cypher_builder import CANONICAL_ENTITY_LABELS

logger = logging.getLogger("backend.repositories.neo4j_repository")


class Neo4jRepository:
    """
    Repository for managing Neo4j schema definitions and core constraints.
    """
    def __init__(self, graph_manager: Neo4jConnectionManager = None):
        self.graph_manager = graph_manager or get_graph_manager()

    def initialize_constraints(self) -> None:
        """
        Idempotently creates unique constraints for all canonical entity labels
        on the 'id' property and 'case_id' index.
        """
        if not self.graph_manager.is_healthy():
            logger.warning("Neo4j is currently unavailable; skipping constraint initialization.")
            return

        with self.graph_manager.get_session() as session:
            for label in CANONICAL_ENTITY_LABELS.values():
                # Enforce globally unique ID per entity type
                unique_constraint = f"CREATE CONSTRAINT constraint_{label}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
                # Create an index on case_id for fast subgraph traversal
                case_index = f"CREATE INDEX index_{label}_case_id IF NOT EXISTS FOR (n:{label}) ON (n.case_id)"
                
                try:
                    session.run(unique_constraint)
                    session.run(case_index)
                except ClientError as e:
                    logger.warning(f"Error applying constraints for {label}: {e}")
            
            logger.info("Successfully initialized all Neo4j schema constraints and indices.")
