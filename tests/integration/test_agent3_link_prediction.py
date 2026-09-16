import pytest
import networkx as nx
import numpy as np
from datetime import datetime, timezone
import torch
from ml.models.classical_baselines import ClassicalBaselines
from ml.preprocessing.feature_builder import FeatureBuilder
from ml.models.gatv2 import GATv2LinkPredictor
from ml.evaluation.metrics import LinkPredictionMetrics

def test_classical_baselines():
    # Construct a simple known graph
    # 1 - 2 - 3 - 4
    #  \ /
    #   5
    G = nx.Graph()
    G.add_edges_from([(1, 2), (2, 3), (3, 4), (1, 5), (2, 5)])
    
    baselines = ClassicalBaselines(G)
    ebunch = [(1, 3), (5, 3), (1, 4)]
    scores = baselines.compute_all(ebunch)
    
    assert scores[(1, 3)]["common_neighbors"] == 1.0 # node 2
    assert scores[(5, 3)]["common_neighbors"] == 1.0 # node 2
    assert scores[(1, 4)]["common_neighbors"] == 0.0
    
    assert scores[(1, 3)]["jaccard"] == 1.0 / (2 + 2 - 1) # node 1 deg=2, node 3 deg=2, union=3 -> 1/3
    assert abs(scores[(1, 3)]["jaccard"] - 0.333) < 0.01

def test_feature_builder_safe():
    nodes = [{"id": "1", "entity_type": "PERSON", "created_at": "2023-01-01T00:00:00Z"}]
    sna = {"degree_centrality": {"1": 0.5}}
    emb = {"1": [0.1] * 64}
    
    fb = FeatureBuilder(sna, emb)
    x = fb.build_node_features(nodes)
    assert x.size(0) == 1
    assert x.size(1) == 7 + 4 + 1 + 64 # Entity types (7) + SNA (4) + Temporal (1) + Emb (64)

def test_gatv2_forward_pass():
    model = GATv2LinkPredictor(in_channels=76, hidden_channels=16, out_channels=8, edge_dim=11)
    
    x = torch.rand(4, 76)
    edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
    edge_attr = torch.rand(4, 11)
    edge_label_index = torch.tensor([[0, 2], [2, 3]], dtype=torch.long)
    
    logits = model(x, edge_index, edge_attr, edge_label_index)
    assert logits.shape == (2,)

def test_metrics():
    y_true = np.array([1, 0, 1, 0])
    y_score = np.array([0.9, 0.1, 0.4, 0.8])
    
    # Ranks of positive samples:
    # 0.9 -> rank 1 (true)
    # 0.8 -> rank 2 (false)
    # 0.4 -> rank 3 (true)
    # 0.1 -> rank 4 (false)
    
    metrics = LinkPredictionMetrics.compute_all_metrics(y_true, y_score)
    
    assert metrics["Hits@1"] == 0.5 # 1 out of 2 true positives in top 1
    assert metrics["Hits@3"] == 1.0 # 2 out of 2 true positives in top 3
    
    # MRR = (1/1 + 1/3) / 2 = (1 + 0.333) / 2 = 0.666
    assert abs(metrics["MRR"] - 0.666) < 0.01
