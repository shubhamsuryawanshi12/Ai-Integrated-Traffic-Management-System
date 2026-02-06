import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from typing import Dict

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
        self.model = ActorCritic(state_dim, action_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.gamma = gamma
        self.action_dim = action_dim
        
        # Memory
        self.log_probs = []
        self.values = []
        self.rewards = []
        self.masks = []

    def get_action(self, state: np.ndarray):
        state_tensor = torch.FloatTensor(state)
        policy, value = self.model(state_tensor)
        
        action_dist = torch.distributions.Categorical(policy)
        action = action_dist.sample()
        
        return action.item(), action_dist.log_prob(action), value

    def store_outcome(self, log_prob, value, reward, done):
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.rewards.append(reward)
        self.masks.append(1 - int(done))

    def update(self):
        """Perform a policy update using collected experiences (A2C/A3C style)"""
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
        torch.save(self.model.state_dict(), path)

    def load(self, path):
        self.model.load_state_dict(torch.load(path))
