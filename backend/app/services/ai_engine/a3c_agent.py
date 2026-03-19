import os
import random
from typing import Dict, List, Any

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: Torch not available. A3C Agent will be in dummy mode.")

if TORCH_AVAILABLE:
    class GlobalA3CNetwork(nn.Module):
        def __init__(self, input_dim, action_dim, hidden_dim=128):
            super(GlobalA3CNetwork, self).__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim)
            
            # Actor head
            self.actor = nn.Linear(hidden_dim, action_dim)
            
            # Critic head
            self.critic = nn.Linear(hidden_dim, 1)

        def forward(self, x):
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            policy = F.softmax(self.actor(x), dim=-1)
            value = self.critic(x)
            return policy, value

class IntersectionWorker:
    def __init__(self, worker_id: str, global_model, optimizer, state_dim: int, action_dim: int, gamma: float = 0.99):
        self.worker_id = worker_id
        self.global_model = global_model
        self.optimizer = optimizer
        self.action_dim = action_dim
        self.gamma = gamma
        
        if TORCH_AVAILABLE:
            self.local_model = GlobalA3CNetwork(state_dim, action_dim)
            self.local_model.load_state_dict(self.global_model.state_dict())
            
        self.log_probs = []
        self.values = []
        self.rewards = []
        self.masks = []
        
    def get_action(self, state: Any):
        if not TORCH_AVAILABLE:
            return random.randint(0, self.action_dim - 1), 0.0, 0.0
            
        if isinstance(state, list):
            if NUMPY_AVAILABLE:
                state = np.array(state, dtype=np.float32)
            else:
                state = torch.tensor(state, dtype=torch.float32)
                
        if NUMPY_AVAILABLE and isinstance(state, np.ndarray):
            state_tensor = torch.FloatTensor(state)
        elif isinstance(state, torch.Tensor):
            state_tensor = state
        else:
            state_tensor = torch.tensor(state, dtype=torch.float32)

        policy, value = self.local_model(state_tensor)
        
        action_dist = torch.distributions.Categorical(policy)
        action = action_dist.sample()
        
        return action.item(), action_dist.log_prob(action), value

    def store_outcome(self, log_prob, value, reward, done):
        if TORCH_AVAILABLE:
            self.log_probs.append(log_prob)
            self.values.append(value)
            self.rewards.append(reward)
            self.masks.append(1 - int(done))

    def update(self):
        if not TORCH_AVAILABLE or len(self.rewards) == 0:
            return 0.0

        discounted_rewards = []
        R = 0
        
        for r, mask in zip(reversed(self.rewards), reversed(self.masks)):
            R = r + self.gamma * R * mask
            discounted_rewards.insert(0, R)
            
        discounted_rewards = torch.FloatTensor(discounted_rewards)
        log_probs = torch.stack(self.log_probs)
        values = torch.stack(self.values).squeeze()
        
        # Ensure values and discounted_rewards have the same shape
        if values.dim() == 0:
            values = values.unsqueeze(0)
            
        advantage = discounted_rewards - values.detach()
        
        actor_loss = -(log_probs * advantage).mean()
        critic_loss = F.mse_loss(values, discounted_rewards)
        
        loss = actor_loss + 0.5 * critic_loss
        
        self.optimizer.zero_grad()
        loss.backward()
        
        # Manually apply gradients to global network
        for global_param, local_param in zip(self.global_model.parameters(), self.local_model.parameters()):
            if local_param.grad is not None:
                global_param._grad = local_param.grad
        
        self.optimizer.step()
        
        # Sync local model with global model
        self.local_model.load_state_dict(self.global_model.state_dict())
        
        # Clear memory
        self.log_probs = []
        self.values = []
        self.rewards = []
        self.masks = []
        
        return loss.item()

class RLAgent:
    """Wrapper class to maintain API compatibility with the old A2C agent, utilizing the A3C architecture."""
    def __init__(self, state_dim: int, action_dim: int, lr: float = 1e-3, gamma: float = 0.99):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr
        self.gamma = gamma
        self.workers = {}
        
        if TORCH_AVAILABLE:
            self.global_model = GlobalA3CNetwork(state_dim, action_dim)
            self.global_optimizer = optim.Adam(self.global_model.parameters(), lr=lr)
        else:
            self.global_model = None
            self.global_optimizer = None
            
        # Default worker for when no intersection ID is provided
        self.default_worker = self._get_worker("default")

    def _get_worker(self, intersection_id: str):
        if intersection_id not in self.workers:
            self.workers[intersection_id] = IntersectionWorker(
                worker_id=intersection_id,
                global_model=self.global_model,
                optimizer=self.global_optimizer,
                state_dim=self.state_dim,
                action_dim=self.action_dim,
                gamma=self.gamma
            )
        return self.workers[intersection_id]

    def get_action(self, state: Any, intersection_id: str = "default"):
        worker = self._get_worker(intersection_id)
        return worker.get_action(state)

    def store_outcome(self, log_prob, value, reward, done, intersection_id: str = "default"):
        worker = self._get_worker(intersection_id)
        worker.store_outcome(log_prob, value, reward, done)

    def update(self, intersection_id: str = "default"):
        worker = self._get_worker(intersection_id)
        return worker.update()

    def update_all(self):
        """Update all workers. Useful for continuous learning."""
        total_loss = 0.0
        for worker in self.workers.values():
            total_loss += worker.update()
        return total_loss

    def save(self, path):
        if TORCH_AVAILABLE:
            torch.save(self.global_model.state_dict(), path)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write("DUMMY_MODEL_WEIGHTS: A3C Training simulated without PyTorch.")

    def load(self, path):
        if TORCH_AVAILABLE and os.path.exists(path):
            self.global_model.load_state_dict(torch.load(path))
            for worker in self.workers.values():
                worker.local_model.load_state_dict(self.global_model.state_dict())
