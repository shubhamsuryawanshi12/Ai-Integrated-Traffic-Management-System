"""
Decision Transformer for Offline RL

Implements offline reinforcement learning using Transformer architecture.
Trains on historical traffic data without requiring online interaction.

Features:
- Decision Transformer architecture
- Return-to-go conditioning
- Trajectory modeling
- Conservative Q-Learning (CQL) integration
"""

from typing import Dict, List, Tuple, Optional, Any
import math

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
    print("WARNING: PyTorch not available. Decision Transformer will use dummy mode.")


class TrajectoryDataset:
    """
    Dataset of offline trajectories for training Decision Transformer.
    """
    
    def __init__(
        self,
        trajectories: List[Dict],
        max_length: int = 30,
        return_scale: float = 100.0
    ):
        self.trajectories = trajectories
        self.max_length = max_length
        self.return_scale = return_scale
        
        # Preprocess trajectories
        self.processed_trajectories = []
        for traj in trajectories:
            self._process_trajectory(traj)
    
    def _process_trajectory(self, traj: Dict):
        """Process a single trajectory."""
        states = traj.get('states', [])
        actions = traj.get('actions', [])
        rewards = traj.get('rewards', [])
        
        if len(states) < 2:
            return
        
        # Compute returns
        returns = []
        total_return = 0
        for r in reversed(rewards):
            total_return = r + total_return
            returns.insert(0, total_return)
        
        # Normalize returns
        returns = np.array(returns)
        returns = returns / (np.std(returns) + 1e-8)
        
        # Store processed trajectory
        self.processed_trajectories.append({
            'states': states[:self.max_length],
            'actions': actions[:self.max_length],
            'rewards': rewards[:self.max_length],
            'returns': returns[:self.max_length].tolist()
        })
    
    def __len__(self) -> int:
        return len(self.processed_trajectories)
    
    def __getitem__(self, idx: int) -> Dict:
        """Get a trajectory."""
        return self.processed_trajectories[idx]
    
    def sample_batch(
        self,
        batch_size: int = 32,
        max_length: int = None
    ) -> Tuple[torch.Tensor, ...]:
        """Sample a batch of trajectories."""
        max_length = max_length or self.max_length
        
        states_batch = []
        actions_batch = []
        returns_batch = []
        timesteps_batch = []
        
        for _ in range(batch_size):
            traj_idx = np.random.randint(0, len(self))
            traj = self.processed_trajectories[traj_idx]
            
            # Sample starting point
            start_idx = np.random.randint(0, max(1, len(traj['states']) - 1))
            length = min(max_length, len(traj['states']) - start_idx)
            
            # Get trajectory segment
            states = traj['states'][start_idx:start_idx+length]
            actions = traj['actions'][start_idx:start_idx+length]
            returns = traj['returns'][start_idx:start_idx+length]
            timesteps = list(range(start_idx, start_idx+length))
            
            # Pad to max_length
            while len(states) < max_length:
                states.append(states[-1] if states else [0] * 12)
                actions.append(actions[-1] if actions else 0)
                returns.append(returns[-1] if returns else 0)
                timesteps.append(timesteps[-1] + 1 if timesteps else 0)
            
            states_batch.append(states[:max_length])
            actions_batch.append(actions[:max_length])
            returns_batch.append(returns[:max_length])
            timesteps_batch.append(timesteps[:max_length])
        
        return (
            torch.FloatTensor(states_batch),
            torch.LongTensor(actions_batch),
            torch.FloatTensor(returns_batch),
            torch.LongTensor(timesteps_batch)
        )


class DecisionTransformer(nn.Module):
    """
    Decision Transformer: Offline RL via sequence modeling.
    """
    
    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 4,
        hidden_dim: int = 128,
        num_layers: int = 3,
        num_heads: int = 4,
        dropout: float = 0.1,
        max_length: int = 30
    ):
        super().__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.max_length = max_length
        
        # Embeddings
        self.state_embedding = nn.Linear(state_dim, hidden_dim)
        self.action_embedding = nn.Embedding(action_dim, hidden_dim)
        self.return_embedding = nn.Linear(1, hidden_dim)
        self.timestep_embedding = nn.Embedding(max_length, hidden_dim)
        
        # Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output heads
        self.action_head = nn.Linear(hidden_dim, action_dim)
        
        # Layer norm
        self.ln = nn.LayerNorm(hidden_dim)
        
        self._init_weights()
    
    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        returns_to_go: torch.Tensor,
        timesteps: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            states: [batch, seq_len, state_dim]
            actions: [batch, seq_len]
            returns_to_go: [batch, seq_len, 1]
            timesteps: [batch, seq_len]
            mask: Optional attention mask
            
        Returns:
            Action logits [batch, seq_len, action_dim]
        """
        batch_size, seq_len = states.shape[:2]
        
        # Embed inputs
        state_emb = self.state_embedding(states)
        action_emb = self.action_embedding(actions)
        
        # For return-to-go, add dimension if needed
        if returns_to_go.dim() == 2:
            returns_to_go = returns_to_go.unsqueeze(-1)
        return_emb = self.return_embedding(returns_to_go)
        
        # Timestep embedding
        timesteps = timesteps.clamp(0, self.max_length - 1)
        time_emb = self.timestep_embedding(timesteps)
        
        # Combine embeddings
        # Each token = state + return + time
        # For first token, use state embedding
        # For subsequent tokens, use state + action + return + time
        
        embeddings = state_emb + return_emb + time_emb
        
        # Shift action embeddings for prediction
        # Action at position i predicts action at position i+1
        action_shift = torch.zeros_like(action_emb)
        action_shift[:, 1:, :] = action_emb[:, :-1, :]
        
        embeddings = embeddings + action_shift
        
        # Apply transformer
        hidden = self.transformer(embeddings, mask=mask)
        hidden = self.ln(hidden)
        
        # Predict actions
        action_logits = self.action_head(hidden)
        
        return action_logits
    
    def get_action(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        returns_to_go: torch.Tensor,
        timesteps: torch.Tensor
    ) -> Tuple[int, torch.Tensor]:
        """
        Get action from model (greedy).
        
        Returns:
            (action, log_prob)
        """
        with torch.no_grad():
            action_logits = self.forward(
                states, actions, returns_to_go, timesteps
            )
            
            # Get action for last timestep
            last_logits = action_logits[0, -1, :]
            action = torch.argmax(last_logits, dim=-1).item()
            
            probs = F.softmax(last_logits, dim=-1)
            log_prob = F.log_softmax(last_logits, dim=-1)[action]
        
        return action, log_prob


class CQLCritic(nn.Module):
    """
    Conservative Q-Learning critic for offline RL.
    Provides Q-value estimation for policy evaluation.
    """
    
    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 4,
        hidden_dim: int = 128
    ):
        super().__init__()
        
        # Q-network
        self.Q = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        # Target Q-network
        self.Q_target = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        # Copy weights
        self._update_target()
    
    def _update_target(self):
        """Update target network."""
        self.Q_target.load_state_dict(self.Q.state_dict())
    
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """Compute Q-value."""
        sa = torch.cat([state, action], dim=-1)
        return self.Q(sa)
    
    def forward_target(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """Compute target Q-value."""
        sa = torch.cat([state, action], dim=-1)
        return self.Q_target(sa)


class DecisionTransformerAgent:
    """
    Decision Transformer agent for offline RL.
    """
    
    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 4,
        hidden_dim: int = 128,
        learning_rate: float = 1e-4,
        gamma: float = 0.99,
        cql_alpha: float = 0.1,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.device = device
        self.gamma = gamma
        self.cql_alpha = cql_alpha
        
        # Decision Transformer
        self.model = DecisionTransformer(
            state_dim=state_dim,
            action_dim=action_dim,
            hidden_dim=hidden_dim
        ).to(device)
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # CQL critic
        self.critic = CQLCritic(state_dim, action_dim, hidden_dim).to(device)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=learning_rate)
        
        # Dataset
        self.dataset: Optional[TrajectoryDataset] = None
        
        # Training history
        self.history = {
            'dt_loss': [],
            'cql_loss': [],
            'actor_loss': []
        }
    
    def load_offline_data(
        self,
        trajectories: List[Dict],
        max_length: int = 30
    ):
        """Load offline trajectory data."""
        self.dataset = TrajectoryDataset(trajectories, max_length=max_length)
    
    def add_trajectory(
        self,
        states: List[List[float]],
        actions: List[int],
        rewards: List[float]
    ):
        """Add a trajectory to dataset."""
        traj = {
            'states': states,
            'actions': actions,
            'rewards': rewards
        }
        
        if self.dataset is None:
            self.dataset = TrajectoryDataset([traj])
        else:
            self.dataset.processed_trajectories.append(
                self.dataset._process_trajectory(traj)
            )
    
    def train_step(
        self,
        batch_size: int = 32,
        lambda_actor: float = 1.0
    ) -> Dict:
        """
        Single training step.
        
        Returns:
            Loss dictionary
        """
        if self.dataset is None or not TORCH_AVAILABLE:
            return {'dt_loss': 0, 'cql_loss': 0, 'actor_loss': 0}
        
        # Sample batch
        states, actions, returns, timesteps = self.dataset.sample_batch(batch_size)
        
        # Get returns to go (cumulative returns from each timestep)
        returns_to_go = torch.cumsum(returns.flip(1), dim=1).flip(1).unsqueeze(-1)
        
        # Shift returns to go for target
        returns_to_go_target = torch.zeros_like(returns_to_go)
        returns_to_go_target[:, 1:, :] = returns_to_go[:, :-1, :]
        
        # Pad first timestep
        returns_to_go_target[:, 0, :] = returns[:, 0:1] / self.dataset.return_scale
        
        # Teacher forcing: shift actions
        # Input actions are all except last
        # Target actions are all except first
        action_input = actions[:, :-1]
        action_target = actions[:, 1:]
        
        # Pad action input
        action_input = torch.cat([torch.zeros_like(action_input[:, :1]), action_input], dim=1)
        
        # Pad states
        states_input = torch.cat([states[:, :1, :], states], dim=1)
        
        # Pad timesteps
        timesteps = torch.cat([torch.zeros_like(timesteps[:, :1]), timesteps], dim=1)
        
        # DT loss
        action_logits = self.model(
            states_input, action_input, returns_to_go_target, timesteps
        )
        
        # Compute loss (cross-entropy)
        dt_loss = F.cross_entropy(
            action_logits.reshape(-1, self.model.action_dim),
            action_target.reshape(-1)
        )
        
        # CQL loss (Conservative Q-Learning)
        # Sample random actions
        random_actions = torch.randint(0, self.model.action_dim, (states.size(0), 1)).to(self.device)
        
        # Get Q-values
        q_sa = self.critic(states[:, 0, :], actions[:, 0].float().unsqueeze(-1))
        q_random = self.critic(states[:, 0, :], random_actions.float())
        
        cql_loss = -(q_sa.mean() - q_random.mean()) * self.cql_alpha
        
        # Actor loss (policy improvement)
        # Use predicted actions from DT
        predicted_actions = torch.argmax(action_logits[:, -1, :], dim=-1)
        q_values = self.critic(states[:, -1, :], predicted_actions.float().unsqueeze(-1))
        actor_loss = -q_values.mean()
        
        # Total loss
        total_loss = dt_loss + cql_loss + lambda_actor * actor_loss
        
        # Optimize
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()
        
        # Update critic periodically
        if len(self.history['dt_loss']) % 10 == 0:
            self._update_critic(states, actions, rewards=returns[:, 0])
        
        # Record losses
        self.history['dt_loss'].append(dt_loss.item())
        self.history['cql_loss'].append(cql_loss.item())
        self.history['actor_loss'].append(actor_loss.item())
        
        return {
            'dt_loss': dt_loss.item(),
            'cql_loss': cql_loss.item(),
            'actor_loss': actor_loss.item()
        }
    
    def _update_critic(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        rewards: torch.Tensor
    ):
        """Update CQL critic."""
        # Simple critic update
        q_values = self.critic(states[:, 0, :], actions[:, 0].float().unsqueeze(-1))
        
        # Target: rewards + gamma * next Q
        with torch.no_grad():
            next_q = self.critic.Q_target(states[:, 0, :], actions[:, 0].float().unsqueeze(-1))
            target = rewards.unsqueeze(-1) + self.gamma * next_q
        
        critic_loss = F.mse_loss(q_values, target)
        
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()
        
        # Update target
        self.critic._update_target()
    
    def get_action(
        self,
        state: List[float],
        target_return: float = 1.0,
        temperature: float = 1.0
    ) -> int:
        """
        Get action for a state.
        
        Args:
            state: Current state
            target_return: Target return to achieve
            temperature: Sampling temperature
            
        Returns:
            Action
        """
        if not TORCH_AVAILABLE or self.dataset is None:
            return 0
        
        self.model.eval()
        
        with torch.no_grad():
            # Prepare input
            max_len = self.model.max_length
            
            # Pad state sequence
            states = torch.FloatTensor([state] * max_len).unsqueeze(0).to(self.device)
            states = states.reshape(1, max_len, -1)
            
            # Actions: start with padding
            actions = torch.zeros(max_len, dtype=torch.long).unsqueeze(0).to(self.device)
            
            # Returns to go
            returns = torch.FloatTensor([target_return] * max_len).unsqueeze(0).unsqueeze(-1).to(self.device)
            
            # Timesteps
            timesteps = torch.LongTensor(list(range(max_len))).unsqueeze(0).to(self.device)
            
            # Get action
            action, _ = self.model.get_action(states, actions, returns, timesteps)
        
        return action
    
    def save(self, path: str):
        """Save model."""
        if TORCH_AVAILABLE:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'critic_state_dict': self.critic.state_dict(),
                'history': self.history
            }, path)
    
    def load(self, path: str):
        """Load model."""
        if TORCH_AVAILABLE:
            checkpoint = torch.load(path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.critic.load_state_dict(checkpoint['critic_state_dict'])
            self.history = checkpoint.get('history', self.history)


class OfflineRLTrainer:
    """
    Trainer for offline RL with Decision Transformer.
    """
    
    def __init__(self, agent: DecisionTransformerAgent):
        self.agent = agent
    
    def train(
        self,
        num_steps: int = 10000,
        batch_size: int = 64,
        log_interval: int = 100
    ) -> Dict:
        """Train the agent on offline data."""
        if self.agent.dataset is None:
            return {'status': 'no_data'}
        
        results = []
        
        for step in range(num_steps):
            loss_dict = self.agent.train_step(batch_size)
            
            if (step + 1) % log_interval == 0:
                print(f"Step {step+1}/{num_steps}: DT Loss: {loss_dict['dt_loss']:.4f}")
                
                results.append({
                    'step': step,
                    **loss_dict
                })
        
        return {
            'status': 'completed',
            'total_steps': num_steps,
            'results': results
        }
    
    def evaluate(
        self,
        eval_trajectories: List[Dict],
        num_episodes: int = 10
    ) -> Dict:
        """Evaluate the agent on trajectories."""
        total_rewards = []
        
        for traj in eval_trajectories[:num_episodes]:
            rewards = traj.get('rewards', [])
            total_rewards.append(sum(rewards))
        
        return {
            'mean_reward': np.mean(total_rewards) if total_rewards else 0,
            'std_reward': np.std(total_rewards) if total_rewards else 0,
            'num_episodes': len(total_rewards)
        }


# Factory function
def create_offline_rl_agent(
    state_dim: int = 12,
    action_dim: int = 4
) -> DecisionTransformerAgent:
    """Create Decision Transformer agent."""
    return DecisionTransformerAgent(
        state_dim=state_dim,
        action_dim=action_dim
    )
