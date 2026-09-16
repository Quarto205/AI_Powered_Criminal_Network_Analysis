#!/usr/bin/env python3
"""
SIH26189 — Agent 3 Standalone Development Environment Reset Script
Deletes the specific deterministic demo dataset (Case A and Case B).
Does NOT perform global destructive operations on the whole database.
"""

import os
import sys
import uuid

# Add the project root to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.db.session import get_engine, get_session_factory
from backend.db.models.identity import Case, User
from backend.db.models.entities import Entity, Relationship

from neo4j import GraphDatabase, basic_auth

# --- Deterministic ID Generation ---
NAMESPACE_AGENT3_SEED = uuid.UUID("12345678-1234-5678-1234-567812345678")

def deterministic_uuid(name: str) -> uuid.UUID:
    """Returns a deterministic UUID based on a string name."""
    return uuid.uuid5(NAMESPACE_AGENT3_SEED, name)

POSTGRES_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:your_secure_postgres_password@localhost:5432/sih26189"
)
from dotenv import load_dotenv
load_dotenv()
from backend.config.neo4j import Neo4jSettings
neo4j_settings = Neo4jSettings.from_env()

NEO4J_URI = neo4j_settings.neo4j_uri
NEO4J_USER = neo4j_settings.neo4j_user
NEO4J_PASSWORD = neo4j_settings.neo4j_password

def reset_demo():
    print("Warning: This will delete demo Cases A and B from Postgres and Neo4j.")
    case_a_id = deterministic_uuid("CASE-A")
    case_b_id = deterministic_uuid("CASE-B")
    
    print(f"Deleting Case A: {case_a_id}")
    print(f"Deleting Case B: {case_b_id}")

    # 1. Postgres Delete (Cascade should handle relationships/entities)
    engine = get_engine(custom_url=POSTGRES_URL)
    db = get_session_factory(engine)()
    try:
        from backend.db.models.entities import Entity, Relationship
        
        # Delete dependent items for Case A and B first
        for cid in [case_a_id, case_b_id]:
            db.query(Relationship).filter(Relationship.case_id == cid).delete(synchronize_session=False)
            db.query(Entity).filter(Entity.case_id == cid).delete(synchronize_session=False)
            db.query(Case).filter(Case.case_id == cid).delete(synchronize_session=False)
        
            
        db.commit()
        print("[OK] PostgreSQL demo cases deleted (cascaded).")
    except Exception as e:
        print(f"[FAIL] Failed to delete from PostgreSQL: {e}")
        db.rollback()
    finally:
        db.close()

    # 2. Neo4j Delete
    driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session(database=neo4j_settings.neo4j_database) as session:
            # Delete relationships first
            session.run("MATCH ()-[r]->() WHERE r.case_id IN [$ca, $cb] DELETE r", ca=str(case_a_id), cb=str(case_b_id))
            # Delete nodes
            session.run("MATCH (n) WHERE n.case_id IN [$ca, $cb] DELETE n", ca=str(case_a_id), cb=str(case_b_id))
        print("[OK] Neo4j demo graph nodes and edges deleted safely.")
    except Exception as e:
        print(f"[FAIL] Failed to delete from Neo4j: {e}")
    finally:
        driver.close()

    print("Reset completed.")

if __name__ == "__main__":
    reset_demo()
