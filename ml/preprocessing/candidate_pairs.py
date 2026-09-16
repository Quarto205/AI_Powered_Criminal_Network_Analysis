import logging
from typing import Any, Dict, List, Set, Tuple
from uuid import UUID

from backend.graph.connection import Neo4jConnectionManager, get_graph_manager

logger = logging.getLogger("ml.preprocessing.candidate_pairs")


class SemanticRule:
    """
    Defines a structural semantic rule for candidate generation.
    e.g., PERSON -> [ANY] -> PERSON predicting ASSOCIATED_WITH.
    """
    def __init__(self, source_type: str, intermediary_type: str, target_type: str, predicted_relationship: str):
        self.source_type = source_type
        self.intermediary_type = intermediary_type
        self.target_type = target_type
        self.predicted_relationship = predicted_relationship


class CandidateGenerator:
    """
    Generates candidate node pairs for link prediction from Neo4j.
    Uses bounded 2-hop traversal to prevent O(N^2) pairwise explosion.
    Strictly isolated by case_id.
    """
    def __init__(self, graph_manager: Neo4jConnectionManager = None):
        self.graph_manager = graph_manager or get_graph_manager()

    def generate_candidates(self, case_id: UUID, rules: List[SemanticRule]) -> List[Dict[str, Any]]:
        """
        Executes candidate generation based on provided semantic rules.
        Excludes existing target edges.
        Returns unique pairs with metadata.
        """
        if not self.graph_manager.is_healthy():
            logger.error("Neo4j is not available for candidate generation.")
            return []

        all_candidates = {}

        with self.graph_manager.get_session() as session:
            for rule in rules:
                # Build the Cypher query for 2-hop candidate generation matching the rule
                # A != C is enforced. We also ensure that no relationship already exists between A and C.
                # To prevent duplicating (A, C) and (C, A), we can enforce A.id < C.id if undirected, 
                # but GATv2 is usually directed. We'll generate both directions if applicable, or normalize.
                
                # Using a generic 2-hop match. 
                # (a:SourceType)-[]-(b:IntermediaryType)-[]-(c:TargetType)
                source_label = rule.source_type if rule.source_type != "ANY" else ""
                intermediary_label = rule.intermediary_type if rule.intermediary_type != "ANY" else ""
                target_label = rule.target_type if rule.target_type != "ANY" else ""

                source_match = f"(a{(':' + source_label.title()) if source_label else ''})"
                intermediary_match = f"(b{(':' + intermediary_label.title()) if intermediary_label else ''})"
                target_match = f"(c{(':' + target_label.title()) if target_label else ''})"

                query = f"""
                MATCH {source_match}-[]-{intermediary_match}-[]-{target_match}
                WHERE a.case_id = $case_id 
                  AND b.case_id = $case_id 
                  AND c.case_id = $case_id
                  AND a.entity_id <> c.entity_id
                  AND NOT (a)-[]-(c)
                RETURN DISTINCT a.entity_id AS source_id, c.entity_id AS target_id, labels(a)[0] AS source_type, labels(c)[0] AS target_type
                """
                
                result = session.run(query, case_id=str(case_id))
                for record in result:
                    source_id = record["source_id"]
                    target_id = record["target_id"]
                    
                    # Normalize orientation for undirected pairs to avoid duplicates
                    # We sort the pair to ensure (A, C) and (C, A) are treated as the same candidate
                    # if the predicted relationship is undirected.
                    pair = tuple(sorted([source_id, target_id]))
                    
                    if pair not in all_candidates:
                        all_candidates[pair] = {
                            "source_id": pair[0],
                            "target_id": pair[1],
                            "predicted_relationship": rule.predicted_relationship,
                            "source_type": record["source_type"] if pair[0] == source_id else record["target_type"],
                            "target_type": record["target_type"] if pair[1] == target_id else record["source_type"],
                        }

        return list(all_candidates.values())
