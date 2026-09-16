#!/usr/bin/env python3
"""
SIH26189 — Agent 3 Validation Script
Verifies that the standalone environment can perform basic analytical operations.
Proves NetworkX integration and Neo4j GDS availability using the mock dataset.
"""

import os
import sys
import uuid
import networkx as nx

# Add the project root to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable

# --- Deterministic ID Generation ---
NAMESPACE_AGENT3_SEED = uuid.UUID("12345678-1234-5678-1234-567812345678")

def deterministic_uuid(name: str) -> uuid.UUID:
    """Returns a deterministic UUID based on a string name."""
    return uuid.uuid5(NAMESPACE_AGENT3_SEED, name)

from dotenv import load_dotenv
load_dotenv()
from backend.config.neo4j import Neo4jSettings
neo4j_settings = Neo4jSettings.from_env()

NEO4J_URI = neo4j_settings.neo4j_uri
NEO4J_USER = neo4j_settings.neo4j_user
NEO4J_PASSWORD = neo4j_settings.neo4j_password

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))

def validate_networkx(driver, case_a_id: str):
    print("\n--- Running NetworkX Sanity Analysis ---")
    G = nx.Graph()
    
    with driver.session(database=neo4j_settings.neo4j_database) as session:
        # Load nodes
        nodes = session.run("MATCH (n) WHERE n.case_id = $cid RETURN n.entity_id AS id, labels(n)[0] AS type", cid=case_a_id)
        for record in nodes:
            G.add_node(record["id"], type=record["type"])
            
        # Load edges
        edges = session.run("MATCH (a)-[r]-(b) WHERE r.case_id = $cid RETURN a.entity_id AS src, b.entity_id AS dst, type(r) AS rel_type", cid=case_a_id)
        for record in edges:
            G.add_edge(record["src"], record["dst"], rel_type=record["rel_type"])
            
    print(f"Graph loaded into NetworkX: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    if G.number_of_nodes() == 0:
        print("[FAIL] Graph is empty. Did you run seed_demo.py?")
        return False
        
    components = list(nx.connected_components(G))
    print(f"Connected components: {len(components)}")
    
    deg_centrality = nx.degree_centrality(G)
    bet_centrality = nx.betweenness_centrality(G)
    
    max_deg_node = max(deg_centrality, key=deg_centrality.get)
    max_bet_node = max(bet_centrality, key=bet_centrality.get)
    
    print(f"Highest Degree Node: {max_deg_node} (Score: {deg_centrality[max_deg_node]:.4f})")
    print(f"Highest Betweenness Node: {max_bet_node} (Score: {bet_centrality[max_bet_node]:.4f})")
    print("[OK] NetworkX analysis completed successfully.")
    return True

def validate_gds(driver, case_a_id: str):
    print("\n--- Running Neo4j GDS Sanity Analysis ---")
    try:
        with driver.session(database=neo4j_settings.neo4j_database) as session:
            # Check GDS version
            result = session.run("CALL gds.version() YIELD gdsVersion")
            print(f"GDS Version: {result.single()['gdsVersion']}")
            
            # Project graph to GDS memory
            graph_name = "demo_graph_case_a"
            
            # Drop if exists
            session.run("CALL gds.graph.drop($name, false) YIELD graphName", name=graph_name)
            
            # Create projection using native projection with Cypher filter for case isolation
            session.run("""
            CALL gds.graph.project.cypher(
              $graph_name,
              'MATCH (n) WHERE n.case_id = "' + $cid + '" RETURN id(n) AS id',
              'MATCH (s)-[r]->(t) WHERE r.case_id = "' + $cid + '" RETURN id(s) AS source, id(t) AS target'
            )
            YIELD graphName, nodeCount, relationshipCount
            """, graph_name=graph_name, cid=case_a_id)
            
            # Run PageRank
            pr_result = session.run("""
            CALL gds.pageRank.stream($graph_name)
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).entity_id AS entity_id, score
            ORDER BY score DESC LIMIT 3
            """, graph_name=graph_name)
            
            print("Top 3 PageRank scores from GDS:")
            for record in pr_result:
                print(f"  {record['entity_id']}: {record['score']:.4f}")
                
            # Cleanup
            session.run("CALL gds.graph.drop($name, false) YIELD graphName", name=graph_name)
            print("[OK] GDS analysis completed successfully.")
            return True
            
    except ServiceUnavailable as e:
        print(f"[FAIL] Neo4j GDS test failed (Service Unavailable): {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Neo4j GDS test failed: {e}")
        return False

def main():
    case_a_id = str(deterministic_uuid("CASE-A"))
    
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        sys.exit(1)
        
    nx_ok = validate_networkx(driver, case_a_id)
    gds_ok = validate_gds(driver, case_a_id)
    
    driver.close()
    
    if nx_ok and gds_ok:
        print("\n[SUCCESS] Agent 3 Analytical Environment is fully functional.")
    else:
        print("\n[ERROR] Some validation checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
