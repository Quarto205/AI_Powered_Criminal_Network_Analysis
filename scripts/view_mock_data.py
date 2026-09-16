#!/usr/bin/env python3
"""
SIH26189 — Standalone Mock Data Viewer & Exporter
Constructs the exact deterministic Case A & Case B topologies from seed_demo.py
in-memory without requiring live PostgreSQL or Neo4j server connections.
Exports the graph to data/demo/mock_graph_demo.json and displays a visual summary.
"""

import os
import sys
import uuid
import json
from datetime import datetime, timezone

NAMESPACE_AGENT3_SEED = uuid.UUID("12345678-1234-5678-1234-567812345678")

def deterministic_uuid(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE_AGENT3_SEED, name))

def generate_mock_graph():
    case_a_id = deterministic_uuid("CASE-A")
    case_b_id = deterministic_uuid("CASE-B")

    entities = []
    relationships = []

    def add_entity(case_id, entity_type, canonical_name, e_id):
        uid = deterministic_uuid(f"{case_id}-{e_id}")
        ent = {
            "entity_id": uid,
            "case_id": case_id,
            "entity_type": entity_type,
            "canonical_name": canonical_name,
            "status": "ACTIVE"
        }
        entities.append(ent)
        return ent

    def add_rel(case_id, source_id, target_id, rel_type, r_id):
        uid = deterministic_uuid(f"{case_id}-{r_id}")
        rel = {
            "relationship_id": uid,
            "case_id": case_id,
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "type": rel_type,
            "status": "OBSERVED"
        }
        relationships.append(rel)
        return rel

    # === CASE A: Complex Analytical Topology ===
    p_central = add_entity(case_a_id, "PERSON", "Synthetic Actor Alpha (Kingpin / Hub)", "p_central")
    ph_central = add_entity(case_a_id, "PHONE", "+91-9999900001", "ph_central")
    add_rel(case_a_id, p_central["entity_id"], ph_central["entity_id"], "OWNS", "r_own_ph_c")

    # Group 1 (Clique of 5)
    g1 = [add_entity(case_a_id, "PERSON", f"G1 Actor {i} (Smuggling Cell)", f"p_g1_{i}") for i in range(5)]
    for i in range(len(g1)):
        for j in range(i + 1, len(g1)):
            add_rel(case_a_id, g1[i]["entity_id"], g1[j]["entity_id"], "CONTACTED", f"r_contact_g1_{i}_{j}")
        if i % 2 == 0:
            add_rel(case_a_id, g1[i]["entity_id"], p_central["entity_id"], "CONTACTED", f"r_contact_g1_central_{i}")

    # Broker connecting Group 1 and Group 2
    p_broker = add_entity(case_a_id, "PERSON", "Synthetic Broker Beta (Bridge / Conduit)", "p_broker")
    add_rel(case_a_id, p_broker["entity_id"], g1[0]["entity_id"], "CONTACTED", "r_broker_g1")

    # Group 2 (Clique of 4)
    g2 = [add_entity(case_a_id, "PERSON", f"G2 Actor {i} (Distribution Cell)", f"p_g2_{i}") for i in range(4)]
    for i in range(len(g2)):
        for j in range(i + 1, len(g2)):
            add_rel(case_a_id, g2[i]["entity_id"], g2[j]["entity_id"], "CONTACTED", f"r_contact_g2_{i}_{j}")
    add_rel(case_a_id, p_broker["entity_id"], g2[0]["entity_id"], "CONTACTED", "r_broker_g2")

    # Front Org & Financial Layer
    org = add_entity(case_a_id, "ORGANIZATION", "Synthetic Front Corp Ltd", "org_front")
    add_rel(case_a_id, p_central["entity_id"], org["entity_id"], "AFFILIATED_WITH", "r_central_org")

    bank1 = add_entity(case_a_id, "BANK_ACCOUNT", "HDFC-ACC-1001", "ba_1")
    bank2 = add_entity(case_a_id, "BANK_ACCOUNT", "SBI-ACC-1002", "ba_2")
    add_rel(case_a_id, g2[1]["entity_id"], bank1["entity_id"], "OWNS", "r_g21_ba1")
    add_rel(case_a_id, g1[1]["entity_id"], bank2["entity_id"], "OWNS", "r_g11_ba2")
    add_rel(case_a_id, bank1["entity_id"], bank2["entity_id"], "TRANSFERRED_TO", "r_ba1_ba2")

    loc = add_entity(case_a_id, "LOCATION", "Synthetic Hub (Safehouse / Port)", "loc_hub")
    add_rel(case_a_id, p_central["entity_id"], loc["entity_id"], "LOCATED_AT", "r_central_loc")

    # Peripheral
    p_sparse = add_entity(case_a_id, "PERSON", "Peripheral Informant", "p_sparse")
    add_rel(case_a_id, p_sparse["entity_id"], g2[2]["entity_id"], "CONTACTED", "r_sparse_g22")

    # === CASE B: Isolated Background Noise ===
    p_b1 = add_entity(case_b_id, "PERSON", "Isolated B1", "p_b1")
    p_b2 = add_entity(case_b_id, "PERSON", "Isolated B2", "p_b2")
    add_rel(case_b_id, p_b1["entity_id"], p_b2["entity_id"], "CONTACTED", "r_b1_b2")

    return {
        "cases": [
            {"case_id": case_a_id, "case_code": "CASE-A", "title": "Synthetic Network Demo"},
            {"case_id": case_b_id, "case_code": "CASE-B", "title": "Isolated Background Noise"},
        ],
        "entities": entities,
        "relationships": relationships,
        "summary": {
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "case_a_entities": len([e for e in entities if e["case_id"] == case_a_id]),
            "case_a_relationships": len([r for r in relationships if r["case_id"] == case_a_id]),
            "case_b_entities": len([e for e in entities if e["case_id"] == case_b_id]),
            "case_b_relationships": len([r for r in relationships if r["case_id"] == case_b_id]),
        }
    }

def main():
    data = generate_mock_graph()
    
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "mock_graph_demo.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("=================================================================")
    print("      SIH26189 — MOCK CRIMINAL NETWORK TOPOLOGY GENERATED        ")
    print("=================================================================")
    print(f"Exported clean JSON to: {os.path.abspath(out_path)}\n")
    print(f"Summary:")
    print(f"  • Total Entities     : {data['summary']['total_entities']}")
    print(f"  • Total Relationships: {data['summary']['total_relationships']}")
    print(f"  • Case A (Main Demo) : {data['summary']['case_a_entities']} nodes, {data['summary']['case_a_relationships']} edges")
    print(f"  • Case B (Isolation) : {data['summary']['case_b_entities']} nodes, {data['summary']['case_b_relationships']} edges\n")

    print("--- CASE A ENTITIES ---")
    case_a_id = data["cases"][0]["case_id"]
    for e in data["entities"]:
        if e["case_id"] == case_a_id:
            print(f"  [{e['entity_type']:<12}] {e['canonical_name']:<42} (UUID: {e['entity_id'][:8]}...)")

    print("\n--- SAMPLE RELATIONSHIPS (CASE A) ---")
    ent_map = {e["entity_id"]: e["canonical_name"].split(" (")[0] for e in data["entities"]}
    for r in data["relationships"][:12]:
        src = ent_map.get(r["source_entity_id"], r["source_entity_id"][:8])
        dst = ent_map.get(r["target_entity_id"], r["target_entity_id"][:8])
        print(f"  {src:<24} --[:{r['type']:<14}]--> {dst}")
    if len(data["relationships"]) > 12:
        print(f"  ... and {len(data['relationships']) - 12} more edges.")
    print("=================================================================")

if __name__ == "__main__":
    main()
