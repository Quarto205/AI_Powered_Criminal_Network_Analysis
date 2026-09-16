import os
import sys
import argparse
import logging
from uuid import UUID
import networkx as nx
import numpy as np
import torch
from sqlalchemy.orm import Session

# Ensure we can import from backend and ml
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.session import SessionLocal
from backend.db.models.analytics import Prediction
from backend.graph.connection import get_graph_manager
from agents.intelligence.sna_engine import SNAEngine
from ml.preprocessing.candidate_pairs import CandidateGenerator, SemanticRule
from ml.models.classical_baselines import ClassicalBaselines
from ml.preprocessing.structural_embeddings import SimpleDeepWalk
from ml.preprocessing.temporal_split import TemporalSplitter
from ml.preprocessing.feature_builder import FeatureBuilder
from ml.models.link_predictor import LinkPredictionPipeline
from ml.evaluation.metrics import LinkPredictionMetrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("evaluation_pipeline")

def load_graph_from_neo4j(case_id: UUID) -> nx.DiGraph:
    """Loads the case subgraph from Neo4j into NetworkX."""
    graph_manager = get_graph_manager()
    G = nx.DiGraph()
    if not graph_manager.is_healthy():
        logger.error("Neo4j is not available. Cannot load graph.")
        return G
        
    with graph_manager.get_session() as session:
        # Get nodes
        result = session.run("MATCH (n:Entity {case_id: $case_id}) RETURN n", case_id=str(case_id))
        for record in result:
            node = record["n"]
            G.add_node(node["id"], **dict(node))
            
        # Get edges
        result = session.run("MATCH (n:Entity {case_id: $case_id})-[r]->(m:Entity {case_id: $case_id}) RETURN n.id AS u, m.id AS v, r", case_id=str(case_id))
        for record in result:
            u, v, r = record["u"], record["v"], record["r"]
            edge_data = dict(r)
            edge_data["type"] = r.type
            G.add_edge(u, v, **edge_data)
            
    return G

def run_evaluation(case_id_str: str):
    logger.info(f"Starting Phase 3 Link Prediction Evaluation Pipeline for Case: {case_id_str}")
    case_id = UUID(case_id_str)
    
    # 1. Load Graph
    logger.info("Loading graph from Neo4j...")
    G = load_graph_from_neo4j(case_id)
    if len(G) == 0:
        logger.error("Graph is empty. Aborting.")
        return
        
    logger.info(f"Graph loaded: {len(G.nodes())} nodes, {len(G.edges())} edges.")
    
    # 2. Chronological Split (Temporal Masking)
    logger.info("Applying Temporal Split (80/20)...")
    edges_data = [d for u, v, d in G.edges(data=True)]
    splitter = TemporalSplitter(test_fraction=0.2)
    train_edges, test_edges, cutoff_time = splitter.split_edges(edges_data)
    
    # Mask graph: build a training graph that only contains train_edges
    G_train = nx.DiGraph()
    G_train.add_nodes_from(G.nodes(data=True))
    for u, v, d in G.edges(data=True):
        edge_time = splitter._parse_time(d)
        if edge_time <= cutoff_time:
            G_train.add_edge(u, v, **d)
            
    logger.info(f"Training Graph: {len(G_train.edges())} edges (Test edges masked).")
    
    # 3. Candidate Generation (Neo4j bounded)
    logger.info("Generating candidate pairs...")
    candidate_generator = CandidateGenerator()
    rules = [
        SemanticRule("PERSON", "ANY", "PERSON", "ASSOCIATED_WITH"),
        SemanticRule("PERSON", "PHONE", "PERSON", "CONTACTED")
    ]
    candidates = candidate_generator.generate_candidates(case_id, rules)
    logger.info(f"Generated {len(candidates)} candidate pairs.")
    
    if not candidates:
        logger.warning("No candidates generated. Aborting.")
        return

    # 4. Classical Baselines
    logger.info("Evaluating Classical Baselines...")
    baselines = ClassicalBaselines(G_train) # Evaluated only on train graph
    candidate_pairs = [(c["source_id"], c["target_id"]) for c in candidates]
    baseline_scores = baselines.compute_all(candidate_pairs)
    
    # 5. Features & Embeddings
    logger.info("Computing SNA Metrics...")
    sna = SNAEngine(G_train)
    sna_metrics = sna.run_all_metrics()
    
    logger.info("Training DeepWalk Embeddings...")
    deepwalk = SimpleDeepWalk(G_train.to_undirected(as_view=True), embedding_dim=32, walk_length=5, num_walks=5, epochs=3)
    embeddings = deepwalk.train_embeddings()
    
    logger.info("Building Node & Edge Features...")
    node_data_list = [{"id": n, **d} for n, d in G_train.nodes(data=True)]
    edge_data_list = [d for _, _, d in G_train.edges(data=True)]
    
    feature_builder = FeatureBuilder(sna_metrics, embeddings)
    x = feature_builder.build_node_features(node_data_list)
    edge_attr = feature_builder.build_edge_features(edge_data_list)
    
    # Create edge_index for PyG
    node_list = list(G_train.nodes())
    node2idx = {node: i for i, node in enumerate(node_list)}
    
    edge_index_list = []
    for u, v in G_train.edges():
        edge_index_list.append([node2idx[u], node2idx[v]])
    edge_index = torch.tensor(edge_index_list, dtype=torch.long).t().contiguous()
    
    if edge_index.numel() == 0:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, len(edge_attr[0]) if len(edge_attr) > 0 else 0), dtype=torch.float32)

    # 6. GATv2 Train & Inference
    # For training, we need positive and negative edges.
    # Positive: a subset of existing edges.
    pos_edge_index = edge_index
    # Negative: randomly sample some non-edges (simplified for this evaluation script)
    neg_edges = []
    import random
    while len(neg_edges) < pos_edge_index.size(1):
        u, v = random.randint(0, len(node_list)-1), random.randint(0, len(node_list)-1)
        if not G_train.has_edge(node_list[u], node_list[v]) and u != v:
            neg_edges.append([u, v])
            
    neg_edge_index = torch.tensor(neg_edges, dtype=torch.long).t().contiguous() if neg_edges else torch.empty((2,0), dtype=torch.long)
    
    pipeline = LinkPredictionPipeline(config={"epochs": 20, "hidden_channels": 32, "out_channels": 16})
    in_channels = x.size(1)
    edge_dim = edge_attr.size(1) if edge_attr.numel() > 0 else 1
    
    # Fix edge_attr if empty
    if edge_attr.numel() == 0:
        edge_attr = torch.zeros((0, edge_dim))
        
    pipeline.build_model(in_channels, edge_dim)
    
    if pos_edge_index.numel() > 0:
        pipeline.train(x, edge_index, edge_attr, pos_edge_index, neg_edge_index)
    
    # 7. Predict on Candidates
    logger.info("Running inference on candidates...")
    candidate_edge_indices = []
    valid_candidates = []
    
    for c in candidates:
        if c["source_id"] in node2idx and c["target_id"] in node2idx:
            candidate_edge_indices.append([node2idx[c["source_id"]], node2idx[c["target_id"]]])
            valid_candidates.append(c)
            
    if not candidate_edge_indices:
        logger.warning("No valid candidates found in training graph nodes.")
        return
        
    candidate_edge_tensor = torch.tensor(candidate_edge_indices, dtype=torch.long).t().contiguous()
    gat_probs = pipeline.predict_probs(x, edge_index, edge_attr, candidate_edge_tensor)
    
    # Evaluate (Self-Supervised if we pretend test edges are ground truth for hits/mrr)
    # Since candidates generated by Cypher explicitly exclude existing edges, 
    # to evaluate we'd usually mix test edges into the candidates.
    # For this script, we'll just demonstrate the scoring and persistence.
    
    # 8. Persistence (System of Record)
    logger.info("Persisting predictions to PostgreSQL...")
    db: Session = SessionLocal()
    
    # Arbitrary dummy model run id just for script completion if required. 
    # Usually you'd create a ModelRun first.
    from backend.db.models.analytics import ModelRun
    model_run = ModelRun(case_id=case_id, status="COMPLETED", model_type="LINK_PREDICTION", configuration={})
    db.add(model_run)
    db.commit()
    db.refresh(model_run)
    
    persisted_count = 0
    for i, candidate in enumerate(valid_candidates):
        score = gat_probs[i].item()
        if score > 0.6: # Threshold
            u_id = candidate["source_id"]
            v_id = candidate["target_id"]
            pred = Prediction(
                model_run_id=model_run.id,
                case_id=case_id,
                source_ref=u_id,
                target_ref=v_id,
                predicted_relationship_type=candidate["predicted_relationship"],
                score=score,
                calibration="UNVERIFIED",
                status="INFERRED",
                metadata_={
                    "model": "GATv2",
                    "baselines": baseline_scores.get((u_id, v_id), {})
                }
            )
            db.add(pred)
            persisted_count += 1
            
    db.commit()
    db.close()
    
    logger.info(f"Evaluation complete. Persisted {persisted_count} high-confidence inferred links.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 3 Link Prediction Evaluation")
    parser.add_argument("--case-id", type=str, required=True, help="UUID of the Case")
    args = parser.parse_args()
    
    run_evaluation(args.case_id)
