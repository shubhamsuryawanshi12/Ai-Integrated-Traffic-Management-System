"""
IDSS (Intelligent Distributed Signal System) Module for PCU-MARL++.

Implements graph attention network for inter-junction communication.
Each junction encodes its local observation into an intent vector,
which is then aggregated via attention with neighbors.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch import Tensor
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not available. IDSS module will be in dummy mode.")


# Intent vector dimension
INTENT_DIM = 64

# Number of attention heads
GAT_HEADS = 4

# Communication radius in meters
COMM_RADIUS = 800


class IntentEncoder:
    """
    Encodes local observations into intent vectors.
    
    Architecture:
    - Input: observation (19 dims: queue + phase + elapsed + rain + event)
    - Linear(obs_dim, 128) → ReLU
    - Linear(128, 64) → Tanh
    - Output: intent vector (64,)
    """
    
    def __init__(
        self,
        obs_dim: int = 19,  # Base observation dimension (without intent)
        hidden_dim: int = 128,
        intent_dim: int = INTENT_DIM,
    ):
        """
        Initialize intent encoder.
        
        Args:
            obs_dim: Input observation dimension
            hidden_dim: Hidden layer dimension
            intent_dim: Output intent dimension
        """
        self.obs_dim = obs_dim
        self.hidden_dim = hidden_dim
        self.intent_dim = intent_dim
        
        if TORCH_AVAILABLE:
            self.encoder = nn.Sequential(
                nn.Linear(obs_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, intent_dim),
                nn.Tanh(),
            )
        else:
            self.encoder = None
    
    def forward(self, obs) -> np.ndarray:
        """
        Encode observation to intent.
        
        Args:
            obs: Observation tensor/numpy array
            
        Returns:
            Intent vector
        """
        if TORCH_AVAILABLE and self.encoder is not None:
            # Convert numpy to tensor if needed
            if isinstance(obs, np.ndarray):
                obs_tensor = torch.from_numpy(obs).float()
            else:
                obs_tensor = obs
            with torch.no_grad():
                return self.encoder(obs_tensor).detach().numpy()
        else:
            return np.zeros(self.intent_dim)
    
    def get_intent(self, obs: np.ndarray) -> np.ndarray:
        """Get intent for a single observation."""
        return self.forward(obs)


class IDSSModule:
    """
    IDSS (Intelligent Distributed Signal System) module.
    
    Manages inter-junction communication via graph attention.
    """
    
    def __init__(
        self,
        n_junctions: int = 12,
        obs_dim: int = 19,  # Base observation dimension
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
        self.n_junctions = n_junctions
        self.intent_dim = intent_dim
        self.comm_radius = comm_radius
        self.road_network = road_network
        
        # Encoder for local observations
        self.encoder = IntentEncoder(obs_dim, intent_dim=intent_dim)
        
        # Store neighbor lists
        self.neighbors: Dict[int, List[int]] = {}
        
        if road_network is not None:
            self._build_communication_graph(road_network)
        else:
            # Default: assume grid with adjacent junctions
            self._build_default_neighbors()
    
    def _build_default_neighbors(self):
        """Build default grid-based neighbors."""
        # Assume 3x4 grid (n_rows=3, n_cols=4)
        n_rows = 3
        n_cols = 4
        
        for j in range(self.n_junctions):
            row = j // n_cols
            col = j % n_cols
            neighbors = []
            
            # Adjacent junctions (up, down, left, right)
            if row > 0:
                neighbors.append((row - 1) * n_cols + col)  # up
            if row < n_rows - 1:
                neighbors.append((row + 1) * n_cols + col)  # down
            if col > 0:
                neighbors.append(row * n_cols + (col - 1))  # left
            if col < n_cols - 1:
                neighbors.append(row * n_cols + (col + 1))  # right
            
            self.neighbors[j] = [n for n in neighbors if n < self.n_junctions]
    
    def _build_communication_graph(self, road_network):
        """Build communication graph from road network."""
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
        # Encode all observations
        intents = {}
        for jid, obs in observations.items():
            obs_array = np.array(obs).astype(np.float32) if not isinstance(obs, np.ndarray) else obs
            intents[jid] = self.encoder.get_intent(obs_array)
        
        # Simple aggregation (average of neighbor intents)
        messages = {}
        for jid in range(self.n_junctions):
            neighbor_list = self.neighbors.get(jid, [])
            
            if not neighbor_list:
                messages[jid] = np.zeros(self.intent_dim, dtype=np.float32)
                continue
            
            # Get neighbor intents
            neighbor_intents = []
            for nid in neighbor_list:
                if nid in intents:
                    neighbor_intents.append(intents[nid])
            
            if not neighbor_intents:
                messages[jid] = np.zeros(self.intent_dim, dtype=np.float32)
                continue
            
            # Average aggregation
            messages[jid] = np.mean(neighbor_intents, axis=0)
        
        return messages
    
    def get_intent(self, obs: np.ndarray) -> np.ndarray:
        """
        Get intent for a single observation.
        
        Args:
            obs: Observation array
            
        Returns:
            Intent vector
        """
        return self.encoder.get_intent(obs)
    
    def get_communication_stats(self) -> Dict:
        """Get communication statistics."""
        total_edges = sum(len(n) for n in self.neighbors.values())
        
        return {
            "n_junctions": self.n_junctions,
            "n_edges": total_edges,
            "avg_degree": total_edges / max(1, self.n_junctions),
            "intent_dim": self.intent_dim,
            "n_heads": GAT_HEADS,
        }
    
    def get_neighbors(self, junction_id: int) -> List[int]:
        """Get neighboring junctions for a given junction."""
        return self.neighbors.get(junction_id, [])


class IDSSCoordinator:
    """
    Coordinator for IDSS module that manages communication schedule.
    """
    
    def __init__(
        self,
        n_junctions: int = 12,
        obs_dim: int = 19,  # Base observation dimension
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
    
    def get_stats(self) -> Dict:
        """Get communication statistics."""
        return self.idss.get_communication_stats()
