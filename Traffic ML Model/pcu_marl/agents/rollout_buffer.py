"""
Rollout Buffer for PCU-MARL++.

Stores trajectories and computes GAE (Generalized Advantage Estimation).
"""

from typing import Optional, Dict, List
import numpy as np
from dataclasses import dataclass, field
from collections import deque


# GAE parameters
DEFAULT_GAMMA = 0.99
DEFAULT_LAMBDA = 0.95


@dataclass
class RolloutData:
    """Single step of rollout data."""
    obs: np.ndarray
    action: int
    reward: float
    log_prob: float
    value: float
    done: bool


@dataclass
class RolloutBatch:
    """Batch of rollout data for training."""
    obs: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    old_log_probs: np.ndarray
    values: np.ndarray
    dones: np.ndarray
    advantages: np.ndarray = field(default=None)
    returns: np.ndarray = field(default=None)
    delta_global_pcu_queue: float = field(default=0.0)


class RolloutBuffer:
    """
    Rollout buffer for storing trajectories.
    
    Stores observations, actions, rewards, log_probs, values, and dones.
    Computes GAE advantages for PPO updates.
    """
    
    def __init__(
        self,
        buffer_size: int = 400,
        obs_dim: int = 83,
        gamma: float = DEFAULT_GAMMA,
        gae_lambda: float = DEFAULT_LAMBDA,
    ):
        """
        Initialize rollout buffer.
        
        Args:
            buffer_size: Maximum buffer size (rollout length)
            obs_dim: Observation dimension
            gamma: Discount factor
            gae_lambda: GAE lambda parameter
        """
        self.buffer_size = buffer_size
        self.obs_dim = obs_dim
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        
        # Storage
        self.obs = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
        
        # For GAE
        self.next_value = 0.0
        self.advantages = []
        self.returns = []
        
        # For Lyapunov term
        self.global_queue_history = []
    
    def store(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        log_prob: float,
        value: float,
        done: bool,
    ):
        """
        Store a step of rollout data.
        
        Args:
            obs: Observation
            action: Action taken
            reward: Reward received
            log_prob: Log probability of action
            value: Value estimate
            done: Done flag
        """
        self.obs.append(obs)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)
    
    def store_global_queue(self, queue: float):
        """Store global queue for Lyapunov term."""
        self.global_queue_history.append(queue)
    
    def compute_gae(
        self,
        final_value: float = 0.0,
    ) -> RolloutBatch:
        """
        Compute GAE advantages and returns.
        
        Args:
            final_value: Value estimate for final step (bootstrap)
            
        Returns:
            RolloutBatch with advantages and returns
        """
        self.next_value = final_value
        
        advantages = np.zeros(len(self.rewards))
        returns = np.zeros(len(self.rewards))
        
        # GAE computation (backward pass)
        gae = 0
        for t in reversed(range(len(self.rewards))):
            if t == len(self.rewards) - 1:
                next_value = final_value
            else:
                next_value = self.values[t + 1]
            
            delta = self.rewards[t] + self.gamma * next_value * (1 - self.dones[t]) - self.values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - self.dones[t]) * gae
            
            advantages[t] = gae
            returns[t] = gae + self.values[t]
        
        self.advantages = advantages
        self.returns = returns
        
        # Compute Lyapunov delta
        lyapunov_delta = 0.0
        if len(self.global_queue_history) >= 2:
            lyapunov_delta = self.global_queue_history[-1] - self.global_queue_history[-2]
        
        # Convert to arrays
        batch = RolloutBatch(
            obs=np.array(self.obs, dtype=np.float32),
            actions=np.array(self.actions, dtype=np.int64),
            rewards=np.array(self.rewards, dtype=np.float32),
            old_log_probs=np.array(self.log_probs, dtype=np.float32),
            values=np.array(self.values, dtype=np.float32),
            dones=np.array(self.dones, dtype=np.float32),
            advantages=advantages,
            returns=returns,
            delta_global_pcu_queue=lyapunov_delta,
        )
        
        return batch
    
    def get_batch(
        self,
        batch_size: int = 64,
    ) -> RolloutBatch:
        """
        Get a random batch for training.
        
        Args:
            batch_size: Batch size
            
        Returns:
            RolloutBatch
        """
        n = len(self.obs)
        
        if n == 0:
            raise ValueError("Buffer is empty")
        
        # Compute GAE if not done
        if len(self.advantages) != n:
            self.compute_gae()
        
        # Random indices
        indices = np.random.choice(n, size=min(batch_size, n), replace=False)
        
        batch = RolloutBatch(
            obs=self.obs[indices] if isinstance(self.obs[0], np.ndarray) else np.array(self.obs)[indices],
            actions=np.array(self.actions)[indices],
            rewards=np.array(self.rewards)[indices],
            old_log_probs=np.array(self.log_probs)[indices],
            values=np.array(self.values)[indices],
            dones=np.array(self.dones)[indices],
            advantages=self.advantages[indices],
            returns=self.returns[indices],
            delta_global_pcu_queue=0.0,
        )
        
        return batch
    
    def get_all(self) -> RolloutBatch:
        """Get all data as a batch."""
        if len(self.advantages) != len(self.obs):
            self.compute_gae()
        
        return RolloutBatch(
            obs=np.array(self.obs, dtype=np.float32),
            actions=np.array(self.actions, dtype=np.int64),
            rewards=np.array(self.rewards, dtype=np.float32),
            old_log_probs=np.array(self.log_probs, dtype=np.float32),
            values=np.array(self.values, dtype=np.float32),
            dones=np.array(self.dones, dtype=np.float32),
            advantages=np.array(self.advantages, dtype=np.float32),
            returns=np.array(self.returns, dtype=np.float32),
            delta_global_pcu_queue=(
                self.global_queue_history[-1] - self.global_queue_history[-2]
                if len(self.global_queue_history) >= 2 else 0.0
            ),
        )
    
    def clear(self):
        """Clear the buffer."""
        self.obs = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
        self.advantages = []
        self.returns = []
        self.global_queue_history = []
    
    def __len__(self) -> int:
        """Get current buffer size."""
        return len(self.obs)
    
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return len(self.obs) >= self.buffer_size


class MultiAgentBuffer:
    """
    Buffer manager for multi-agent scenario.
    
    Maintains separate buffers for each agent.
    """
    
    def __init__(
        self,
        n_agents: int = 12,
        buffer_size: int = 400,
        obs_dim: int = 83,
        gamma: float = DEFAULT_GAMMA,
        gae_lambda: float = DEFAULT_LAMBDA,
    ):
        """
        Initialize multi-agent buffer.
        
        Args:
            n_agents: Number of agents
            buffer_size: Buffer size per agent
            obs_dim: Observation dimension
            gamma: Discount factor
            gae_lambda: GAE lambda
        """
        self.n_agents = n_agents
        
        # Create buffer for each agent
        self.buffers = [
            RolloutBuffer(buffer_size, obs_dim, gamma, gae_lambda)
            for _ in range(n_agents)
        ]
    
    def store(
        self,
        agent_id: int,
        obs: np.ndarray,
        action: int,
        reward: float,
        log_prob: float,
        value: float,
        done: bool,
    ):
        """Store data for specific agent."""
        self.buffers[agent_id].store(obs, action, reward, log_prob, value, done)
    
    def store_global_queue(self, agent_id: int, queue: float):
        """Store global queue for Lyapunov term."""
        self.buffers[agent_id].store_global_queue(queue)
    
    def compute_gae(self, final_values: Optional[List[float]] = None):
        """Compute GAE for all agents."""
        if final_values is None:
            final_values = [0.0] * self.n_agents
        
        for i, buffer in enumerate(self.buffers):
            buffer.compute_gae(final_values[i])
    
    def get_agent_batch(self, agent_id: int, batch_size: int = 64) -> RolloutBatch:
        """Get batch for specific agent."""
        return self.buffers[agent_id].get_batch(batch_size)
    
    def get_all_batches(self) -> List[RolloutBatch]:
        """Get batches for all agents."""
        return [buffer.get_all() for buffer in self.buffers]
    
    def clear_all(self):
        """Clear all buffers."""
        for buffer in self.buffers:
            buffer.clear()
    
    def __len__(self) -> int:
        """Get buffer length (all same)."""
        return len(self.buffers[0])
