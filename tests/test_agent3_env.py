import pytest
import os
import uuid
from sqlalchemy.orm import Session
from neo4j import GraphDatabase, basic_auth

from backend.db.session import get_engine, get_session_factory
from backend.db.models.entities import Entity, Relationship

# --- Helper Configuration ---
POSTGRES_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:your_secure_postgres_password@localhost:5432/sih26189"
)
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "your_secure_neo4j_password")

NAMESPACE_AGENT3_SEED = uuid.UUID("12345678-1234-5678-1234-567812345678")

def deterministic_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE_AGENT3_SEED, name)

CASE_A_ID = deterministic_uuid("CASE-A")
CASE_B_ID = deterministic_uuid("CASE-B")

@pytest.fixture(scope="module")
def db_session():
    engine = get_engine(custom_url=POSTGRES_URL)
    session = get_session_factory(engine)()
    yield session
    session.close()

@pytest.fixture(scope="module")
def neo4j_driver():
    driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    yield driver
    driver.close()

def test_environment_availability(db_session, neo4j_driver):
    # Test DB
    assert db_session.execute("SELECT 1").scalar() == 1
    
    # Test Neo4j
    neo4j_driver.verify_connectivity()

def test_python_packages():
    # Verify imports
    import networkx as nx
    import torch
    import torch_geometric as pyg
    
    assert nx.__version__ is not None
    assert torch.__version__ is not None
    assert pyg.__version__ is not None

def test_postgresql_consistency(db_session):
    # Ensure entities and relationships exist for cases
    ent_a = db_session.query(Entity).filter(Entity.case_id == CASE_A_ID).count()
    rel_a = db_session.query(Relationship).filter(Relationship.case_id == CASE_A_ID).count()
    
    assert ent_a > 0, "CASE-A should have entities"
    assert rel_a > 0, "CASE-A should have relationships"

def test_case_isolation(neo4j_driver):
    with neo4j_driver.session() as session:
        # Check cross-case edges
        result = session.run("""
        MATCH (a)-[r]-(b)
        WHERE a.case_id = $ca AND b.case_id = $cb
        RETURN count(r) AS c
        """, ca=str(CASE_A_ID), cb=str(CASE_B_ID))
        cross_edges = result.single()["c"]
        
        assert cross_edges == 0, "Case A and Case B must be isolated"

def test_neo4j_postgres_consistency(db_session, neo4j_driver):
    pg_ent_a = db_session.query(Entity).filter(Entity.case_id == CASE_A_ID).count()
    pg_rel_a = db_session.query(Relationship).filter(Relationship.case_id == CASE_A_ID).count()
    
    with neo4j_driver.session() as session:
        n4j_ent_a = session.run("MATCH (n) WHERE n.case_id = $cid RETURN count(n) AS c", cid=str(CASE_A_ID)).single()["c"]
        n4j_rel_a = session.run("MATCH ()-[r]->() WHERE r.case_id = $cid RETURN count(r) AS c", cid=str(CASE_A_ID)).single()["c"]
        
    assert pg_ent_a == n4j_ent_a, f"Node count mismatch: PG={pg_ent_a}, Neo4j={n4j_ent_a}"
    assert pg_rel_a == n4j_rel_a, f"Edge count mismatch: PG={pg_rel_a}, Neo4j={n4j_rel_a}"

def test_seed_determinism(neo4j_driver):
    # The IDs in neo4j should match the deterministic ones we expect
    p_central_uuid = str(deterministic_uuid(f"{CASE_A_ID}-p_central"))
    
    with neo4j_driver.session() as session:
        res = session.run("MATCH (n {entity_id: $uid}) RETURN count(n) AS c", uid=p_central_uuid)
        assert res.single()["c"] == 1, "Deterministic central node not found"
