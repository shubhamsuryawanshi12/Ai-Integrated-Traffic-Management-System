"""
Actor-Critic Networks for PCU-MARL++.

Implements:
- Actor Network: Decentralized policy for each junction
- Centralized Critic Network: Global value function using all observations
"""

from typing import Optional, Tuple
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch import Tensor
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not available. Actor-Critic networks will be in dummy mode.")


# Observation dimension (after all features are concatenated)
# pcu_queue: 4, phase: 1, elapsed: 1, rain: 1, intent: 64, event: 12 = 83
OBS_DIM = 83
ACTION_DIM = 4

# Global observation dimension (N * obs_dim)
N_JUNCTIONS = 12
GLOBAL_OBS_DIM = N_JUNCTIONS * OBS_DIM  # 12 * 83 = 996


class ActorNetwork:
    """
    Actor network for decentralized control.
    
    Architecture:
    - Input: obs_dim (83)
    - Linear(83, 256) → LayerNorm → ReLU
    - Linear(256, 128) → LayerNorm → ReLU
    - Linear(128, 4) → logits
    """
    
    def __init__(
        self,
        obs_dim: int = OBS_DIM,
        action_dim: int = ACTION_DIM,
        hidden_dim: int = 256,
    ):
        """
        Initialize actor network.
        
        Args:
            obs_dim: Observation dimension
            action_dim: Number of actions
            hidden_dim: Hidden layer dimension
        """
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        
        if TORCH_AVAILABLE:
            self._init_torch_network(hidden_dim)
        else:
            self._init_dummy_network()
    
    def _init_torch_network(self, hidden_dim: int):
        """Initialize PyTorch network."""
        self.actor = nn.Sequential(
            nn.Linear(self.obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, self.action_dim),
        )
    
    def _init_dummy_network(self):
        """Initialize dummy network for when PyTorch is not available."""
        self.actor = None
    
    def forward(self, obs) -> "Tensor":
        """
        Get action logits.
        
        Args:
            obs: Observation tensor (batch, obs_dim)
            
        Returns:
            Action logits (batch, action_dim)
        """
        if TORCH_AVAILABLE and self.actor is not None:
            return self.actor(obs)
        else:
            # Return dummy logits
            if isinstance(obs, np.ndarray):
                batch_size = obs.shape[0] if len(obs.shape) > 1 else 1
            else:
                batch_size = 1
            return np.zeros((batch_size, self.action_dim))
    
    def get_action(
        self, 
        obs,
        deterministic: bool = False,
    ) -> Tuple:
        """
        Sample action from policy.
        
        Args:
            obs: Observation tensor
            deterministic: If True, take argmax
            
        Returns:
            Tuple of (action, log_prob, entropy)
        """
        if TORCH_AVAILABLE and self.actor is not None:
            logits = self.forward(obs)
            dist = Categorical(logits=logits)
            
            if deterministic:
                action = dist.probs.argmax(dim=-1)
            else:
                action = dist.sample()
            
            log_prob = dist.log_prob(action)
            entropy = dist.entropy()
            
            return action, log_prob, entropy
        else:
            # Dummy action
            import random
            action = random.randint(0, self.action_dim - 1)
            return action, 0.0, 0.0
    
    def evaluate_actions(
        self,
        obs,
        actions,
    ) -> Tuple:
        """
        Evaluate actions for a batch.
        
        Args:
            obs: Observation tensor
            actions: Actions tensor
            
        Returns:
            Tuple of (log_probs, entropies)
        """
        if TORCH_AVAILABLE and self.actor is not None:
            logits = self.forward(obs)
            dist = Categorical(logits=logits)
            
            log_probs = dist.log_prob(actions)
            entropies = dist.entropy()
            
            return log_probs, entropies
        else:
            return np.zeros(len(actions)), np.zeros(len(actions))


class CriticNetwork:
    """
    Centralized critic network for value estimation.
    
    Uses global observation (all junctions) to estimate value.
    
    Architecture:
    - Input: global_obs_dim (996)
    - Linear(996, 512) → LayerNorm → ReLU
    - Linear(512, 256) → LayerNorm → ReLU
    - Linear(256, 1) → value
    """
    
    def __init__(
        self,
        global_obs_dim: int = GLOBAL_OBS_DIM,
        hidden_dim: int = 512,
    ):
        """
        Initialize critic network.
        
        Args:
            global_obs_dim: Global observation dimension
            hidden_dim: Hidden layer dimension
        """
        self.global_obs_dim = global_obs_dim
        self.hidden_dim = hidden_dim
        
        if TORCH_AVAILABLE:
            self.critic = nn.Sequential(
                nn.Linear(global_obs_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.LayerNorm(hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1),
            )
        else:
            self.critic = None
    
    def forward(self, global_obs) -> "Tensor":
        """
        Estimate value.
        
        Args:
            global_obs: Global observation tensor (batch, global_obs_dim)
            
        Returns:
            Value estimate (batch, 1)
        """
        if TORCH_AVAILABLE and self.critic is not None:
            return self.critic(global_obs)
        else:
            return np.zeros((1, 1))


class LocalCriticNetwork:
    """
    Local critic for individual value estimation.
    
    Used for bootstrapping during rollouts.
    """
    
    def __init__(
        self,
        obs_dim: int = OBS_DIM,
        hidden_dim: int = 128,
    ):
        """
        Initialize local critic.
        
        Args:
            obs_dim: Observation dimension
            hidden_dim: Hidden dimension
        """
        self.obs_dim = obs_dim
        self.hidden_dim = hidden_dim
        
        if TORCH_AVAILABLE:
            self.critic = nn.Sequential(
                nn.Linear(obs_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1),
            )
        else:
            self.critic = None
    
    def forward(self, obs) -> "Tensor":
        """Get value estimate."""
        if TORCH_AVAILABLE and self.critic is not None:
            return self.critic(obs)
        else:
            return np.zeros((1, 1))


class ActorCritic:
    """
    Combined Actor-Critic for a single agent.
    """
    
    def __init__(
        self,
        obs_dim: int = OBS_DIM,
        action_dim: int = ACTION_DIM,
        actor_hidden: int = 256,
        critic_hidden: int = 128,
    ):
        """
        Initialize actor-critic.
        
        Args:
            obs_dim: Observation dimension
            action_dim: Action dimension
            actor_hidden: Actor hidden dimension
            critic_hidden: Critic hidden dimension
        """
        self.actor = ActorNetwork(obs_dim, action_dim, actor_hidden)
        self.local_critic = LocalCriticNetwork(obs_dim, critic_hidden)
    
    def forward(self, obs) -> "Tensor":
        """Forward pass through actor."""
        return self.actor(obs)
    
    def get_action(
        self,
        obs,
        deterministic: bool = False,
    ) -> Tuple:
        """Get action from actor."""
        return self.actor.get_action(obs, deterministic)
    
    def evaluate_actions(
        self,
        obs,
        actions,
    ) -> Tuple:
        """Evaluate actions."""
        return self.actor.evaluate_actions(obs, actions)
    
    def get_value(self, obs) -> "Tensor":
        """Get local value estimate."""
        return self.local_critic.forward(obs)


class CentralizedActorCritic:
    """
    Centralized Actor-Critic system with shared global critic.
    """
    
    def __init__(
        self,
        obs_dim: int = OBS_DIM,
        action_dim: int = ACTION_DIM,
        n_agents: int = N_JUNCTIONS,
        actor_hidden: int = 256,
        critic_hidden: int = 512,
    ):
        """
        Initialize centralized actor-critic.
        
        Args:
            obs_dim: Per-agent observation dimension
            action_dim: Action dimension
            n_agents: Number of agents
            actor_hidden: Actor hidden dimension
            critic_hidden: Critic hidden dimension
        """
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        
        if TORCH_AVAILABLE:
            # Create actor for each agent
            self.actors = nn.ModuleList([
                ActorNetwork(obs_dim, action_dim, actor_hidden)
                for _ in range(n_agents)
            ])
            
            # Centralized critic
            global_obs_dim = n_agents * obs_dim
            self.critic = CriticNetwork(global_obs_dim, critic_hidden)
            
            # Local critics for each agent
            self.local_critics = nn.ModuleList([
                LocalCriticNetwork(obs_dim, actor_hidden // 2)
                for _ in range(n_agents)
            ])
        else:
            self.actors = [ActorNetwork(obs_dim, action_dim, actor_hidden) for _ in range(n_agents)]
            self.critic = None
            self.local_critics = [LocalCriticNetwork(obs_dim, actor_hidden // 2) for _ in range(n_agents)]
    
    def get_actor_params(self, agent_id: int) -> dict:
        """Get parameters for a specific agent's actor."""
        if TORCH_AVAILABLE:
            return self.actors[agent_id].state_dict()
        return {}
    
    def load_actor_params(self, agent_id: int, state_dict: dict):
        """Load parameters for a specific agent's actor."""
        if TORCH_AVAILABLE:
            self.actors[agent_id].load_state_dict(state_dict)
    
    def get_all_actor_params(self) -> list:
        """Get parameters for all actors."""
        if TORCH_AVAILABLE:
            return [actor.state_dict() for actor in self.actors]
        return [{} for _ in range(self.n_agents)]
    
    def load_all_actor_params(self, params_list: list):
        """Load parameters for all actors."""
        if TORCH_AVAILABLE:
            for i, params in enumerate(params_list):
                if i < len(self.actors):
                    self.actors[i].load_state_dict(params)
    
    def forward_actor(self, agent_id: int, obs) -> "Tensor":
        """Forward through specific agent's actor."""
        return self.actors[agent_id].forward(obs)
    
    def get_global_value(self, global_obs) -> "Tensor":
        """Get global value estimate."""
        if TORCH_AVAILABLE and self.critic is not None:
            return self.critic.forward(global_obs)
        return np.zeros((1, 1))
    
    def get_local_value(self, agent_id: int, obs) -> "Tensor":
        """Get local value estimate for agent."""
        return self.local_critics[agent_id].forward(obs)
    
    def get_action(
        self,
        agent_id: int,
        obs,
        deterministic: bool = False,
    ) -> Tuple:
        """Get action for a specific agent."""
        return self.actors[agent_id].get_action(obs, deterministic)
    
    def evaluate_actions(
        self,
        agent_id: int,
        obs,
        actions,
    ) -> Tuple:
        """Evaluate actions for a specific agent."""
        return self.actors[agent_id].evaluate_actions(obs, actions)


def create_actor_critic(
    obs_dim: int = OBS_DIM,
    action_dim: int = ACTION_DIM,
    n_agents: int = N_JUNCTIONS,
) -> CentralizedActorCritic:
    """
    Factory function to create actor-critic.
    
    Args:
        obs_dim: Observation dimension
        action_dim: Action dimension
        n_agents: Number of agents
        
    Returns:
        CentralizedActorCritic instance
    """
    return CentralizedActorCritic(
        obs_dim=obs_dim,
        action_dim=action_dim,
        n_agents=n_agents,
    )
