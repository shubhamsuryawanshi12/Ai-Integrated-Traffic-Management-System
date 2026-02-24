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
import random

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch import Tensor
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not available. CATC module will be in dummy mode.")


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


class ClimatePolicyNetwork:
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
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        
        if TORCH_AVAILABLE:
            self.policy = nn.Sequential(
                nn.Linear(obs_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.LayerNorm(hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, action_dim),
            )
        else:
            self.policy = None
    
    def forward(self, obs) -> np.ndarray:
        """Get action logits."""
        if TORCH_AVAILABLE and self.policy is not None:
            return self.policy(obs).detach().numpy()
        else:
            return np.zeros(self.action_dim)
    
    def get_action(self, obs) -> Tuple[int, float, float]:
        """
        Sample action from policy.
        
        Returns:
            Tuple of (action, log_prob, entropy)
        """
        if TORCH_AVAILABLE and self.policy is not None:
            logits = self.forward(obs)
            dist = Categorical(logits=torch.from_numpy(logits))
            action = dist.sample().item()
            log_prob = dist.log_prob(torch.tensor(action)).item()
            entropy = dist.entropy().mean().item()
            return action, log_prob, entropy
        else:
            # Dummy action
            return random.randint(0, self.action_dim - 1), 0.0, 0.0


class CATCModule:
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
        
        self.obs_dim = obs_dim
        self.action_dim = action_dim
    
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
    
    def forward(self, obs: np.ndarray) -> np.ndarray:
        """
        Get mixed policy logits.
        
        Args:
            obs: Observation array
            
        Returns:
            Mixed logits
        """
        w1, w2, w3 = self.current_weights
        
        logits_clear = self.policy_clear.forward(obs)
        logits_moderate = self.policy_moderate.forward(obs)
        logits_heavy = self.policy_heavy.forward(obs)
        
        # Weighted combination
        mixed_logits = w1 * logits_clear + w2 * logits_moderate + w3 * logits_heavy
        
        return mixed_logits
    
    def get_action(
        self, 
        obs: np.ndarray,
        deterministic: bool = False,
    ) -> Tuple[int, float, float]:
        """
        Sample action from mixed policy.
        
        Args:
            obs: Observation array
            deterministic: If True, take argmax action
            
        Returns:
            Tuple of (action, log_prob, entropy)
        """
        w1, w2, w3 = self.current_weights
        
        if deterministic:
            # Take most likely action from mixed policy
            mixed_logits = self.forward(obs)
            action = int(np.argmax(mixed_logits))
            log_prob = 0.0
            entropy = 0.0
        else:
            # Sample from each policy and weight by mixing weights
            if w1 > 0.7:
                return self.policy_clear.get_action(obs)
            elif w2 > 0.7:
                return self.policy_moderate.get_action(obs)
            elif w3 > 0.7:
                return self.policy_heavy.get_action(obs)
            else:
                # Mixed - use clear policy as fallback
                return self.policy_clear.get_action(obs)
        
        return action, log_prob, entropy
    
    def get_policy(self, regime: str) -> ClimatePolicyNetwork:
        """
        Get policy for a specific regime.
        
        Args:
            regime: "clear", "moderate", or "heavy"
            
        Returns:
            Policy network
        """
        return self.policies.get(regime, self.policy_clear)
    
    def set_policy(self, regime: str, state_dict: dict):
        """
        Load policy weights from state dict.
        
        Args:
            regime: "clear", "moderate", or "heavy"
            state_dict: State dictionary to load
        """
        if regime in self.policies and TORCH_AVAILABLE:
            self.policies[regime].policy.load_state_dict(state_dict)
    
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
    
    def get_capacity_factor(self) -> float:
        """
        Get capacity factor based on current rain intensity.
        
        Returns:
            Capacity factor (0.6 to 1.0)
        """
        rain = self.current_rain
        if rain < RAIN_MODERATE:
            # Linear interpolation from 1.0 to 0.8
            return CAPACITY_CLEAR - (CAPACITY_CLEAR - CAPACITY_MODERATE) * (rain / RAIN_MODERATE)
        elif rain < RAIN_HEAVY:
            # Linear interpolation from 0.8 to 0.6
            return CAPACITY_MODERATE - (CAPACITY_MODERATE - CAPACITY_HEAVY) * ((rain - RAIN_MODERATE) / (RAIN_HEAVY - RAIN_MODERATE))
        else:
            return CAPACITY_HEAVY


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
