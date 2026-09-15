"""Optional Graph Neural Network (GNN) module for PROVISYN.
Ports GraphSAGE architecture from Snowflake GPU notebooks.
Gated behind PROVISYN_GRAPH_BACKEND=gnn and torch_geometric installation.
"""
from typing import Dict, List, Any, Optional
import numpy as np
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

def is_gnn_available() -> bool:
    """Check if PyTorch and PyTorch Geometric are available and GNN backend is active."""
    if settings.GRAPH_BACKEND.lower() != "gnn":
        return False
    try:
        import torch
        import torch_geometric
        return True
    except ImportError:
        return False

class GraphSAGEModelWrapper:
    """Wrapper for optional GraphSAGE GNN link prediction and node embedding model."""

    def __init__(self, in_channels: int = 16, hidden_channels: int = 32, out_channels: int = 16):
        self.is_available = is_gnn_available()
        self.model = None
        if self.is_available:
            self._init_torch_model(in_channels, hidden_channels, out_channels)
        else:
            logger.info("GraphSAGE GNN track is disabled or torch_geometric is not installed. Defaulting to NetworkX.")

    def _init_torch_model(self, in_channels: int, hidden_channels: int, out_channels: int):
        try:
            import torch
            import torch.nn as nn
            from torch_geometric.nn import SAGEConv

            class GraphSAGE(nn.Module):
                def __init__(self, in_ch, hid_ch, out_ch):
                    super().__init__()
                    self.conv1 = SAGEConv(in_ch, hid_ch)
                    self.conv2 = SAGEConv(hid_ch, out_ch)

                def forward(self, x, edge_index):
                    x = self.conv1(x, edge_index).relu()
                    x = self.conv2(x, edge_index)
                    return x

            self.model = GraphSAGE(in_channels, hidden_channels, out_channels)
            logger.info("GraphSAGE PyTorch Geometric model initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize GraphSAGE PyTorch model: {e}")
            self.model = None

    def compute_embeddings(self, node_features: np.ndarray, edge_index: np.ndarray) -> np.ndarray:
        """Compute node representations via 2-layer GraphSAGE message passing."""
        if not self.is_available or self.model is None:
            # Fallback to normalized feature matrix
            norm = np.linalg.norm(node_features, axis=1, keepdims=True)
            return node_features / np.maximum(norm, 1e-6)

        import torch
        with torch.no_grad():
            x = torch.tensor(node_features, dtype=torch.float)
            edges = torch.tensor(edge_index, dtype=torch.long)
            out = self.model(x, edges)
            return out.numpy()
