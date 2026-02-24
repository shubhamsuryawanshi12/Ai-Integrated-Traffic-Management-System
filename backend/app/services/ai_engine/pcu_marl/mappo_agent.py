"""
MAPPO Agent for PCU-MARL++.

Implements the Multi-Agent Proximal Policy Optimization algorithm
with centralized training and decentralized execution.
"""

from typing import Dict, Optional, Tuple, List
import numpy as np
import random

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch import Tensor
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not available. MAPPO Agent will be in dummy mode.")


# MAPPO hyperparameters
CLIP_EPS = 0.2
VALUE_CLIP = 0.2
ENTROPY_COEF = 0.01
VALUE_COEF = 0.5
LYAPUNOV_LAMBDA = 0.1
MAX_GRAD_NORM = 0.5


class MAPPOAgent:
    """
    MAPPO Agent for a single junction.
    
    Uses PPO with clipped surrogate objective for policy updates.
    Includes entropy bonus and Lyapunov stability term.
    """
    
    def __init__(
        self,
        agent_id: int,
        obs_dim: int = 83,
        action_dim: int = 4,
        actor_hidden: int = 256,
        critic_hidden: int = 128,
        lr_actor: float = 3e-4,
        lr_critic: float = 1e-3,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_eps: float = CLIP_EPS,
        entropy_coef: float = ENTROPY_COEF,
        value_coef: float = VALUE_COEF,
        lyapunov_lambda: float = LYAPUNOV_LAMBDA,
        device: str = "cpu",
    ):
        """
        Initialize MAPPO agent.
        
        Args:
            agent_id: Unique agent identifier
            obs_dim: Observation dimension
            action_dim: Action dimension
            actor_hidden: Actor hidden dimension
            critic_hidden: Critic hidden dimension
            lr_actor: Actor learning rate
            lr_critic: Critic learning rate
            gamma: Discount factor
            gae_lambda: GAE lambda
            clip_eps: PPO clipping epsilon
            entropy_coef: Entropy coefficient
            value_coef: Value loss coefficient
            lyapunov_lambda: Lyapunov term weight
            device: Device for tensors
        """
        self.agent_id = agent_id
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.device = device
        
        if TORCH_AVAILABLE:
            # Networks
            from .actor_critic import ActorNetwork, LocalCriticNetwork
            self.actor = ActorNetwork(obs_dim, action_dim, actor_hidden)
            self.local_critic = LocalCriticNetwork(obs_dim, critic_hidden)
            
            # Optimizers
            self.actor_optimizer = optim.Adam(self.actor.actor.parameters(), lr=lr_actor)
            self.critic_optimizer = optim.Adam(self.local_critic.critic.parameters(), lr=lr_critic)
        else:
            self.actor = None
            self.local_critic = None
            self.actor_optimizer = None
            self.critic_optimizer = None
        
        # Hyperparameters
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_eps = clip_eps
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.lyapunov_lambda = lyapunov_lambda
        
        # Buffer
        self.buffer = RolloutBuffer(obs_dim=obs_dim)
        
        # Training state
        self.steps = 0
    
    def select_action(
        self,
        obs: np.ndarray,
        deterministic: bool = False,
    ) -> Tuple[int, float, float]:
        """
        Select action given observation.
        
        Args:
            obs: Observation array
            deterministic: If True, take argmax
            
        Returns:
            Tuple of (action, log_prob, value)
        """
        if TORCH_AVAILABLE and self.actor is not None:
            obs_tensor = torch.from_numpy(obs).float().unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                value = self.local_critic(obs_tensor).item()
            
            action, log_prob, entropy = self.actor.get_action(obs_tensor, deterministic)
            
            action_val = action.item()
            log_prob_val = log_prob.item()
        else:
            # Dummy action
            action_val = random.randint(0, self.action_dim - 1)
            log_prob_val = 0.0
            value = 0.0
        
        self.steps += 1
        
        return action_val, log_prob_val, value
    
    def store_transition(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        log_prob: float,
        value: float,
        done: bool,
    ):
        """Store transition in buffer."""
        self.buffer.store(obs, action, reward, log_prob, value, done)
    
    def compute_loss(
        self,
        batch,
    ) -> Dict[str, float]:
        """
        Compute MAPPO loss.
        
        Args:
            batch: Rollout batch
            
        Returns:
            Dictionary of loss values
        """
        if not TORCH_AVAILABLE:
            return {"total": 0.0, "actor": 0.0, "value": 0.0, "entropy": 0.0, "lyapunov": 0.0}
        
        # Convert to tensors
        obs = torch.from_numpy(batch.obs).float().to(self.device)
        actions = torch.from_numpy(batch.actions).long().to(self.device)
        old_log_probs = torch.from_numpy(batch.old_log_probs).float().to(self.device)
        advantages = torch.from_numpy(batch.advantages).float().to(self.device)
        returns = torch.from_numpy(batch.returns).float().to(self.device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Actor loss (PPO clipped)
        log_probs, entropies = self.actor.evaluate_actions(obs, actions)
        
        ratio = torch.exp(log_probs - old_log_probs)
        
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.clip_eps, 1 + self.clip_eps) * advantages
        
        actor_loss = -torch.min(surr1, surr2).mean()
        
        # Entropy bonus
        entropy_loss = -entropies.mean()
        
        # Value loss
        values = self.local_critic(obs).squeeze(-1)
        value_loss = F.mse_loss(values, returns)
        
        # Lyapunov stability term
        lyapunov_loss = self.lyapunov_lambda * max(0, getattr(batch, 'delta_global_pcu_queue', 0))
        
        # Total loss
        total_loss = (
            actor_loss 
            + self.value_coef * value_loss 
            + self.entropy_coef * entropy_loss
            + lyapunov_loss
        )
        
        return {
            "total": total_loss,
            "actor": actor_loss.item(),
            "value": value_loss.item(),
            "entropy": entropy_loss.item(),
            "lyapunov": lyapunov_loss.item(),
        }
    
    def update(self, batch) -> Dict[str, float]:
        """
        Update agent using batch.
        
        Args:
            batch: Rollout batch
            
        Returns:
            Loss dictionary
        """
        if not TORCH_AVAILABLE:
            return {"total": 0.0, "actor": 0.0, "value": 0.0, "entropy": 0.0, "lyapunov": 0.0}
        
        # Compute losses
        losses = self.compute_loss(batch)
        
        # Update actor
        self.actor_optimizer.zero_grad()
        # Combine actor and entropy loss
        actor_total = losses["actor"] + self.entropy_coef * losses["entropy"]
        actor_total.backward()
        nn.utils.clip_grad_norm_(self.actor.actor.parameters(), MAX_GRAD_NORM)
        self.actor_optimizer.step()
        
        # Update critic
        self.critic_optimizer.zero_grad()
        losses["value"].backward()
        nn.utils.clip_grad_norm_(self.local_critic.critic.parameters(), MAX_GRAD_NORM)
        self.critic_optimizer.step()
        
        return losses
    
    def get_actor_params(self) -> dict:
        """Get actor parameters."""
        if TORCH_AVAILABLE:
            return self.actor.actor.state_dict()
        return {}
    
    def load_actor_params(self, state_dict: dict):
        """Load actor parameters."""
        if TORCH_AVAILABLE:
            self.actor.actor.load_state_dict(state_dict)
    
    def reset_buffer(self):
        """Reset the rollout buffer."""
        self.buffer.clear()
    
    def to(self, device: str):
        """Move to device."""
        self.device = device
        return self


class RolloutBuffer:
    """Buffer for storing rollout data."""
    
    def __init__(self, obs_dim: int, capacity: int = 10000):
        self.obs_dim = obs_dim
        self.capacity = capacity
        self.observations = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
        self.position = 0
        self.size = 0
    
    def store(self, obs: np.ndarray, action: int, reward: float, 
              log_prob: float, value: float, done: bool):
        """Store a transition."""
        if len(self.observations) < self.capacity:
            self.observations.append(obs)
            self.actions.append(action)
            self.rewards.append(reward)
            self.log_probs.append(log_prob)
            self.values.append(value)
            self.dones.append(done)
        else:
            idx = self.position
            self.observations[idx] = obs
            self.actions[idx] = action
            self.rewards[idx] = reward
            self.log_probs[idx] = log_prob
            self.values[idx] = value
            self.dones[idx] = done
        
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
    
    def clear(self):
        """Clear the buffer."""
        self.observations = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
        self.position = 0
        self.size = 0
    
    def __len__(self):
        return self.size
    
    def compute_gae(self, final_value: float = 0.0):
        """Compute GAE advantages."""
        advantages = np.zeros(self.size)
        gae = 0
        
        for t in reversed(range(self.size)):
            if t == self.size - 1:
                next_value = final_value
            else:
                next_value = self.values[t + 1]
            
            delta = self.rewards[t] + self.gamma * next_value * (1 - self.dones[t]) - self.values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - self.dones[t]) * gae
            advantages[t] = gae
        
        returns = advantages + np.array(self.values)
        
        return advantages, returns
    
    def get_batch(self, batch_size: int = 64):
        """Get a random batch."""
        if self.size < batch_size:
            batch_size = self.size
        
        indices = np.random.choice(self.size, batch_size, replace=False)
        
        batch = RolloutBatch(
            obs=np.array([self.observations[i] for i in indices]),
            actions=np.array([self.actions[i] for i in indices]),
            old_log_probs=np.array([self.log_probs[i] for i in indices]),
            advantages=np.zeros(batch_size),
            returns=np.zeros(batch_size),
        )
        
        advantages, returns = self.compute_gae()
        batch.advantages = np.array([advantages[i] for i in indices])
        batch.returns = np.array([returns[i] for i in indices])
        
        return batch


class RolloutBatch:
    """Batch of rollout data."""
    
    def __init__(self, obs, actions, old_log_probs, advantages, returns):
        self.obs = obs
        self.actions = actions
        self.old_log_probs = old_log_probs
        self.advantages = advantages
        self.returns = returns
        self.delta_global_pcu_queue = 0.0


class CentralizedMAPPO:
    """
    Centralized MAPPO system managing all agents.
    """
    
    def __init__(
        self,
        n_agents: int = 12,
        obs_dim: int = 83,
        action_dim: int = 4,
        actor_hidden: int = 256,
        critic_hidden: int = 128,
        lr_actor: float = 3e-4,
        lr_critic: float = 1e-3,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_eps: float = CLIP_EPS,
        entropy_coef: float = ENTROPY_COEF,
        value_coef: float = VALUE_COEF,
        lyapunov_lambda: float = LYAPUNOV_LAMBDA,
        device: str = "cpu",
    ):
        """
        Initialize centralized MAPPO.
        
        Args:
            n_agents: Number of agents
            obs_dim: Observation dimension
            action_dim: Action dimension
            actor_hidden: Actor hidden dimension
            critic_hidden: Critic hidden dimension
            lr_actor: Actor learning rate
            lr_critic: Critic learning rate
            gamma: Discount factor
            gae_lambda: GAE lambda
            clip_eps: PPO clipping epsilon
            entropy_coef: Entropy coefficient
            value_coef: Value loss coefficient
            lyapunov_lambda: Lyapunov term weight
            device: Device for tensors
        """
        self.n_agents = n_agents
        self.device = device
        
        # Create agents
        self.agents = [
            MAPPOAgent(
                agent_id=i,
                obs_dim=obs_dim,
                action_dim=action_dim,
                actor_hidden=actor_hidden,
                critic_hidden=critic_hidden,
                lr_actor=lr_actor,
                lr_critic=lr_critic,
                gamma=gamma,
                gae_lambda=gae_lambda,
                clip_eps=clip_eps,
                entropy_coef=entropy_coef,
                value_coef=value_coef,
                lyapunov_lambda=lyapunov_lambda,
                device=device,
            )
            for i in range(n_agents)
        ]
        
        # Storage for rollouts
        self.rollouts = {i: [] for i in range(n_agents)}
    
    def select_actions(
        self,
        observations: Dict[int, np.ndarray],
        deterministic: bool = False,
    ) -> Dict[int, Tuple[int, float, float]]:
        """
        Select actions for all agents.
        
        Args:
            observations: Dict of observations
            deterministic: If True, deterministic actions
            
        Returns:
            Dict of (action, log_prob, value)
        """
        results = {}
        
        for agent_id, obs in observations.items():
            if agent_id < len(self.agents):
                action, log_prob, value = self.agents[agent_id].select_action(
                    obs, deterministic
                )
                results[agent_id] = (action, log_prob, value)
        
        return results
    
    def store_transitions(
        self,
        agent_id: int,
        obs: np.ndarray,
        action: int,
        reward: float,
        log_prob: float,
        value: float,
        done: bool,
    ):
        """Store transition for agent."""
        if agent_id < len(self.agents):
            self.agents[agent_id].store_transition(
                obs, action, reward, log_prob, value, done
            )
    
    def update_all(
        self,
        global_obs: np.ndarray,
        n_epochs: int = 10,
        batch_size: int = 64,
    ) -> Dict[str, float]:
        """
        Update all agents.
        
        Args:
            global_obs: Global observation for centralized critic
            n_epochs: Number of PPO epochs
            batch_size: Batch size
            
        Returns:
            Average loss dictionary
        """
        all_losses = []
        
        for agent in self.agents:
            if len(agent.buffer) == 0:
                continue
            
            # Compute GAE
            agent.buffer.compute_gae(final_value=0.0)
            
            # PPO update
            for _ in range(n_epochs):
                batch = agent.buffer.get_batch(batch_size)
                losses = agent.update(batch)
                all_losses.append(losses)
        
        # Average losses
        if all_losses:
            avg_losses = {}
            for key in all_losses[0].keys():
                avg_losses[key] = np.mean([l[key] for l in all_losses])
            return avg_losses
        
        return {}
    
    def get_all_actor_params(self) -> List[dict]:
        """Get parameters for all actors."""
        return [agent.get_actor_params() for agent in self.agents]
    
    def load_all_actor_params(self, params_list: List[dict]):
        """Load parameters for all actors."""
        for i, params in enumerate(params_list):
            if i < len(self.agents):
                self.agents[i].load_actor_params(params)
    
    def reset_all_buffers(self):
        """Reset all agent buffers."""
        for agent in self.agents:
            agent.reset_buffer()
    
    def to(self, device: str):
        """Move all to device."""
        self.device = device
        for agent in self.agents:
            agent.to(device)
        return self


def create_mappo(
    n_agents: int = 12,
    obs_dim: int = 83,
    action_dim: int = 4,
    device: str = "cpu",
) -> CentralizedMAPPO:
    """
    Factory function to create MAPPO system.
    
    Args:
        n_agents: Number of agents
        obs_dim: Observation dimension
        action_dim: Action dimension
        device: Device
        
    Returns:
        CentralizedMAPPO instance
    """
    return CentralizedMAPPO(
        n_agents=n_agents,
        obs_dim=obs_dim,
        action_dim=action_dim,
        device=device,
    )
