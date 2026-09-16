import torch
import torch.nn.functional as F
import torch.optim as optim
from typing import Dict, Any, List, Tuple
import logging

from ml.models.gatv2 import GATv2LinkPredictor

logger = logging.getLogger("ml.models.link_predictor")

class LinkPredictionPipeline:
    """
    Manages the GATv2 model lifecycle: training, evaluation, and inference.
    Deterministic behavior controlled by seeds.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device(config.get("device", "cpu"))
        
        # Extract hyperparameters
        self.hidden_channels = config.get("hidden_channels", 64)
        self.out_channels = config.get("out_channels", 32)
        self.num_heads = config.get("num_heads", 4)
        self.dropout = config.get("dropout", 0.2)
        self.lr = config.get("lr", 0.005)
        self.epochs = config.get("epochs", 100)
        self.seed = config.get("seed", 42)
        
        self._set_seeds()
        self.model = None

    def _set_seeds(self):
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

    def build_model(self, in_channels: int, edge_dim: int):
        self.model = GATv2LinkPredictor(
            in_channels=in_channels,
            hidden_channels=self.hidden_channels,
            out_channels=self.out_channels,
            edge_dim=edge_dim,
            num_heads=self.num_heads,
            dropout=self.dropout
        ).to(self.device)

    def train(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor, 
              pos_edge_label_index: torch.Tensor, neg_edge_label_index: torch.Tensor):
        """
        Trains the GATv2 model using Binary Cross Entropy with Logits.
        """
        if self.model is None:
            raise RuntimeError("Model must be built before training.")
            
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
        
        x = x.to(self.device)
        edge_index = edge_index.to(self.device)
        edge_attr = edge_attr.to(self.device)
        
        # Combine positive and negative training edges
        edge_label_index = torch.cat([pos_edge_label_index, neg_edge_label_index], dim=-1).to(self.device)
        edge_label = torch.cat([
            torch.ones(pos_edge_label_index.size(1)),
            torch.zeros(neg_edge_label_index.size(1))
        ]).to(self.device)
        
        logger.info(f"Training GATv2 on {self.device} for {self.epochs} epochs...")
        self.model.train()
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            logits = self.model(x, edge_index, edge_attr, edge_label_index)
            loss = F.binary_cross_entropy_with_logits(logits, edge_label)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0 or epoch == 0:
                logger.debug(f"Epoch {epoch+1:03d}/{self.epochs:03d} - Loss: {loss.item():.4f}")

    def predict_probs(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor, 
                      candidate_edge_index: torch.Tensor) -> torch.Tensor:
        """
        Runs inference on candidate edges returning normalized probabilities (0-1).
        """
        if self.model is None:
            raise RuntimeError("Model must be built before prediction.")
            
        self.model.eval()
        x = x.to(self.device)
        edge_index = edge_index.to(self.device)
        edge_attr = edge_attr.to(self.device)
        candidate_edge_index = candidate_edge_index.to(self.device)
        
        with torch.no_grad():
            logits = self.model(x, edge_index, edge_attr, candidate_edge_index)
            probs = torch.sigmoid(logits)
            
        return probs.cpu()
