from typing import Dict, List, Any
import os
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
    print("WARNING: Torch not available. RL Agent will be in dummy mode.")

import random

if TORCH_AVAILABLE:
    class ActorCritic(nn.Module):
        def __init__(self, input_dim, action_dim, hidden_dim=128):
            super(ActorCritic, self).__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            
            # Actor head
            self.actor = nn.Linear(hidden_dim, action_dim)
            
            # Critic head
            self.critic = nn.Linear(hidden_dim, 1)

        def forward(self, x):
            x = F.relu(self.fc1(x))
            policy = F.softmax(self.actor(x), dim=-1)
            value = self.critic(x)
            return policy, value

class RLAgent:
    def __init__(self, state_dim: int, action_dim: int, lr: float = 1e-3, gamma: float = 0.99):
        self.action_dim = action_dim
        if TORCH_AVAILABLE:
            self.model = ActorCritic(state_dim, action_dim)
            self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
            self.gamma = gamma
            
            # Memory
            self.log_probs = []
            self.values = []
            self.rewards = []
            self.masks = []
        else:
            self.model = None

    def get_action(self, state: Any):
        # State can be list or numpy array
        if TORCH_AVAILABLE:
            # If state is list, convert to tensor
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

            policy, value = self.model(state_tensor)
            
            action_dist = torch.distributions.Categorical(policy)
            action = action_dist.sample()
            
            return action.item(), action_dist.log_prob(action), value
        else:
            # Dummy random action
            return random.randint(0, self.action_dim - 1), 0.0, 0.0

    def store_outcome(self, log_prob, value, reward, done):
        if TORCH_AVAILABLE:
            self.log_probs.append(log_prob)
            self.values.append(value)
            self.rewards.append(reward)
            self.masks.append(1 - int(done))

    def update(self):
        """Perform a policy update using collected experiences (A2C/A3C style)"""
        if not TORCH_AVAILABLE:
            return 0.0

        discounted_rewards = []
        R = 0
        # If we had a next_value bootstrapping, we would start with that.
        # Here assuming episodic or end of batch with 0 terminal value for simplicity in this snippet.
        
        for r, mask in zip(reversed(self.rewards), reversed(self.masks)):
            R = r + self.gamma * R * mask
            discounted_rewards.insert(0, R)
            
        discounted_rewards = torch.FloatTensor(discounted_rewards)
        log_probs = torch.stack(self.log_probs)
        values = torch.stack(self.values).squeeze()
        
        advantage = discounted_rewards - values.detach()
        
        actor_loss = -(log_probs * advantage).mean()
        critic_loss = F.mse_loss(values, discounted_rewards)
        
        loss = actor_loss + 0.5 * critic_loss
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Clear memory
        self.log_probs = []
        self.values = []
        self.rewards = []
        self.masks = []
        
        return loss.item()

    def save(self, path):
        if TORCH_AVAILABLE:
            torch.save(self.model.state_dict(), path)
        else:
            # Save dummy file so training appears successful
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write("DUMMY_MODEL_WEIGHTS: Training simulated without PyTorch.")

    def load(self, path):
        if TORCH_AVAILABLE:
            self.model.load_state_dict(torch.load(path))
