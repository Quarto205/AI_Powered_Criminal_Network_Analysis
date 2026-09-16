"""
Case-scoped graph extraction from Neo4j into NetworkX.
Provides deterministic extraction of the observed Neo4j graph for a specific case.
"""

import logging
from typing import Dict, Any, Tuple
import networkx as nx

from backend.graph.connection import Neo4jConnectionManager, get_graph_manager

logger = logging.getLogger("backend.graph.graph_extractor")

class GraphExtractorError(Exception):
    pass


class GraphExtractor:
    """
    Extracts case-scoped observed graphs from Neo4j into NetworkX representations.
    Ensures no arbitrary Cypher execution and enforces case bounds.
    """
    def __init__(self, graph_manager: Neo4jConnectionManager = None):
        self.graph_manager = graph_manager or get_graph_manager()

    def extract_case_graph(self, case_id: str, as_directed: bool = True) -> nx.Graph:
        """
        Extracts all nodes and relationships belonging to a specific case_id.
        Returns a NetworkX graph (DiGraph if as_directed=True, else Graph).
        
        Args:
            case_id: The UUID string of the case to extract.
            as_directed: Whether to return a directed graph.
            
        Returns:
            A networkx Graph or DiGraph containing the case's subgraph.
        """
        if not self.graph_manager.is_healthy():
            raise GraphExtractorError("Neo4j is currently unavailable.")

        # Cypher query is strictly parameterized to case_id
        # We order by elementId to ensure deterministic graph construction
        # Return source entity_id and target entity_id to build the graph edges correctly.
        query = """
        MATCH (n)
        WHERE n.case_id = $case_id
        OPTIONAL MATCH (n)-[r]->(m)
        WHERE m.case_id = $case_id
        RETURN 
            n.entity_id AS source_id, labels(n) AS source_labels, properties(n) AS source_props,
            type(r) AS rel_type, properties(r) AS rel_props,
            m.entity_id AS target_id
        ORDER BY source_id, type(r), target_id
        """

        G = nx.DiGraph() if as_directed else nx.Graph()

        try:
            with self.graph_manager.get_session(access_mode="READ") as session:
                result = session.run(query, case_id=str(case_id))
                
                for record in result:
                    source_id = record["source_id"]
                    if not source_id:
                        continue
                        
                    # Add node if not exists (properties might overwrite if already added, which is fine since they are the same node)
                    if source_id not in G:
                        labels = list(record["source_labels"]) if record["source_labels"] else []
                        props = record["source_props"] or {}
                        G.add_node(source_id, labels=labels, **props)
                    
                    target_id = record["target_id"]
                    if target_id is not None:
                        # Edge properties
                        rel_type = record["rel_type"]
                        rel_props = record["rel_props"] or {}
                        # Make sure target node is also added (will be populated with its own properties when its own row is processed)
                        if target_id not in G:
                            G.add_node(target_id)
                        G.add_edge(source_id, target_id, type=rel_type, **rel_props)
                        
        except Exception as e:
            logger.error(f"Failed to extract graph for case {case_id}: {e}", exc_info=True)
            raise GraphExtractorError(f"Extraction failed: {e}")
            
        return G
