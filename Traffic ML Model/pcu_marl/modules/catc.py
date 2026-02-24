"""
CATC (Climate-Adaptive Traffic Control) Module for PCU-MARL++.

Implements three distinct policies trained under different weather regimes:
- Clear weather (R=0)
- Moderate rain (R≈0.45)
- Heavy rain (R>0.7)

With smooth sigmoid-based mixing at inference time.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch.distributions import Categorical


# Policy training regimes
CAPACITY_CLEAR = 1.0
CAPACITY_MODERATE = 0.8
CAPACITY_HEAVY = 0.6

# Rain intensity thresholds
RAIN_CLEAR = 0.0
RAIN_MODERATE = 0.45
RAIN_HEAVY = 0.7


def sigmoid(x: float) -> float:
    """Sigmoid function."""
    return 1.0 / (1.0 + np.exp(-x))


def mixing_weights(rain_intensity: float) -> Tuple[float, float, float]:
    """
    Calculate mixing weights for the three policies.
    
    Uses smooth sigmoid functions:
    - w1: peaks at R=0 (clear)
    - w2: peaks at R=0.45 (moderate)
    - w3: peaks at R>0.7 (heavy)
    
    Args:
        rain_intensity: Current rain intensity [0, 1]
        
    Returns:
        Tuple of (w_clear, w_moderate, w_heavy) that sum to 1
    """
    # Weight for clear weather policy
    w1 = sigmoid(-(rain_intensity - RAIN_CLEAR) * 10)
    
    # Weight for moderate weather policy
    w2 = (
        sigmoid((rain_intensity - RAIN_MODERATE) * 10) * 
        sigmoid(-(rain_intensity - (RAIN_MODERATE + RAIN_HEAVY) / 2) * 10)
    )
    
    # Weight for heavy weather policy
    w3 = sigmoid((rain_intensity - RAIN_HEAVY) * 10)
    
    # Normalize to sum to 1
    total = w1 + w2 + w3
    if total > 0:
        w1 /= total
        w2 /= total
        w3 /= total
    else:
        # Default to clear
        w1, w2, w3 = 1.0, 0.0, 0.0
    
    return w1, w2, w3


class ClimatePolicyNetwork(nn.Module):
    """
    Policy network for a specific weather regime.
    
    Architecture same as the actor network.
    """
    
    def __init__(
        self,
        obs_dim: int = 83,
        action_dim: int = 4,
        hidden_dim: int = 256,
    ):
        """
        Initialize policy network.
        
        Args:
            obs_dim: Observation dimension
            action_dim: Number of actions
            hidden_dim: Hidden layer dimension
        """
        super().__init__()
        
        self.policy = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
        )
    
    def forward(self, obs: Tensor) -> Tensor:
        """Get action logits."""
        return self.policy(obs)
    
    def get_action(self, obs: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        """
        Sample action from policy.
        
        Returns:
            Tuple of (action, log_prob, entropy)
        """
        logits = self.forward(obs)
        dist = Categorical(logits=logits)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, entropy
    
    def evaluate_actions(
        self, 
        obs: Tensor, 
        actions: Tensor
    ) -> Tuple[Tensor, Tensor, Tensor]:
        """
        Evaluate actions for a batch.
        
        Returns:
            Tuple of (log_probs, values, entropies)
        """
        logits = self.forward(obs)
        dist = Categorical(logits=logits)
        
        log_probs = dist.log_prob(actions)
        entropies = dist.entropy()
        
        return log_probs, entropies, logits


class CATCModule(nn.Module):
    """
    Climate-Adaptive Traffic Control module.
    
    Maintains three policy networks and mixes them based on rain intensity.
    """
    
    def __init__(
        self,
        obs_dim: int = 83,
        action_dim: int = 4,
        hidden_dim: int = 256,
    ):
        """
        Initialize CATC module.
        
        Args:
            obs_dim: Observation dimension
            action_dim: Number of actions
            hidden_dim: Hidden layer dimension
        """
        super().__init__()
        
        # Three policy networks for different weather regimes
        self.policy_clear = ClimatePolicyNetwork(obs_dim, action_dim, hidden_dim)
        self.policy_moderate = ClimatePolicyNetwork(obs_dim, action_dim, hidden_dim)
        self.policy_heavy = ClimatePolicyNetwork(obs_dim, action_dim, hidden_dim)
        
        # Current rain intensity
        self.current_rain = 0.0
        self.current_weights = (1.0, 0.0, 0.0)
        
        # Policy storage
        self.policies = {
            "clear": self.policy_clear,
            "moderate": self.policy_moderate,
            "heavy": self.policy_heavy,
        }
    
    def set_rain(self, rain_intensity: float):
        """
        Set current rain intensity.
        
        Args:
            rain_intensity: Rain intensity [0, 1]
        """
        self.current_rain = rain_intensity
        self.current_weights = mixing_weights(rain_intensity)
    
    def get_weights(self) -> Tuple[float, float, float]:
        """Get current mixing weights."""
        return self.current_weights
    
    def get_active_policy_name(self) -> str:
        """Get name of most active policy."""
        weights = self.current_weights
        idx = np.argmax(weights)
        return ["clear", "moderate", "heavy"][idx]
    
    def forward(self, obs: Tensor) -> Tensor:
        """
        Get mixed policy logits.
        
        Args:
            obs: Observation tensor
            
        Returns:
            Mixed logits
        """
        w1, w2, w3 = self.current_weights
        
        logits_clear = self.policy_clear(obs)
        logits_moderate = self.policy_moderate(obs)
        logits_heavy = self.policy_heavy(obs)
        
        # Weighted combination
        mixed_logits = w1 * logits_clear + w2 * logits_moderate + w3 * logits_heavy
        
        return mixed_logits
    
    def get_action(
        self, 
        obs: Tensor,
        deterministic: bool = False,
    ) -> Tuple[Tensor, Tensor, Tensor]:
        """
        Sample action from mixed policy.
        
        Args:
            obs: Observation tensor
            deterministic: If True, take argmax action
            
        Returns:
            Tuple of (action, log_prob, entropy)
        """
        if deterministic:
            # Take most likely action
            mixed_logits = self.forward(obs)
            action = mixed_logits.argmax(dim=-1)
            dist = Categorical(logits=mixed_logits)
            log_prob = dist.log_prob(action)
            entropy = dist.entropy()
        else:
            mixed_logits = self.forward(obs)
            dist = Categorical(logits=mixed_logits)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            entropy = dist.entropy()
        
        return action, log_prob, entropy
    
    def evaluate_actions(
        self,
        obs: Tensor,
        actions: Tensor,
    ) -> Tuple[Tensor, Tensor]:
        """
        Evaluate actions using mixed policy.
        
        Args:
            obs: Observation tensor
            actions: Actions tensor
            
        Returns:
            Tuple of (log_probs, entropies)
        """
        mixed_logits = self.forward(obs)
        dist = Categorical(logits=mixed_logits)
        
        log_probs = dist.log_prob(actions)
        entropies = dist.entropy()
        
        return log_probs, entropies
    
    def get_policy(self, regime: str) -> ClimatePolicyNetwork:
        """
        Get policy for a specific regime.
        
        Args:
            regime: "clear", "moderate", or "heavy"
            
        Returns:
            Policy network
        """
        return self.policies[regime]
    
    def set_policy(self, regime: str, state_dict: Dict):
        """
        Load policy weights from state dict.
        
        Args:
            regime: "clear", "moderate", or "heavy"
            state_dict: State dictionary to load
        """
        self.policies[regime].load_state_dict(state_dict)
    
    def get_mixing_stats(self) -> Dict:
        """Get mixing statistics."""
        return {
            "rain_intensity": self.current_rain,
            "weights": {
                "clear": self.current_weights[0],
                "moderate": self.current_weights[1],
                "heavy": self.current_weights[2],
            },
            "active_policy": self.get_active_policy_name(),
        }


class CATCTrainer:
    """
    Trainer for CATC module.
    
    Handles training of individual policies under different regimes.
    """
    
    def __init__(
        self,
        obs_dim: int = 83,
        action_dim: int = 4,
        hidden_dim: int = 256,
        lr: float = 3e-4,
    ):
        """
        Initialize CATC trainer.
        
        Args:
            obs_dim: Observation dimension
            action_dim: Number of actions
            hidden_dim: Hidden dimension
            lr: Learning rate
        """
        self.catc = CATCModule(obs_dim, action_dim, hidden_dim)
        self.optimizer = torch.optim.Adam(self.catc.parameters(), lr=lr)
        
        self.obs_dim = obs_dim
        self.action_dim = action_dim
    
    def train_policy(
        self,
        regime: str,
        obs: Tensor,
        actions: Tensor,
        advantages: Tensor,
    ) -> Dict[str, float]:
        """
        Train a specific policy regime.
        
        Args:
            regime: "clear", "moderate", or "heavy"
            obs: Observations
            actions: Actions
            advantages: Advantages
            
        Returns:
            Loss dictionary
        """
        policy = self.catc.get_policy(regime)
        
        logits = policy(obs)
        dist = Categorical(logits=logits)
        
        log_probs = dist.log_prob(actions)
        
        # PPO loss
        ratio = torch.exp(log_probs)
        surr1 = ratio * advantages
        surr2 = ratio.clamp(1 - 0.2, 1 + 0.2) * advantages
        
        actor_loss = -torch.min(surr1, surr2).mean()
        entropy_loss = -dist.entropy().mean()
        
        loss = actor_loss + 0.01 * entropy_loss
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return {
            "actor_loss": actor_loss.item(),
            "entropy_loss": entropy_loss.item(),
            "total_loss": loss.item(),
        }
    
    def get_module(self) -> CATCModule:
        """Get the CATC module."""
        return self.catc


def get_policy_capacity(regime: str) -> float:
    """
    Get capacity factor for a policy regime.
    
    Args:
        regime: "clear", "moderate", or "heavy"
        
    Returns:
        Capacity factor
    """
    capacities = {
        "clear": CAPACITY_CLEAR,
        "moderate": CAPACITY_MODERATE,
        "heavy": CAPACITY_HEAVY,
    }
    return capacities.get(regime, CAPACITY_CLEAR)
