import pytest
from datetime import datetime, timezone, timedelta
from ml.preprocessing.feature_builder import FeatureBuilder
from ml.preprocessing.temporal_split import TemporalSplitter

def test_raw_id_leakage_blocked():
    # Create nodes with sensitive raw IDs
    nodes = [
        {"id": "1", "entity_type": "PHONE", "phone_number": "+1234567890"},
        {"id": "2", "entity_type": "PERSON", "imsi": "9999999999"}
    ]
    fb = FeatureBuilder(sna_metrics={}, embeddings={})
    
    with pytest.raises(ValueError, match="CRITICAL LEAKAGE DETECTED"):
        fb.build_node_features(nodes)

def test_temporal_split_no_leakage():
    now = datetime.now(timezone.utc)
    # 5 edges chronological
    edges = [
        {"id": "e1", "created_at": (now - timedelta(days=5)).isoformat()},
        {"id": "e2", "created_at": (now - timedelta(days=4)).isoformat()},
        {"id": "e3", "created_at": (now - timedelta(days=3)).isoformat()},
        {"id": "e4", "created_at": (now - timedelta(days=2)).isoformat()},
        {"id": "e5", "created_at": (now - timedelta(days=1)).isoformat()},
    ]
    
    splitter = TemporalSplitter(test_fraction=0.4) # 2 test edges, 3 train edges
    train_edges, test_edges, cutoff_time = splitter.split_edges(edges)
    
    assert len(train_edges) == 3
    assert len(test_edges) == 2
    
    # Ensure test edges are strictly strictly after cutoff
    for t_edge in test_edges:
        assert splitter._parse_time(t_edge) > cutoff_time
