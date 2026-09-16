import logging
from uuid import UUID
import networkx as nx
import torch
from sqlalchemy.orm import Session

from backend.db.models.analytics import Prediction
from backend.graph.connection import get_graph_manager
from agents.intelligence.sna_engine import SNAEngine
from ml.preprocessing.candidate_pairs import CandidateGenerator, SemanticRule
from ml.models.classical_baselines import ClassicalBaselines
from ml.preprocessing.structural_embeddings import SimpleDeepWalk
from ml.preprocessing.feature_builder import FeatureBuilder
from ml.models.link_predictor import LinkPredictionPipeline

logger = logging.getLogger("agents.intelligence.link_prediction_engine")

class LinkPredictionEngine:
    """
    Deterministic Link Prediction (Phase 3) Engine for AI-Powered Criminal Network Analysis.
    Integrates with the async worker to provide GATv2-based inferred links.
    """
    def __init__(self, db: Session, run_id: UUID):
        self.db = db
        self.run_id = run_id

    def load_graph_from_neo4j(self, case_id: UUID) -> nx.DiGraph:
        """Loads the case subgraph from Neo4j into NetworkX."""
        graph_manager = get_graph_manager()
        G = nx.DiGraph()
        if not graph_manager.is_healthy():
            logger.error("Neo4j is not available. Cannot load graph for link prediction.")
            return G
            
        with graph_manager.get_session() as session:
            # Get nodes
            result = session.run("MATCH (n) WHERE n.case_id = $case_id RETURN n", case_id=str(case_id))
            for record in result:
                node = record["n"]
                G.add_node(node["entity_id"], **dict(node))
                
            # Get edges
            result = session.run("MATCH (n)-[r]->(m) WHERE n.case_id = $case_id AND m.case_id = $case_id RETURN n.entity_id AS u, m.entity_id AS v, r", case_id=str(case_id))
            for record in result:
                u, v, r = record["u"], record["v"], record["r"]
                edge_data = dict(r)
                edge_data["type"] = r.type
                G.add_edge(u, v, **edge_data)
                
        return G

    def run(self, case_id: UUID):
        """Runs the deterministic GATv2 pipeline for candidate pairs and persists predictions."""
        logger.info(f"Starting Link Prediction Engine (GATv2) for Case: {case_id}")
        
        # 1. Load Graph
        G = self.load_graph_from_neo4j(case_id)
        if len(G) == 0:
            logger.warning("Graph is empty. Aborting Link Prediction.")
            return
            
        # 2. Candidate Generation (Neo4j bounded)
        candidate_generator = CandidateGenerator()
        rules = [
            SemanticRule("PERSON", "ANY", "PERSON", "ASSOCIATED_WITH"),
            SemanticRule("PERSON", "PHONE", "PERSON", "CONTACTED")
        ]
        candidates = candidate_generator.generate_candidates(case_id, rules)
        
        if not candidates:
            logger.info("No candidate pairs generated. Aborting Link Prediction.")
            return

        # 3. Classical Baselines
        baselines = ClassicalBaselines(G)
        candidate_pairs = [(c["source_id"], c["target_id"]) for c in candidates]
        baseline_scores = baselines.compute_all(candidate_pairs)
        
        # 4. Features & Embeddings
        sna = SNAEngine(G)
        sna_metrics = sna.run_all_metrics()
        
        deepwalk = SimpleDeepWalk(G.to_undirected(as_view=True), embedding_dim=32, walk_length=5, num_walks=5, epochs=3)
        embeddings = deepwalk.train_embeddings()
        
        node_data_list = [{"id": n, **d} for n, d in G.nodes(data=True)]
        edge_data_list = [d for _, _, d in G.edges(data=True)]
        
        feature_builder = FeatureBuilder(sna_metrics, embeddings)
        x = feature_builder.build_node_features(node_data_list)
        edge_attr = feature_builder.build_edge_features(edge_data_list)
        
        # Create edge_index for PyG
        node_list = list(G.nodes())
        node2idx = {node: i for i, node in enumerate(node_list)}
        
        edge_index_list = []
        for u, v in G.edges():
            edge_index_list.append([node2idx[u], node2idx[v]])
        edge_index = torch.tensor(edge_index_list, dtype=torch.long).t().contiguous()
        
        if edge_index.numel() == 0:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, len(edge_attr[0]) if len(edge_attr) > 0 else 0), dtype=torch.float32)

        # 5. GATv2 Train & Inference
        pos_edge_index = edge_index
        neg_edges = []
        import random
        while len(neg_edges) < max(pos_edge_index.size(1), 10):
            u, v = random.randint(0, len(node_list)-1), random.randint(0, len(node_list)-1)
            if not G.has_edge(node_list[u], node_list[v]) and u != v:
                neg_edges.append([u, v])
                
        neg_edge_index = torch.tensor(neg_edges, dtype=torch.long).t().contiguous() if neg_edges else torch.empty((2,0), dtype=torch.long)
        
        pipeline = LinkPredictionPipeline(config={"epochs": 20, "hidden_channels": 32, "out_channels": 16})
        in_channels = x.size(1)
        edge_dim = edge_attr.size(1) if edge_attr.numel() > 0 else 1
        
        if edge_attr.numel() == 0:
            edge_attr = torch.zeros((0, edge_dim))
            
        pipeline.build_model(in_channels, edge_dim)
        
        if pos_edge_index.numel() > 0:
            pipeline.train(x, edge_index, edge_attr, pos_edge_index, neg_edge_index)
        
        # 6. Predict on Candidates
        candidate_edge_indices = []
        valid_candidates = []
        
        for c in candidates:
            if c["source_id"] in node2idx and c["target_id"] in node2idx:
                candidate_edge_indices.append([node2idx[c["source_id"]], node2idx[c["target_id"]]])
                valid_candidates.append(c)
                
        if not candidate_edge_indices:
            return
            
        candidate_edge_tensor = torch.tensor(candidate_edge_indices, dtype=torch.long).t().contiguous()
        gat_probs = pipeline.predict_probs(x, edge_index, edge_attr, candidate_edge_tensor)
        
        # 7. Persistence (System of Record)
        new_preds = []
        from uuid import uuid4
        for i, candidate in enumerate(valid_candidates):
            score = gat_probs[i].item()
            if score > 0.6: # Threshold for considering an inferred link
                u_id = candidate["source_id"]
                v_id = candidate["target_id"]
                pred = Prediction(
                    prediction_id=uuid4(),
                    run_id=self.run_id,
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
                new_preds.append(pred)
                
        if new_preds:
            self.db.bulk_save_objects(new_preds)
            self.db.commit()
            logger.info(f"Persisted {len(new_preds)} inferred links to PostgreSQL.")
