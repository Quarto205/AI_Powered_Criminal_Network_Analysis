import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv

class GATv2LinkPredictor(nn.Module):
    """
    Graph Attention Network v2 for Link Prediction.
    Encodes nodes using structural and edge features, then scores pairs.
    """
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, 
                 edge_dim: int, num_heads: int = 4, dropout: float = 0.2):
        super().__init__()
        self.dropout = dropout
        
        # Two GATv2 layers
        self.conv1 = GATv2Conv(
            in_channels, 
            hidden_channels, 
            heads=num_heads, 
            edge_dim=edge_dim, 
            concat=True, 
            dropout=dropout
        )
        self.conv2 = GATv2Conv(
            hidden_channels * num_heads, 
            out_channels, 
            heads=1, 
            edge_dim=edge_dim, 
            concat=False, 
            dropout=dropout
        )
        
        # Link scoring head. Uses element-wise product and absolute difference.
        self.scorer = nn.Sequential(
            nn.Linear(out_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, 1)
        )

    def encode(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        """
        Passes node features X through GATv2 to obtain hidden node representations.
        """
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv1(x, edge_index, edge_attr)
        x = F.elu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index, edge_attr)
        return x

    def decode(self, z: torch.Tensor, edge_label_index: torch.Tensor) -> torch.Tensor:
        """
        Given hidden node representations Z and candidate edge pairs,
        scores each pair using the link scoring head.
        """
        # Obtain source and target representations for the given candidate pairs
        z_u = z[edge_label_index[0]]
        z_v = z[edge_label_index[1]]
        
        # Combine representations: Hadamard product and absolute difference
        combined = torch.cat([z_u * z_v, torch.abs(z_u - z_v)], dim=-1)
        
        # Pass through scorer and return raw logits
        logits = self.scorer(combined).squeeze(-1)
        return logits

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor, 
                edge_label_index: torch.Tensor) -> torch.Tensor:
        """
        End-to-end forward pass returning prediction logits.
        """
        z = self.encode(x, edge_index, edge_attr)
        logits = self.decode(z, edge_label_index)
        return logits
