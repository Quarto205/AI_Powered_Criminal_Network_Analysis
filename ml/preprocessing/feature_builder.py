from typing import Dict, List, Any, Tuple
import torch
import numpy as np
from datetime import datetime, timezone
import logging

logger = logging.getLogger("ml.preprocessing.feature_builder")

# Global schema configuration mapping (must remain deterministic)
ENTITY_TYPES = ["PERSON", "PHONE", "ACCOUNT", "VEHICLE", "LOCATION", "ORGANIZATION", "UNKNOWN"]
RELATIONSHIP_TYPES = [
    "HAS_PHONE", "HAS_ACCOUNT", "OWNS_VEHICLE", "LOCATED_AT", 
    "AFFILIATED_WITH", "CONTACTED", "TRANSACTED_WITH", 
    "ASSOCIATED_WITH", "UNKNOWN"
]

def safe_one_hot(value: str, categories: List[str]) -> List[float]:
    """Generates a one-hot vector based on a predefined categorical schema."""
    one_hot = [0.0] * len(categories)
    upper_val = str(value).upper()
    if upper_val in categories:
        one_hot[categories.index(upper_val)] = 1.0
    else:
        one_hot[categories.index("UNKNOWN")] = 1.0
    return one_hot

class FeatureBuilder:
    """
    Constructs deterministic Node Matrix X and Edge Matrix E for PyTorch Geometric.
    Strictly forbids raw identifiers (IMSI, phone numbers, account numbers).
    """
    def __init__(self, sna_metrics: Dict[str, Any], embeddings: Dict[str, List[float]]):
        self.sna_metrics = sna_metrics
        self.embeddings = embeddings

        self.degree = sna_metrics.get("degree_centrality", {})
        self.betweenness = sna_metrics.get("betweenness_centrality", {})
        self.pagerank = sna_metrics.get("pagerank", {})
        self.k_core = sna_metrics.get("k_core", {})

        # Define indices to detect leakage dynamically
        self.forbidden_keys = {"phone", "imsi", "account_number", "ssn", "identifier"}

    def _prevent_leakage(self, attributes: Dict[str, Any]):
        """Raises ValueError if any sensitive identifier is passed into features."""
        for key in attributes.keys():
            lower_key = str(key).lower()
            if any(forbidden in lower_key for forbidden in self.forbidden_keys):
                raise ValueError(f"CRITICAL LEAKAGE DETECTED: Sensitive identifier '{key}' passed to FeatureBuilder.")

    def build_node_features(self, nodes: List[Dict[str, Any]]) -> torch.Tensor:
        """
        Constructs Node Feature Matrix X.
        Features:
        - Entity Type One-Hot
        - SNA Metrics (Degree, Betweenness, PageRank, K-Core)
        - Temporal Activity (Time since last activity in days)
        - Structural Embeddings (Node2Vec/DeepWalk)
        """
        x_features = []
        now = datetime.now(timezone.utc)
        
        for node in nodes:
            self._prevent_leakage(node)
            node_id = str(node.get("id"))
            
            # 1. Type One-Hot
            type_vec = safe_one_hot(node.get("entity_type", "UNKNOWN"), ENTITY_TYPES)
            
            # 2. SNA metrics
            sna_vec = [
                self.degree.get(node_id, 0.0),
                self.betweenness.get(node_id, 0.0),
                self.pagerank.get(node_id, 0.0),
                float(self.k_core.get(node_id, 0.0))
            ]
            
            # 3. Temporal (e.g. days since creation/last_event)
            created_at = node.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    created_at = None
                    
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
                
            time_since_days = 0.0
            if created_at:
                time_since_days = (now - created_at).total_seconds() / (3600 * 24)
            temporal_vec = [float(time_since_days)]
            
            # 4. Embeddings
            emb_vec = self.embeddings.get(node_id, [0.0] * 64) # Assuming dim=64 if missing
            
            feature_row = type_vec + sna_vec + temporal_vec + emb_vec
            x_features.append(feature_row)
            
        return torch.tensor(x_features, dtype=torch.float32)

    def build_edge_features(self, edges: List[Dict[str, Any]]) -> torch.Tensor:
        """
        Constructs Edge Feature Matrix E.
        Features:
        - Relationship Type One-Hot
        - Provenance Count (Observation frequency)
        - Temporal Decay based on created_at
        """
        e_features = []
        now = datetime.now(timezone.utc)
        decay_lambda = 0.005 # Configurable decay parameter
        
        for edge in edges:
            self._prevent_leakage(edge)
            
            # 1. Type One-Hot
            type_vec = safe_one_hot(edge.get("type", "UNKNOWN"), RELATIONSHIP_TYPES)
            
            # 2. Provenance Frequency
            prov_count = float(edge.get("provenance_count", 1.0))
            
            # 3. Time Decay (exp(-lambda * age_days))
            created_at = edge.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    created_at = None
                    
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
                
            decay = 1.0
            if created_at:
                age_days = (now - created_at).total_seconds() / (3600 * 24)
                if age_days > 0:
                    decay = np.exp(-decay_lambda * age_days)
                    
            e_features.append(type_vec + [prov_count, decay])
            
        if not e_features:
            # Return empty tensor with correct shape if no edges
            return torch.zeros((0, len(RELATIONSHIP_TYPES) + 2), dtype=torch.float32)
            
        return torch.tensor(e_features, dtype=torch.float32)
