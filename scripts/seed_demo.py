#!/usr/bin/env python3
"""
SIH26189 — Agent 3 Standalone Development Environment Seed Script
Creates a deterministic mock dataset (Case A and Case B) to develop Agent 3 analytics.
Must be idempotent and not perform global destructive operations.
"""

import os
import sys
import uuid
import json
from datetime import datetime, timezone

# Add the project root to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.db.session import get_engine, get_session_factory, create_all_tables
from backend.db.models.identity import Case, User
from backend.db.models.entities import (
    Entity,
    Relationship,
    Event,
    Communication,
    Transaction,
    Location,
    Vehicle,
    Organization,
    Phone,
    Account,
)
from backend.db.models.analytics import ModelRun, Prediction, RiskScore, Alert, GraphSnapshot

from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable

# --- Deterministic ID Generation ---
NAMESPACE_AGENT3_SEED = uuid.UUID("12345678-1234-5678-1234-567812345678")

def deterministic_uuid(name: str) -> uuid.UUID:
    """Returns a deterministic UUID based on a string name."""
    return uuid.uuid5(NAMESPACE_AGENT3_SEED, name)

# --- Config & Connections ---
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

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))

# --- Verification & Setup ---
def verify_services():
    print("Verifying services...")
    engine = get_engine(custom_url=POSTGRES_URL)
    try:
        engine.connect().close()
        print("[OK] PostgreSQL reachable.")
        # Ensure tables exist
        create_all_tables(engine)
    except Exception as e:
        print(f"[FAIL] PostgreSQL unreachable: {e}")
        sys.exit(1)
        
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        print("[OK] Neo4j reachable.")
        
        with driver.session(database=neo4j_settings.neo4j_database) as session:
            result = session.run("CALL gds.version() YIELD gdsVersion")
            gds_version = result.single()["gdsVersion"]
            print(f"[OK] Neo4j GDS available (version: {gds_version}).")
    except ServiceUnavailable as e:
        print(f"[FAIL] Neo4j unreachable: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[WARNING] Neo4j GDS might not be available: {e}")

    return get_session_factory(engine)(), get_neo4j_driver()

def ensure_constraints(driver):
    queries = [
        "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.entity_id IS UNIQUE",
        "CREATE CONSTRAINT phone_id_unique IF NOT EXISTS FOR (n:Phone) REQUIRE n.entity_id IS UNIQUE",
        "CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (n:BankAccount) REQUIRE n.entity_id IS UNIQUE",
        "CREATE CONSTRAINT vehicle_id_unique IF NOT EXISTS FOR (n:Vehicle) REQUIRE n.entity_id IS UNIQUE",
        "CREATE CONSTRAINT org_id_unique IF NOT EXISTS FOR (n:Organization) REQUIRE n.entity_id IS UNIQUE",
        "CREATE CONSTRAINT loc_id_unique IF NOT EXISTS FOR (n:Location) REQUIRE n.entity_id IS UNIQUE",
    ]
    with driver.session(database=neo4j_settings.neo4j_database) as session:
        for q in queries:
            try:
                session.run(q)
            except Exception:
                pass # Already exists

# --- Postgres Seeding ---
def get_or_create_user(db: Session, user_name: str) -> User:
    uid = deterministic_uuid(user_name)
    user = db.query(User).filter(User.user_id == uid).first()
    if not user:
        user = User(
            user_id=uid,
            email=f"{user_name.lower()}@investigation.local",
            username=user_name,
            password_hash="synthetic_hash",
            account_status="ACTIVE",
        )
        db.add(user)
        db.commit()
    return user

def get_or_create_case(db: Session, case_code: str, title: str, user_id: uuid.UUID) -> Case:
    cid = deterministic_uuid(case_code)
    case = db.query(Case).filter(Case.case_id == cid).first()
    if not case:
        case = Case(
            case_id=cid,
            case_code=case_code,
            title=title,
            status="OPEN",
            jurisdiction="SYNTHETIC",
            created_by=user_id
        )
        db.add(case)
        db.commit()
    return case

def get_or_create_entity(db: Session, case_id: uuid.UUID, entity_type: str, canonical_name: str, e_id: str) -> Entity:
    uid = deterministic_uuid(f"{case_id}-{e_id}")
    entity = db.query(Entity).filter(Entity.entity_id == uid).first()
    if not entity:
        entity = Entity(
            entity_id=uid,
            case_id=case_id,
            entity_type=entity_type,
            canonical_name=canonical_name,
            status="ACTIVE"
        )
        db.add(entity)
    return entity

def get_or_create_relationship(db: Session, case_id: uuid.UUID, source_id: uuid.UUID, target_id: uuid.UUID, rel_type: str, r_id: str) -> Relationship:
    uid = deterministic_uuid(f"{case_id}-{r_id}")
    rel = db.query(Relationship).filter(Relationship.relationship_id == uid).first()
    if not rel:
        rel = Relationship(
            relationship_id=uid,
            case_id=case_id,
            source_entity_uuid=source_id,
            target_entity_uuid=target_id,
            type=rel_type,
            status="OBSERVED"
        )
        db.add(rel)
    return rel

def seed_postgres(db: Session):
    print("Seeding PostgreSQL (Idempotent)...")
    system_user = get_or_create_user(db, "System_Agent3")
    
    # Cases
    case_a = get_or_create_case(db, "CASE-A", "Synthetic Network Demo", system_user.user_id)
    case_b = get_or_create_case(db, "CASE-B", "Isolated Background Noise", system_user.user_id)
    
    # === CASE A: Complex Analytical Topology ===
    # 1. High degree node (Central Figure)
    p_central = get_or_create_entity(db, case_a.case_id, "PERSON", "Synthetic Actor Alpha", "p_central")
    ph_central = get_or_create_entity(db, case_a.case_id, "PHONE", "9999900001", "ph_central")
    get_or_create_relationship(db, case_a.case_id, p_central.entity_id, ph_central.entity_id, "OWNS", "r_own_ph_c")
    
    # 2. Dense Community (Group 1)
    group1 = [get_or_create_entity(db, case_a.case_id, "PERSON", f"G1 Actor {i}", f"p_g1_{i}") for i in range(5)]
    for i in range(len(group1)):
        for j in range(i+1, len(group1)):
            get_or_create_relationship(db, case_a.case_id, group1[i].entity_id, group1[j].entity_id, "CONTACTED", f"r_contact_g1_{i}_{j}")
        # Connect some to central
        if i % 2 == 0:
            get_or_create_relationship(db, case_a.case_id, group1[i].entity_id, p_central.entity_id, "CONTACTED", f"r_contact_g1_central_{i}")

    # 3. High betweenness broker
    p_broker = get_or_create_entity(db, case_a.case_id, "PERSON", "Synthetic Broker Beta", "p_broker")
    get_or_create_relationship(db, case_a.case_id, p_broker.entity_id, group1[0].entity_id, "CONTACTED", "r_broker_g1")
    
    # 4. Dense Community (Group 2)
    group2 = [get_or_create_entity(db, case_a.case_id, "PERSON", f"G2 Actor {i}", f"p_g2_{i}") for i in range(4)]
    for i in range(len(group2)):
        for j in range(i+1, len(group2)):
            get_or_create_relationship(db, case_a.case_id, group2[i].entity_id, group2[j].entity_id, "CONTACTED", f"r_contact_g2_{i}_{j}")
    
    get_or_create_relationship(db, case_a.case_id, p_broker.entity_id, group2[0].entity_id, "CONTACTED", "r_broker_g2")
    
    # 5. Multi-hop paths & other modalities
    org = get_or_create_entity(db, case_a.case_id, "ORGANIZATION", "Synthetic Front Corp", "org_front")
    get_or_create_relationship(db, case_a.case_id, p_central.entity_id, org.entity_id, "AFFILIATED_WITH", "r_central_org")
    
    bank1 = get_or_create_entity(db, case_a.case_id, "BANK_ACCOUNT", "ACC-1001", "ba_1")
    bank2 = get_or_create_entity(db, case_a.case_id, "BANK_ACCOUNT", "ACC-1002", "ba_2")
    get_or_create_relationship(db, case_a.case_id, group2[1].entity_id, bank1.entity_id, "OWNS", "r_g21_ba1")
    get_or_create_relationship(db, case_a.case_id, group1[1].entity_id, bank2.entity_id, "OWNS", "r_g11_ba2")
    get_or_create_relationship(db, case_a.case_id, bank1.entity_id, bank2.entity_id, "TRANSFERRED_TO", "r_ba1_ba2")
    
    loc = get_or_create_entity(db, case_a.case_id, "LOCATION", "Synthetic Hub", "loc_hub")
    get_or_create_relationship(db, case_a.case_id, p_central.entity_id, loc.entity_id, "LOCATED_AT", "r_central_loc")

    # 6. Sparse actors
    p_sparse = get_or_create_entity(db, case_a.case_id, "PERSON", "Peripheral Actor", "p_sparse")
    get_or_create_relationship(db, case_a.case_id, p_sparse.entity_id, group2[2].entity_id, "CONTACTED", "r_sparse_g22")

    # === CASE B: Isolated Noise ===
    p_b1 = get_or_create_entity(db, case_b.case_id, "PERSON", "Isolated B1", "p_b1")
    p_b2 = get_or_create_entity(db, case_b.case_id, "PERSON", "Isolated B2", "p_b2")
    get_or_create_relationship(db, case_b.case_id, p_b1.entity_id, p_b2.entity_id, "CONTACTED", "r_b1_b2")
    
    db.commit()

    # Agent 3 specific mock data (model_runs)
    run_uid = deterministic_uuid(f"{case_a.case_id}-run1")
    run = db.query(ModelRun).filter(ModelRun.run_id == run_uid).first()
    if not run:
        run = ModelRun(
            run_id=run_uid,
            model_name="synthetic-agent3-fixture",
            version="0.1.0",
            task_type="DEMO",
            input_snapshot_checksum="demo_checksum",
            status="COMPLETED"
        )
        db.add(run)
        db.commit()

    return case_a.case_id, case_b.case_id

# --- Neo4j Seeding ---
def seed_neo4j(db: Session, driver, case_id: uuid.UUID):
    print(f"Projecting PostgreSQL graph to Neo4j for Case {case_id}...")
    
    entities = db.query(Entity).filter(Entity.case_id == case_id).all()
    rels = db.query(Relationship).filter(Relationship.case_id == case_id).all()
    
    with driver.session(database=neo4j_settings.neo4j_database) as session:
        for ent in entities:
            # Map canonical type to graph label
            label = "Person"
            name_prop = "display_name"
            val = ent.canonical_name
            if ent.entity_type == "PHONE":
                label = "Phone"
                name_prop = "masked_identifier"
            elif ent.entity_type == "BANK_ACCOUNT":
                label = "BankAccount"
                name_prop = "masked_identifier"
            elif ent.entity_type == "LOCATION":
                label = "Location"
                name_prop = "normalized_name"
            elif ent.entity_type == "ORGANIZATION":
                label = "Organization"
                name_prop = "name"
            elif ent.entity_type == "VEHICLE":
                label = "Vehicle"
                name_prop = "masked_plate"
                
            query = f"""
            MERGE (n:{label} {{entity_id: $eid}})
            SET n.{name_prop} = $name, n.case_id = $cid
            """
            session.run(query, eid=str(ent.entity_id), name=val, cid=str(case_id))
            
        for rel in rels:
            # Use dynamic type securely mapped from DB (ensure it's clean alphanumeric)
            rtype = rel.type.upper() if rel.type.isalnum() or '_' in rel.type else "OBSERVED_LINK"
            query = f"""
            MATCH (s {{entity_id: $sid}}), (t {{entity_id: $tid}})
            MERGE (s)-[r:{rtype} {{relationship_id: $rid}}]->(t)
            SET r.case_id = $cid, r.status = $status
            """
            session.run(query, sid=str(rel.source_entity_uuid), tid=str(rel.target_entity_uuid),
                        rid=str(rel.relationship_id), cid=str(case_id), status=rel.status)

# --- Verification ---
def verify_counts(db: Session, driver, case_a_id: uuid.UUID, case_b_id: uuid.UUID):
    # PostgreSQL counts
    pg_ent_a = db.query(Entity).filter(Entity.case_id == case_a_id).count()
    pg_rel_a = db.query(Relationship).filter(Relationship.case_id == case_a_id).count()
    
    pg_ent_b = db.query(Entity).filter(Entity.case_id == case_b_id).count()
    pg_rel_b = db.query(Relationship).filter(Relationship.case_id == case_b_id).count()
    
    pg_runs = db.query(ModelRun).count()
    
    # Neo4j counts
    with driver.session(database=neo4j_settings.neo4j_database) as session:
        n4j_ent_a = session.run("MATCH (n) WHERE n.case_id = $cid RETURN count(n) AS c", cid=str(case_a_id)).single()["c"]
        n4j_rel_a = session.run("MATCH ()-[r]->() WHERE r.case_id = $cid RETURN count(r) AS c", cid=str(case_a_id)).single()["c"]
        n4j_ent_b = session.run("MATCH (n) WHERE n.case_id = $cid RETURN count(n) AS c", cid=str(case_b_id)).single()["c"]
        n4j_rel_b = session.run("MATCH ()-[r]->() WHERE r.case_id = $cid RETURN count(r) AS c", cid=str(case_b_id)).single()["c"]

    # Cross case queries to ensure isolation
    with driver.session(database=neo4j_settings.neo4j_database) as session:
        # Are there any edges connecting case A and case B?
        cross_edges = session.run("""
        MATCH (a)-[r]-(b) 
        WHERE a.case_id = $ca AND b.case_id = $cb
        RETURN count(r) AS c
        """, ca=str(case_a_id), cb=str(case_b_id)).single()["c"]
    
    iso_pass = cross_edges == 0
    consistency_pass = (pg_ent_a == n4j_ent_a) and (pg_rel_a == n4j_rel_a)

    print("\n=========================================")
    print("SIH26189 Agent 3 Demo Seed")
    print("=========================================")
    print(f"\nCases:\n  CASE-A: {case_a_id}\n  CASE-B: {case_b_id}")
    
    print("\nPostgreSQL:")
    print(f"  entities: {pg_ent_a + pg_ent_b}")
    print(f"  relationships: {pg_rel_a + pg_rel_b}")
    print(f"  model_runs: {pg_runs}")
    print(f"  predictions: 0")
    print(f"  risk_scores: 0")
    print(f"  alerts: 0")
    print(f"  graph_snapshots: 0")
    
    print("\nNeo4j:")
    print(f"  nodes: {n4j_ent_a + n4j_ent_b}")
    print(f"  relationships: {n4j_rel_a + n4j_rel_b}")
    
    print(f"\nIsolation:\n  CASE-A -> {'PASS' if iso_pass else 'FAIL'}\n  CASE-B -> {'PASS' if iso_pass else 'FAIL'}")
    print(f"\nDeterministic IDs:\n  {'PASS' if consistency_pass else 'FAIL'}")
    print("\nSeed completed successfully.")

def main():
    db, driver = verify_services()
    try:
        ensure_constraints(driver)
        case_a_id, case_b_id = seed_postgres(db)
        seed_neo4j(db, driver, case_a_id)
        seed_neo4j(db, driver, case_b_id)
        verify_counts(db, driver, case_a_id, case_b_id)
    finally:
        db.close()
        driver.close()

if __name__ == "__main__":
    main()
