from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger("ml.preprocessing.temporal_split")

class TemporalSplitter:
    """
    Implements Chronological Edge-Masking Evaluation.
    Sorts observed edges by actual event time, defines a cutoff,
    and isolates test edges to strictly prevent temporal leakage.
    """
    def __init__(self, test_fraction: float = 0.2):
        self.test_fraction = test_fraction

    def _parse_time(self, edge: Dict[str, Any]) -> datetime:
        """Extracts and standardizes the created_at/event_time of an edge."""
        created_at = edge.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.min.replace(tzinfo=timezone.utc)
        elif not created_at:
            created_at = datetime.min.replace(tzinfo=timezone.utc)
            
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
            
        return created_at

    def split_edges(self, edges: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], datetime]:
        """
        Sorts edges chronologically.
        Splits into:
        1. Training edges (older)
        2. Testing edges (more recent)
        Returns (train_edges, test_edges, cutoff_datetime)
        """
        if not edges:
            return [], [], datetime.now(timezone.utc)
            
        # Ensure all edges have a parsed time
        sorted_edges = sorted(edges, key=self._parse_time)
        
        test_size = int(len(sorted_edges) * self.test_fraction)
        if test_size == 0 and len(sorted_edges) > 1:
            test_size = 1 # At least one test edge if possible
            
        train_size = len(sorted_edges) - test_size
        
        train_edges = sorted_edges[:train_size]
        test_edges = sorted_edges[train_size:]
        
        cutoff_time = self._parse_time(train_edges[-1]) if train_edges else datetime.min.replace(tzinfo=timezone.utc)
        
        logger.info(f"Chronological split applied. Train edges: {len(train_edges)}, Test edges: {len(test_edges)}. Cutoff: {cutoff_time.isoformat()}")
        
        return train_edges, test_edges, cutoff_time
