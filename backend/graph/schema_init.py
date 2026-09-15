"""
Idempotent Neo4j Schema Initializer for SIH26189.
Creates composite uniqueness constraints and case-scoped indexes.
Guarantees idempotency using 'IF NOT EXISTS'.
Never drops existing constraints or destroys graph data during startup.
"""

import logging
from typing import List
from backend.graph.connection import Neo4jConnectionManager, get_graph_manager
from backend.graph.cypher_builder import CANONICAL_ENTITY_LABELS

logger = logging.getLogger("backend.graph.schema_init")


# Composite uniqueness constraints per label (id + case_id)
# Neo4j 5.x+ syntax: CREATE CONSTRAINT name IF NOT EXISTS FOR (n:Label) REQUIRE (n.id, n.case_id) IS UNIQUE
CONSTRAINT_STATEMENTS: List[str] = [
    f"CREATE CONSTRAINT cst_{label.lower()}_id_case IF NOT EXISTS "
    f"FOR (n:{label}) REQUIRE (n.id, n.case_id) IS UNIQUE"
    for label in CANONICAL_ENTITY_LABELS.values()
]

# Additional Entity super-label constraint if supported
CONSTRAINT_STATEMENTS.append(
    "CREATE CONSTRAINT cst_entity_id_case IF NOT EXISTS "
    "FOR (n:Entity) REQUIRE (n.id, n.case_id) IS UNIQUE"
)

# Case-scoped lookup indexes
INDEX_STATEMENTS: List[str] = [
    "CREATE INDEX idx_entity_case_id IF NOT EXISTS FOR (n:Entity) ON (n.case_id)",
    "CREATE INDEX idx_person_case_id IF NOT EXISTS FOR (n:Person) ON (n.case_id)",
    "CREATE INDEX idx_phone_case_id IF NOT EXISTS FOR (n:Phone) ON (n.case_id)",
    "CREATE INDEX idx_bankaccount_case_id IF NOT EXISTS FOR (n:BankAccount) ON (n.case_id)",
    "CREATE INDEX idx_vehicle_case_id IF NOT EXISTS FOR (n:Vehicle) ON (n.case_id)",
    "CREATE INDEX idx_organization_case_id IF NOT EXISTS FOR (n:Organization) ON (n.case_id)",
    "CREATE INDEX idx_location_case_id IF NOT EXISTS FOR (n:Location) ON (n.case_id)",
]


def init_graph_schema(manager: Neo4jConnectionManager = None) -> bool:
    """
    Executes idempotent DDL statements to set up constraints and indexes.
    Returns True if initialized, False if Neo4j is unavailable or fails.
    """
    mgr = manager or get_graph_manager()
    if not mgr.is_healthy():
        logger.warning("Skipping Neo4j schema initialization: database is not available.")
        return False

    try:
        with mgr.get_session() as session:
            # 1. Initialize constraints
            for stmt in CONSTRAINT_STATEMENTS:
                try:
                    session.run(stmt)
                    logger.debug(f"Executed constraint statement: {stmt}")
                except Exception as e:
                    logger.warning(f"Constraint creation notice ({stmt}): {str(e)}")

            # 2. Initialize indexes
            for stmt in INDEX_STATEMENTS:
                try:
                    session.run(stmt)
                    logger.debug(f"Executed index statement: {stmt}")
                except Exception as e:
                    logger.warning(f"Index creation notice ({stmt}): {str(e)}")

        logger.info("Neo4j graph schema constraints and indexes initialized successfully.")
        return True
    except Exception as e:
        logger.error("Failed to initialize Neo4j schema", exc_info=True)
        return False
