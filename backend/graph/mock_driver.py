"""
Lightweight In-Memory Mock Neo4j Driver and Session for SIH26189.
Supports offline testing, outage simulation, parameterized MERGE query semantics,
and Cytoscape graph queries.
"""

from typing import Any, Callable, Dict, List, Optional
from uuid import UUID


class MockRecord:
    """Mock single record returned from Neo4j query result."""
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class MockResult:
    """Mock query result generator."""
    def __init__(self, records: List[Dict[str, Any]]):
        self._records = [MockRecord(r) for r in records]

    def single(self) -> Optional[MockRecord]:
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


class MockSession:
    """
    Mock Neo4j session maintaining an in-memory graph state of nodes and edges.
    Supports MERGE semantics, case-scoped deletion, and graph inspection.
    """
    def __init__(self, store: Dict[str, Any], is_outage: bool = False):
        self._store = store  # {"nodes": {(id, case_id): dict}, "edges": {(id, case_id): dict}}
        self._is_outage = is_outage

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, query: str, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> MockResult:
        if self._is_outage:
            from neo4j.exceptions import ServiceUnavailable
            raise ServiceUnavailable("Simulated Neo4j database outage.")

        params = dict(parameters or {})
        params.update(kwargs)

        # 1. Health check ping
        if "RETURN 1 AS ping" in query:
            return MockResult([{"ping": 1}])

        # 2. Schema DDL (Constraints / Indexes)
        if query.startswith("CREATE CONSTRAINT") or query.startswith("CREATE INDEX"):
            return MockResult([])

        # 3. Case Purge
        if "DETACH DELETE" in query and "$case_id" in query:
            case_id = str(params["case_id"])
            to_delete_nodes = [k for k in self._store["nodes"] if k[1] == case_id]
            for k in to_delete_nodes:
                del self._store["nodes"][k]
            to_delete_edges = [k for k in self._store["edges"] if k[1] == case_id]
            for k in to_delete_edges:
                del self._store["edges"][k]
            return MockResult([])

        # 4. Batch UNWIND Entity Node MERGE
        if "UNWIND $batch AS row" in query and "MERGE (n:Entity:" in query:
            batch = params.get("batch", [])
            for row in batch:
                key = (str(row["entity_id"]), str(row["case_id"]))
                self._store["nodes"][key] = {
                    "id": str(row["entity_id"]),
                    "case_id": str(row["case_id"]),
                    "canonical_name": str(row["canonical_name"]),
                    "entity_type": str(row["entity_type"]),
                    "status": str(row["status"]),
                    "created_at": str(row["created_at"]),
                }
            return MockResult([])

        # 5. Batch UNWIND Relationship MERGE
        if "UNWIND $batch AS row" in query and "MERGE (src)-[r:" in query:
            batch = params.get("batch", [])
            for row in batch:
                key = (str(row["relationship_id"]), str(row["case_id"]))
                self._store["edges"][key] = {
                    "id": str(row["relationship_id"]),
                    "case_id": str(row["case_id"]),
                    "source_id": str(row["source_id"]),
                    "target_id": str(row["target_id"]),
                    "type": str(row["rel_type"]),
                    "status": str(row["status"]),
                    "confidence_score": float(row["confidence_score"]),
                    "is_predicted": bool(row["is_predicted"]),
                    "provenance_count": int(row["provenance_count"]),
                    "created_at": str(row["created_at"]),
                }
            return MockResult([])

        # 6. Single Entity Node MERGE
        if query.startswith("MERGE (n:Entity:"):
            key = (str(params["entity_id"]), str(params["case_id"]))
            self._store["nodes"][key] = {
                "id": str(params["entity_id"]),
                "case_id": str(params["case_id"]),
                "canonical_name": str(params["canonical_name"]),
                "entity_type": str(params["entity_type"]),
                "status": str(params["status"]),
                "created_at": str(params["created_at"]),
            }
            return MockResult([])

        # 7. Single Relationship Edge MERGE
        if "MERGE (src)-[r:" in query:
            key = (str(params["relationship_id"]), str(params["case_id"]))
            self._store["edges"][key] = {
                "id": str(params["relationship_id"]),
                "case_id": str(params["case_id"]),
                "source_id": str(params["source_id"]),
                "target_id": str(params["target_id"]),
                "type": str(params["rel_type"]),
                "status": str(params["status"]),
                "confidence_score": float(params["confidence_score"]),
                "is_predicted": bool(params["is_predicted"]),
                "provenance_count": int(params["provenance_count"]),
                "created_at": str(params["created_at"]),
            }
            return MockResult([])

        # 8. Graph Query (Whole Case or Focus Entity)
        if "RETURN all_nodes AS nodes" in query or "RETURN collect(DISTINCT n) AS nodes" in query:
            case_id = str(params["case_id"])
            min_conf = float(params.get("min_confidence", 0.0))
            is_pred_excluded = "AND r.is_predicted = false" in query
            allowed_types = params.get("allowed_types", None)
            focus_id = params.get("focus_id", None)

            # Filter nodes by case_id (and focus_id / entity_types if applicable)
            matched_nodes = []
            for (nid, cid), node_data in self._store["nodes"].items():
                if cid != case_id:
                    continue
                if allowed_types and node_data["entity_type"] not in allowed_types:
                    continue
                matched_nodes.append(node_data)

            # Filter edges by case_id, min_confidence, is_predicted
            matched_edges = []
            for (eid, cid), edge_data in self._store["edges"].items():
                if cid != case_id:
                    continue
                if edge_data["confidence_score"] < min_conf:
                    continue
                if is_pred_excluded and edge_data["is_predicted"]:
                    continue
                matched_edges.append(edge_data)

            if focus_id:
                # If focus_id specified, only return connected nodes
                focus_str = str(focus_id)
                connected_node_ids = {focus_str}
                final_edges = []
                for e in matched_edges:
                    if e["source_id"] in connected_node_ids or e["target_id"] in connected_node_ids:
                        connected_node_ids.add(e["source_id"])
                        connected_node_ids.add(e["target_id"])
                        final_edges.append(e)
                matched_nodes = [n for n in matched_nodes if n["id"] in connected_node_ids]
                matched_edges = final_edges

            return MockResult([{"nodes": matched_nodes, "edges": matched_edges}])

        return MockResult([])


class MockDriver:
    """Mock Neo4j Driver."""
    def __init__(self, store: Optional[Dict[str, Any]] = None):
        self._store = store if store is not None else {"nodes": {}, "edges": {}}
        self._is_outage = False

    def session(self, database: Optional[str] = None, **kwargs) -> MockSession:
        return MockSession(self._store, is_outage=self._is_outage)

    def simulate_outage(self, is_outage: bool = True) -> None:
        self._is_outage = is_outage

    def close(self) -> None:
        pass


class MockNeo4jConnectionManager:
    """Mock Connection Manager conforming to Neo4jConnectionManager interface."""
    def __init__(self):
        self.mock_driver = MockDriver()

    def get_driver(self) -> MockDriver:
        return self.mock_driver

    def check_health(self) -> Dict[str, Any]:
        if self.mock_driver._is_outage:
            return {"status": "unavailable"}
        return {"status": "healthy", "database": "neo4j"}

    def is_healthy(self) -> bool:
        return not self.mock_driver._is_outage

    def get_session(self, access_mode: Optional[str] = None) -> MockSession:
        return self.mock_driver.session()

    def close(self) -> None:
        self.mock_driver.close()
