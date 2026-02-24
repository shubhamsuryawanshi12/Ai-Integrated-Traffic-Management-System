"""
IDSS (Intelligent Distributed Signal System) Module for PCU-MARL++.

Implements graph attention network for inter-junction communication.
Each junction encodes its local observation into an intent vector,
which is then aggregated via attention with neighbors.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


# Intent vector dimension
INTENT_DIM = 64

# Number of attention heads
GAT_HEADS = 4

# Communication radius in meters
COMM_RADIUS = 800


class IntentEncoder(nn.Module):
    """
    Encodes local observations into intent vectors.
    
    Architecture:
    - Input: observation (various dimensions)
    - Linear(obs_dim, 128) → ReLU
    - Linear(128, 64) → Tanh
    - Output: intent vector (64,)
    """
    
    def __init__(self, obs_dim: int = 83, hidden_dim: int = 128, intent_dim: int = INTENT_DIM):
        """
        Initialize intent encoder.
        
        Args:
            obs_dim: Input observation dimension
            hidden_dim: Hidden layer dimension
            intent_dim: Output intent dimension
        """
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, intent_dim),
            nn.Tanh(),
        )
    
    def forward(self, obs: Tensor) -> Tensor:
        """
        Encode observation to intent.
        
        Args:
            obs: Observation tensor
            
        Returns:
            Intent vector
        """
        return self.encoder(obs)


class GATLayer(nn.Module):
    """
    Graph Attention Layer for inter-junction communication.
    
    Implements multi-head attention with 4 heads.
    Edge weights initialized from physical travel times.
    """
    
    def __init__(
        self,
        in_dim: int = INTENT_DIM,
        out_dim: int = INTENT_DIM,
        n_heads: int = GAT_HEADS,
    ):
        """
        Initialize GAT layer.
        
        Args:
            in_dim: Input dimension
            out_dim: Output dimension (per head)
            n_heads: Number of attention heads
        """
        super().__init__()
        
        self.n_heads = n_heads
        self.out_dim = out_dim
        
        # Attention parameters
        self.W_att = nn.Linear(2 * in_dim, 1)
        self.W_val = nn.Linear(in_dim, out_dim * n_heads)
        
        # Output projection
        self.out_proj = nn.Linear(n_heads * out_dim, out_dim)
        
        # Leaky ReLU for attention
        self.leaky_relu = nn.LeakyReLU(0.2)
    
    def forward(
        self,
        self_intent: Tensor,
        neighbor_intents: Tensor,
        edge_weights: Optional[Tensor] = None,
    ) -> Tensor:
        """
        Compute aggregated message from neighbors.
        
        Args:
            self_intent: Self intent (batch, in_dim)
            neighbor_intents: Neighbor intents (batch, n_neighbors, in_dim)
            edge_weights: Optional edge weights
            
        Returns:
            Aggregated message (batch, out_dim)
        """
        batch_size = self_intent.size(0)
        n_neighbors = neighbor_intents.size(1) if neighbor_intents.dim() > 1 else 0
        
        if n_neighbors == 0:
            # No neighbors - return zero message
            return torch.zeros(batch_size, self.out_dim, device=self_intent.device)
        
        # Expand self intent for concatenation
        self_expanded = self_intent.unsqueeze(1).expand(-1, n_neighbors, -1)
        
        # Concatenate self and neighbor
        concat = torch.cat([self_expanded, neighbor_intents], dim=-1)
        
        # Compute attention scores
        e = self.leaky_relu(self.W_att(concat))  # (batch, n_neighbors, 1)
        
        # Apply edge weights if provided
        if edge_weights is not None:
            e = e * edge_weights.unsqueeze(-1)
        
        # Attention weights (softmax over neighbors)
        alpha = F.softmax(e, dim=1)  # (batch, n_neighbors, 1)
        
        # Compute values
        values = self.W_val(neighbor_intents)  # (batch, n_neighbors, n_heads * out_dim)
        
        # Reshape for multi-head attention
        values = values.view(batch_size, n_neighbors, self.n_heads, self.out_dim)
        alpha = alpha.unsqueeze(2)  # (batch, n_neighbors, 1, 1)
        
        # Weighted sum
        aggregated = (alpha * values).sum(dim=1)  # (batch, n_heads, out_dim)
        
        # Concatenate heads
        aggregated = aggregated.view(batch_size, self.n_heads * self.out_dim)
        
        # Output projection
        output = self.out_proj(aggregated)
        
        return output


class IDSSModule(nn.Module):
    """
    IDSS (Intelligent Distributed Signal System) module.
    
    Manages inter-junction communication via graph attention.
    """
    
    def __init__(
        self,
        n_junctions: int = 12,
        obs_dim: int = 83,
        intent_dim: int = INTENT_DIM,
        n_heads: int = GAT_HEADS,
        comm_radius: float = COMM_RADIUS,
        road_network=None,
    ):
        """
        Initialize IDSS module.
        
        Args:
            n_junctions: Number of junctions
            obs_dim: Observation dimension
            intent_dim: Intent vector dimension
            n_heads: GAT attention heads
            comm_radius: Communication radius in meters
            road_network: RoadNetwork instance
        """
        super().__init__()
        
        self.n_junctions = n_junctions
        self.intent_dim = intent_dim
        self.comm_radius = comm_radius
        
        # Encoder for local observations
        self.encoder = IntentEncoder(obs_dim, intent_dim=intent_dim)
        
        # GAT layers
        self.gat = GATLayer(
            in_dim=intent_dim,
            out_dim=intent_dim // n_heads,
            n_heads=n_heads,
        )
        
        # Store road network for neighbor lookup
        self.road_network = road_network
        
        # Initialize adjacency
        self.adjacency: Optional[Tensor] = None
        self.neighbors: Dict[int, List[int]] = {}
        
        if road_network is not None:
            self._build_communication_graph(road_network)
    
    def _build_communication_graph(self, road_network):
        """Build communication graph from road network."""
        # Build adjacency from road network
        adj_matrix = road_network.build_adjacency_matrix()
        
        # Convert to tensor
        self.adjacency = torch.from_numpy(adj_matrix).float()
        
        # Build neighbor lists
        for jid in range(self.n_junctions):
            self.neighbors[jid] = road_network.get_neighbors(
                jid, 
                radius=self.comm_radius
            )
    
    def update_intents(
        self,
        observations: Dict[int, np.ndarray],
    ) -> Dict[int, np.ndarray]:
        """
        Update intent messages for all junctions.
        
        Args:
            observations: Dict mapping junction_id to observation array
            
        Returns:
            Dict mapping junction_id to intent array
        """
        self.eval()
        
        with torch.no_grad():
            # Encode all observations
            intents = {}
            for jid, obs in observations.items():
                obs_tensor = torch.from_numpy(obs).float().unsqueeze(0)
                intents[jid] = self.encoder(obs_tensor).squeeze(0).numpy()
            
            # Aggregate messages
            messages = {}
            for jid in range(self.n_junctions):
                neighbors = self.neighbors.get(jid, [])
                
                if not neighbors:
                    messages[jid] = np.zeros(self.intent_dim, dtype=np.float32)
                    continue
                
                # Get neighbor intents
                neighbor_intents = []
                edge_weights = []
                
                for nid in neighbors:
                    if nid in intents:
                        neighbor_intents.append(intents[nid])
                        if self.adjacency is not None:
                            edge_weights.append(self.adjacency[jid, nid].item())
                
                if not neighbor_intents:
                    messages[jid] = np.zeros(self.intent_dim, dtype=np.float32)
                    continue
                
                # Stack tensors
                neighbor_tensor = torch.from_numpy(np.stack(neighbor_intents)).unsqueeze(0)
                
                self_intent = torch.from_numpy(intents[jid]).unsqueeze(0)
                
                if edge_weights:
                    edge_tensor = torch.tensor(edge_weights).unsqueeze(0)
                else:
                    edge_tensor = None
                
                # Compute aggregated message
                message = self.gat(self_intent, neighbor_tensor, edge_tensor)
                messages[jid] = message.squeeze(0).numpy()
        
        return messages
    
    def get_intent(self, obs: np.ndarray) -> np.ndarray:
        """
        Get intent for a single observation.
        
        Args:
            obs: Observation array
            
        Returns:
            Intent vector
        """
        self.eval()
        
        with torch.no_grad():
            obs_tensor = torch.from_numpy(obs).float().unsqueeze(0)
            intent = self.encoder(obs_tensor).squeeze(0).numpy()
        
        return intent
    
    def forward(
        self,
        self_obs: Tensor,
        neighbor_obs: Tensor,
        edge_weights: Optional[Tensor] = None,
    ) -> Tensor:
        """
        Forward pass for training.
        
        Args:
            self_obs: Self observations (batch, obs_dim)
            neighbor_obs: Neighbor observations (batch, n_neighbors, obs_dim)
            edge_weights: Edge weights (batch, n_neighbors)
            
        Returns:
            Aggregated messages (batch, intent_dim)
        """
        # Encode self observation
        self_intent = self.encoder(self_obs)
        
        # Encode neighbor observations
        neighbor_intents = self.encoder(neighbor_obs)  # (batch, n_neighbors, intent_dim)
        
        # GAT aggregation
        messages = self.gat(self_intent, neighbor_intents, edge_weights)
        
        return messages
    
    def get_communication_stats(self) -> Dict:
        """Get communication statistics."""
        total_edges = sum(len(n) for n in self.neighbors.values())
        
        return {
            "n_junctions": self.n_junctions,
            "n_edges": total_edges,
            "avg_degree": total_edges / max(1, self.n_junctions),
            "intent_dim": self.intent_dim,
            "n_heads": self.n_heads,
        }


class IDSSCoordinator:
    """
    Coordinator for IDSS module that manages communication schedule.
    """
    
    def __init__(
        self,
        n_junctions: int = 12,
        obs_dim: int = 83,
        intent_dim: int = INTENT_DIM,
        road_network=None,
    ):
        """
        Initialize IDSS coordinator.
        
        Args:
            n_junctions: Number of junctions
            obs_dim: Observation dimension
            intent_dim: Intent dimension
            road_network: RoadNetwork instance
        """
        self.idss = IDSSModule(
            n_junctions=n_junctions,
            obs_dim=obs_dim,
            intent_dim=intent_dim,
            road_network=road_network,
        )
        
        self.current_messages: Dict[int, np.ndarray] = {}
    
    def update(self, observations: Dict[int, np.ndarray]) -> Dict[int, np.ndarray]:
        """
        Update intent messages.
        
        Args:
            observations: Current observations
            
        Returns:
            Updated intent messages
        """
        self.current_messages = self.idss.update_intents(observations)
        return self.current_messages
    
    def get_messages(self) -> Dict[int, np.ndarray]:
        """Get current messages."""
        return self.current_messages
    
    def reset(self):
        """Reset messages."""
        self.current_messages = {
            i: np.zeros(INTENT_DIM, dtype=np.float32) 
            for i in range(self.idss.n_junctions)
        }
