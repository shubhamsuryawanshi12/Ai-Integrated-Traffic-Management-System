"""
Graph Neural Network (GNN) for Traffic Network Modeling

Implements Graph Attention Networks (GAT) and Graph Convolutional Networks (GCN)
to model spatio-temporal dependencies between intersections.

Features:
- Graph construction from road network
- Graph Attention Network (GAT) layers
- Temporal convolution (TGCN)
- Multi-intersection coordination
"""

from typing import Dict, List, Tuple, Optional, Any
import math

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not available. GNN will be in dummy mode.")


class GraphBuilder:
    """Builds graph representation from traffic network."""
    
    def __init__(self, num_intersections: int = 9):
        self.num_intersections = num_intersections
        self.adjacency_matrix = None
        self.edge_features = None
        self._build_default_graph()
    
    def _build_default_graph(self):
        """Build default grid graph for intersections."""
        # Create 3x3 grid adjacency
        # Intersection IDs:
        # 0 1 2
        # 3 4 5
        # 6 7 8
        
        adj = np.zeros((self.num_intersections, self.num_intersections))
        
        # Horizontal edges
        for row in range(3):
            for col in range(2):
                i = row * 3 + col
                j = row * 3 + col + 1
                adj[i, j] = 1
                adj[j, i] = 1
        
        # Vertical edges
        for col in range(3):
            for row in range(2):
                i = row * 3 + col
                j = (row + 1) * 3 + col
                adj[i, j] = 1
                adj[j, i] = 1
        
        self.adjacency_matrix = adj
        
        # Edge features (distance, road capacity)
        self.edge_features = self._compute_edge_features()
    
    def _compute_edge_features(self) -> np.ndarray:
        """Compute edge features."""
        num_edges = int(np.sum(self.adjacency_matrix) / 2)
        features = np.zeros((num_edges, 3))  # distance, capacity, speed_limit
        
        edge_idx = 0
        for i in range(self.num_intersections):
            for j in range(i + 1, self.num_intersections):
                if self.adjacency_matrix[i, j] > 0:
                    # Simulated distance (grid units)
                    features[edge_idx, 0] = 1.0
                    features[edge_idx, 1] = 2.0  # lanes
                    features[edge_idx, 2] = 50.0  # km/h
                    edge_idx += 1
        
        return features
    
    def build_from_config(self, config: Dict):
        """Build graph from configuration."""
        if 'adjacency' in config:
            self.adjacency_matrix = np.array(config['adjacency'])
            self.num_intersections = self.adjacency_matrix.shape[0]
    
    def get_adjacency(self, normalize: bool = True) -> np.ndarray:
        """Get adjacency matrix."""
        if normalize:
            # Normalize using degree matrix
            degree = np.sum(self.adjacency_matrix, axis=1)
            degree_inv_sqrt = np.power(degree, -0.5)
            degree_inv_sqrt[np.isinf(degree_inv_sqrt)] = 0
            d_mat_inv_sqrt = np.diag(degree_inv_sqrt)
            return d_mat_inv_sqrt @ self.adjacency_matrix @ d_mat_inv_sqrt
        
        return self.adjacency_matrix
    
    def get_edge_index(self) -> Tuple[List[int], List[int]]:
        """Get edge list as (source, target) tuples."""
        edges_u = []
        edges_v = []
        
        for i in range(self.num_intersections):
            for j in range(self.num_intersections):
                if self.adjacency_matrix[i, j] > 0:
                    edges_u.append(i)
                    edges_v.append(j)
        
        return edges_u, edges_v


class GraphAttentionLayer(nn.Module):
    """Graph Attention Layer (GAT)."""
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        alpha: float = 0.2
    ):
        super().__init__()
        
        self.num_heads = num_heads
        self.out_features = out_features
        self.head_dim = out_features // num_heads
        
        assert out_features % num_heads == 0, "out_features must be divisible by num_heads"
        
        # Linear projections
        self.W = nn.Linear(in_features, out_features)
        self.att = nn.Linear(2 * self.head_dim, 1)
        
        self.dropout = nn.Dropout(dropout)
        self.leakyrelu = nn.LeakyReLU(alpha)
        
        self._init_weights()
    
    def _init_weights(self):
        nn.init.xavier_uniform_(self.W.weight)
        nn.init.xavier_uniform_(self.att.weight)
    
    def forward(
        self,
        x: torch.Tensor,
        edge_index: Tuple[torch.Tensor, torch.Tensor]
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, in_features]
            edge_index: Edge indices [2, num_edges]
            
        Returns:
            Updated node features [num_nodes, out_features]
        """
        h = self.W(x).view(-1, self.num_heads, self.head_dim)
        
        edges_u, edges_v = edge_index
        
        # Compute attention coefficients
        h_u = h[edges_u]  # [num_edges, num_heads, head_dim]
        h_v = h[edges_v]
        
        # Concatenate and compute attention
        h_concat = torch.cat([h_u, h_v], dim=-1)  # [num_edges, num_heads, 2*head_dim]
        e = self.att(h_concat).squeeze(-1)  # [num_edges, num_heads]
        e = self.leakyrelu(e)
        
        # Sparse softmax
        attention = F.softmax(e, dim=0)
        attention = self.dropout(attention)
        
        # Aggregate neighbors
        out = torch.zeros_like(h)
        out.index_add_(0, edges_u.repeat(self.num_heads, 1).t(), 
                       attention.unsqueeze(-1) * h_v)
        
        out = out.view(-1, self.out_features)
        
        return out


class GraphConvLayer(nn.Module):
    """Graph Convolutional Layer (GCN)."""
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True
    ):
        super().__init__()
        
        self.in_features = in_features
        self.out_features = out_features
        
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter('bias', None)
        
        self.reset_parameters()
    
    def reset_parameters(self):
        nn.init.xavier_uniform_(self.weight)
        if self.bias is not None:
            nn.init.zeros_(self.bias)
    
    def forward(
        self,
        x: torch.Tensor,
        adj: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [batch, num_nodes, in_features]
            adj: Adjacency matrix [batch, num_nodes, num_nodes]
            
        Returns:
            Output features [batch, num_nodes, out_features]
        """
        support = torch.matmul(x, self.weight)
        output = torch.matmul(adj, support)
        
        if self.bias is not None:
            output = output + self.bias
        
        return output


class TemporalConvLayer(nn.Module):
    """Temporal Convolutional Layer."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.conv1 = nn.Conv1d(
            in_channels, out_channels, kernel_size,
            padding=kernel_size // 2
        )
        self.conv2 = nn.Conv1d(
            out_channels, out_channels, kernel_size,
            padding=kernel_size // 2
        )
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: [batch, channels, time_steps]
            
        Returns:
            [batch, channels, time_steps]
        """
        x = F.relu(self.conv1(x))
        x = self.dropout(x)
        x = F.relu(self.conv2(x))
        return x


class GraphAttentionNetwork(nn.Module):
    """Graph Attention Network for traffic prediction."""
    
    def __init__(
        self,
        num_nodes: int = 9,
        input_dim: int = 12,
        hidden_dim: int = 64,
        output_dim: int = 1,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.num_nodes = num_nodes
        self.num_layers = num_layers
        
        # Input embedding
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # GAT layers
        self.gat_layers = nn.ModuleList([
            GraphAttentionLayer(
                hidden_dim, hidden_dim,
                num_heads=num_heads,
                dropout=dropout
            )
            for _ in range(num_layers)
        ])
        
        # Output projection
        self.output_proj = nn.Linear(hidden_dim, output_dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        x: torch.Tensor,
        edge_index: Tuple[torch.Tensor, torch.Tensor]
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [batch, num_nodes, input_dim]
            edge_index: Edge indices
            
        Returns:
            Predictions [batch, num_nodes]
        """
        batch_size = x.size(0)
        
        # Project input
        h = self.input_proj(x)
        h = self.dropout(h)
        
        # Apply GAT layers
        for layer in self.gat_layers:
            h = layer(h, edge_index)
            h = F.elu(h)
        
        # Output projection
        out = self.output_proj(h)
        
        return out.squeeze(-1)


class TGCNModel(nn.Module):
    """
    Temporal Graph Convolutional Network.
    Combines GCN with temporal convolutions for spatio-temporal prediction.
    """
    
    def __init__(
        self,
        num_nodes: int = 9,
        input_dim: int = 12,
        hidden_dim: int = 64,
        output_dim: int = 1,
        num_timesteps: int = 12,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.num_timesteps = num_timesteps
        
        # Temporal convolution (input)
        self.temporal_in = TemporalConvLayer(input_dim, hidden_dim, dropout=dropout)
        
        # Graph convolution
        self.gcn = GraphConvLayer(hidden_dim, hidden_dim)
        
        # Temporal convolution (output)
        self.temporal_out = TemporalConvLayer(hidden_dim, hidden_dim, dropout=dropout)
        
        # Output
        self.fc = nn.Linear(hidden_dim, output_dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        x: torch.Tensor,
        adj: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input [batch, num_timesteps, num_nodes, input_dim]
            adj: Adjacency [batch, num_nodes, num_nodes]
            
        Returns:
            Predictions [batch, num_nodes]
        """
        batch_size = x.size(0)
        
        # Reshape for temporal conv: [B, T, N, C] -> [B, C, T]
        x = x.permute(0, 2, 3, 1)  # [B, N, C, T]
        x = x.reshape(batch_size * self.num_nodes, self.hidden_dim, self.num_timesteps)
        
        # Temporal convolution
        x = self.temporal_in(x)
        x = self.dropout(x)
        
        # Reshape back: [B*N, C, T] -> [B, N, C, T]
        x = x.view(batch_size, self.num_nodes, self.hidden_dim, self.num_timesteps)
        
        # Temporal last: [B, N, C, T] -> [B, N, C]
        x = x[:, :, :, -1]
        
        # Graph convolution
        x = self.gcn(x, adj)
        
        # Temporal convolution
        x = x.permute(0, 2, 1)  # [B, C, N]
        x = x.unsqueeze(-1)  # [B, C, N, 1]
        x = self.temporal_out(x.squeeze(-1).permute(0, 2, 1)).permute(0, 2, 1)
        
        # Output
        x = self.fc(x)
        
        return x.squeeze(-1)


class TrafficGNN:
    """
    High-level interface for GNN-based traffic prediction.
    """
    
    def __init__(
        self,
        num_intersections: int = 9,
        input_dim: int = 12,
        hidden_dim: int = 64,
        learning_rate: float = 1e-3,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.device = device
        self.num_intersections = num_intersections
        
        # Build graph
        self.graph_builder = GraphBuilder(num_intersections)
        
        # Initialize model
        if TORCH_AVAILABLE:
            self.model = GraphAttentionNetwork(
                num_nodes=num_intersections,
                input_dim=input_dim,
                hidden_dim=hidden_dim,
                output_dim=1,
                num_heads=4,
                num_layers=2
            ).to(device)
            
            self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
            self.criterion = nn.MSELoss()
        else:
            self.model = None
    
    def _prepare_data(
        self,
        states: List[Dict]
    ) -> torch.Tensor:
        """Prepare input data from states."""
        if not TORCH_AVAILABLE:
            return torch.zeros(1, self.num_intersections, 12)
        
        features = []
        
        for state in states:
            # Extract features for each intersection
            node_features = []
            for i in range(self.num_intersections):
                # Find intersection data
                int_data = {}
                for s in state.get('intersections', []):
                    if s.get('id') == i:
                        int_data = s
                        break
                
                # Feature vector
                feat = [
                    int_data.get('vehicles', 0) / 100.0,
                    int_data.get('throughput', 0) / 100.0,
                    int_data.get('queue', 0) / 50.0,
                    int_data.get('wait_time', 0) / 60.0,
                    int_data.get('pedestrians', 0) / 20.0,
                    0.0,  # emergency
                    math.sin(2 * math.pi * state.get('hour', 12) / 24),
                    math.cos(2 * math.pi * state.get('hour', 12) / 24),
                    0.0,  # day_sin
                    0.0,  # day_cos
                    0.0,  # is_peak
                    0.0,  # is_night
                ]
                node_features.append(feat)
            
            features.append(node_features)
        
        # Pad to num_timesteps
        while len(features) < self.num_intersections:
            features.append(features[-1])
        
        return torch.FloatTensor(features).unsqueeze(0).to(self.device)
    
    def predict(
        self,
        history: List[Dict]
    ) -> List[float]:
        """Predict traffic flow."""
        if self.model is None:
            # Return mock predictions
            return [10.0] * self.num_intersections
        
        self.model.eval()
        
        with torch.no_grad():
            x = self._prepare_data(history)
            
            # Get edge index
            edges_u, edges_v = self.graph_builder.get_edge_index()
            edge_index = (
                torch.LongTensor(edges_u).to(self.device),
                torch.LongTensor(edges_v).to(self.device)
            )
            
            # Predict
            output = self.model(x, edge_index)
            
            # Denormalize
            predictions = (output.squeeze() * 100).cpu().numpy().tolist()
            
            if isinstance(predictions, float):
                predictions = [predictions]
        
        return predictions
    
    def train_step(
        self,
        history: List[Dict],
        targets: List[float]
    ) -> float:
        """Training step."""
        if self.model is None:
            return 0.0
        
        self.model.train()
        
        x = self._prepare_data(history)
        y = torch.FloatTensor([targets]).to(self.device)
        
        edges_u, edges_v = self.graph_builder.get_edge_index()
        edge_index = (
            torch.LongTensor(edges_u).to(self.device),
            torch.LongTensor(edges_v).to(self.device)
        )
        
        self.optimizer.zero_grad()
        output = self.model(x, edge_index)
        loss = self.criterion(output, y)
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def save(self, path: str):
        """Save model."""
        if TORCH_AVAILABLE and self.model:
            torch.save(self.model.state_dict(), path)
    
    def load(self, path: str):
        """Load model."""
        if TORCH_AVAILABLE and self.model:
            self.model.load_state_dict(torch.load(path, map_location=self.device))


class MultiIntersectionCoordinator:
    """
    Coordinates signal timing across multiple intersections using GNN.
    """
    
    def __init__(self, num_intersections: int = 9):
        self.gnn = TrafficGNN(num_intersections)
        self.num_intersections = num_intersections
        
        # Coordination parameters
        self.coordination_weights = np.ones((num_intersections, num_intersections))
        self.phase_offsets = np.zeros(num_intersections)
    
    def optimize_signals(
        self,
        states: List[Dict]
    ) -> List[int]:
        """
        Optimize signals across all intersections.
        
        Args:
            states: Current states of all intersections
            
        Returns:
            List of recommended phases
        """
        # Get predictions
        predictions = self.gnn.predict(states)
        
        # Calculate optimal phases
        phases = []
        for i, pred in enumerate(predictions):
            if pred > 15:  # High congestion
                # Prefer giving green to this intersection's conflicting direction
                phase = 0 if i % 2 == 0 else 2
            elif pred < 5:  # Low congestion
                phase = 0  # Default
            else:
                phase = 1  # Transition
            
            phases.append(phase)
        
        return phases
    
    def calculate_green_wave(
        self,
        route: List[int],
        desired_speed: float = 50.0
    ) -> List[float]:
        """
        Calculate green wave timing for a route.
        
        Args:
            route: List of intersection IDs
            desired_speed: Desired speed in km/h
            
        Returns:
            Phase offsets for each intersection
        """
        offsets = []
        
        # Assuming 100m between intersections
        travel_time = (100 / 1000) / (desired_speed / 3600)  # seconds
        
        for i, intersection_id in enumerate(route):
            offsets.append(i * travel_time)
        
        return offsets
    
    def get_coordination_score(self) -> float:
        """Get network-wide coordination score."""
        # Simplified score based on phase differences
        score = 1.0 - np.std(self.phase_offsets) / 30.0
        return max(0.0, score)
