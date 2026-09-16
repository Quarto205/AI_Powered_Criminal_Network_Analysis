import networkx as nx
import torch
import torch.nn as nn
import torch.optim as optim
import random
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger("ml.preprocessing.structural_embeddings")

class SimpleDeepWalk:
    """
    Dependency-free implementation of DeepWalk using standard PyTorch.
    Generates random walks using NetworkX and trains embeddings via Skip-Gram.
    Provides deterministic behavior when seeds are controlled.
    """
    def __init__(self, 
                 graph: nx.Graph, 
                 embedding_dim: int = 64, 
                 walk_length: int = 10, 
                 num_walks: int = 10,
                 context_window: int = 3,
                 seed: int = 42):
        self.graph = graph
        self.embedding_dim = embedding_dim
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.context_window = context_window
        self.seed = seed
        
        # Ensure determinism
        random.seed(self.seed)
        torch.manual_seed(self.seed)
        
        self.nodes = list(self.graph.nodes())
        self.node2idx = {node: i for i, node in enumerate(self.nodes)}
        self.idx2node = {i: node for i, node in enumerate(self.nodes)}
        self.vocab_size = len(self.nodes)
        
    def _generate_random_walks(self) -> List[List[int]]:
        """Generates random walks for all nodes."""
        walks = []
        for _ in range(self.num_walks):
            nodes = list(self.graph.nodes())
            random.shuffle(nodes)
            for node in nodes:
                walk = [self.node2idx[node]]
                current_node = node
                for _ in range(self.walk_length - 1):
                    neighbors = list(self.graph.neighbors(current_node))
                    if not neighbors:
                        break
                    next_node = random.choice(neighbors)
                    walk.append(self.node2idx[next_node])
                    current_node = next_node
                walks.append(walk)
        return walks

    def _generate_training_data(self, walks: List[List[int]]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Generates positive context pairs from walks."""
        contexts = []
        targets = []
        for walk in walks:
            for i, target in enumerate(walk):
                # Get window boundaries
                start = max(0, i - self.context_window)
                end = min(len(walk), i + self.context_window + 1)
                for j in range(start, end):
                    if i != j:
                        contexts.append(walk[j])
                        targets.append(target)
                        
        return torch.tensor(contexts, dtype=torch.long), torch.tensor(targets, dtype=torch.long)

    def train_embeddings(self, epochs: int = 5, lr: float = 0.025, device: str = "cpu") -> Dict[str, List[float]]:
        """Trains the Skip-Gram embeddings."""
        if self.vocab_size == 0:
            return {}
            
        logger.info(f"Generating random walks for {self.vocab_size} nodes...")
        walks = self._generate_random_walks()
        
        logger.info("Building training pairs...")
        x_context, y_target = self._generate_training_data(walks)
        
        if len(x_context) == 0:
            # Handle empty/fully disconnected graphs gracefully
            return {node: [0.0] * self.embedding_dim for node in self.nodes}

        # Simple PyTorch Embedding layer
        embeddings = nn.Embedding(self.vocab_size, self.embedding_dim)
        output_weights = nn.Linear(self.embedding_dim, self.vocab_size, bias=False)
        
        # Deterministic init
        nn.init.xavier_uniform_(embeddings.weight)
        nn.init.xavier_uniform_(output_weights.weight)
        
        model = nn.Sequential(embeddings, output_weights).to(device)
        x_context = x_context.to(device)
        y_target = y_target.to(device)
        
        optimizer = optim.Adam(model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()
        
        logger.info(f"Training DeepWalk model for {epochs} epochs...")
        model.train()
        
        # Batching to avoid memory explosion
        batch_size = 2048
        dataset_size = len(x_context)
        
        for epoch in range(epochs):
            total_loss = 0
            # Create deterministic permutation
            indices = torch.randperm(dataset_size, generator=torch.Generator().manual_seed(self.seed + epoch))
            
            for i in range(0, dataset_size, batch_size):
                batch_idx = indices[i:i + batch_size]
                batch_x = x_context[batch_idx]
                batch_y = y_target[batch_idx]
                
                optimizer.zero_grad()
                out = model(batch_x)
                loss = criterion(out, batch_y)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item() * len(batch_x)
                
            logger.debug(f"Epoch {epoch+1}/{epochs} - Loss: {total_loss / dataset_size:.4f}")
            
        # Extract the input embeddings
        model.eval()
        with torch.no_grad():
            emb_matrix = embeddings.weight.cpu().numpy()
            
        return {self.idx2node[i]: emb_matrix[i].tolist() for i in range(self.vocab_size)}
