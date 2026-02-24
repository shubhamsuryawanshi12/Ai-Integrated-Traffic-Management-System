"""
Imitation Learning Module for UrbanFlow

Implements behavior cloning and DAgger (Dataset Aggregation) for learning
from expert traffic controllers.

Supports:
- Behavior Cloning
- DAgger (Dataset Aggregation)
- Expert demonstrations collection
- Policy refinement through interaction
"""

from typing import Dict, List, Tuple, Optional, Any
import json
import os
from datetime import datetime
from collections import deque

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
    print("WARNING: PyTorch not available. Imitation Learning will use dummy mode.")


class ExpertPolicy:
    """
    Expert policy that provides demonstrations.
    Can be a fixed-time controller, rule-based system, or human operator.
    """
    
    # Fixed-time signal timings (seconds)
    PHASE_DURATIONS = {
        0: 30,  # NS Green
        1: 5,   # NS Yellow
        2: 30,  # EW Green
        3: 5,   # EW Yellow
    }
    
    @staticmethod
    def get_action(state: Dict) -> int:
        """
        Get expert action for given state.
        
        Uses fixed-time controller logic:
        - Monitors queue lengths
        - Extends green phase if queue is building
        - Switches phase when thresholds are met
        
        Args:
            state: Traffic state dictionary
            
        Returns:
            Action (phase): 0=NS_Green, 1=NS_Yellow, 2=EW_Green, 3=EW_Yellow
        """
        current_phase = state.get('current_phase', 0)
        ns_queue = state.get('ns_queue', 0)
        ew_queue = state.get('ew_queue', 0)
        phase_time = state.get('phase_time', 0)
        
        min_green = 15
        max_green = 60
        yellow_time = 5
        
        # Get minimum duration for current phase
        if current_phase in [0, 2]:  # Green phases
            min_duration = min_green
            max_duration = max_green
            
            # Check if we should switch
            if phase_time >= min_duration:
                # Compare queues
                other_queue = ns_queue if current_phase == 2 else ew_queue
                current_queue = ns_queue if current_phase == 0 else ew_queue
                
                # Switch if other direction has significantly more vehicles
                # or if current direction is empty
                if (other_queue > current_queue * 1.5 and phase_time >= min_duration + 10) or \
                   (current_queue == 0 and phase_time >= min_duration):
                    # Switch to next phase
                    return (current_phase + 1) % 4
                
                # Switch if max duration reached
                if phase_time >= max_duration:
                    return (current_phase + 1) % 4
        
        return current_phase
    
    @staticmethod
    def generate_demonstration(
        states: List[Dict],
        actions: List[int]
    ) -> List[Dict]:
        """Generate demonstration dataset from states and actions."""
        demonstrations = []
        for state, action in zip(states, actions):
            demonstrations.append({
                'state': state,
                'action': action,
                'timestamp': datetime.now().isoformat()
            })
        return demonstrations


class BehaviorCloning(nn.Module):
    """Behavior cloning policy network."""
    
    def __init__(
        self,
        state_dim: int = 15,
        action_dim: int = 4,
        hidden_dim: int = 256
    ):
        super().__init__()
        
        # Policy network
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returns action logits."""
        return self.net(x)
    
    def get_action(self, state: torch.Tensor) -> Tuple[int, torch.Tensor]:
        """
        Get action from state.
        
        Returns:
            (action, log_prob)
        """
        logits = self.forward(state)
        probs = F.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action.item(), log_prob


class ImitationLearner:
    """
    Main imitation learning class implementing Behavior Cloning and DAgger.
    """
    
    def __init__(
        self,
        state_dim: int = 15,
        action_dim: int = 4,
        learning_rate: float = 3e-4,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.device = device
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Policy network
        if TORCH_AVAILABLE:
            self.policy = BehaviorCloning(state_dim, action_dim).to(device)
            self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)
            self.criterion = nn.CrossEntropyLoss()
        else:
            self.policy = None
        
        # Demonstration buffer
        self.demonstrations: deque = deque(maxlen=10000)
        
        # Training history
        self.history = {
            'loss': [],
            'accuracy': [],
            'dagger_iterations': 0
        }
    
    def add_demonstration(self, state: Dict, action: int):
        """Add expert demonstration to buffer."""
        self.demonstrations.append({
            'state': state,
            'action': action
        })
    
    def add_demonstrations(self, demonstrations: List[Dict]):
        """Add multiple demonstrations."""
        for demo in demonstrations:
            self.add_demonstration(demo['state'], demo['action'])
    
    def _prepare_batch(self, batch: List[Dict]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Prepare batch for training."""
        if not TORCH_AVAILABLE:
            return None, None
            
        states = []
        actions = []
        
        for demo in batch:
            # Extract features from state
            state_vec = self._state_to_vector(demo['state'])
            states.append(state_vec)
            actions.append(demo['action'])
        
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        
        return states, actions
    
    def _state_to_vector(self, state: Dict) -> List[float]:
        """Convert state dict to feature vector."""
        features = []
        
        # Queue lengths
        features.append(state.get('ns_queue', 0) / 50.0)
        features.append(state.get('ew_queue', 0) / 50.0)
        
        # Vehicle counts
        features.append(state.get('ns_vehicles', 0) / 100.0)
        features.append(state.get('ew_vehicles', 0) / 100.0)
        
        # Wait times
        features.append(state.get('ns_wait_time', 0) / 60.0)
        features.append(state.get('ew_wait_time', 0) / 60.0)
        
        # Throughput
        features.append(state.get('ns_throughput', 0) / 50.0)
        features.append(state.get('ew_throughput', 0) / 50.0)
        
        # Time features
        hour = state.get('hour', 12)
        features.append(hour / 24.0)
        
        # Phase info
        features.append(state.get('current_phase', 0) / 3.0)
        features.append(state.get('phase_time', 0) / 60.0)
        
        # Pedestrians
        features.append(state.get('ns_pedestrians', 0) / 20.0)
        features.append(state.get('ew_pedestrians', 0) / 20.0)
        
        # Emergency
        features.append(state.get('emergency_present', 0))
        
        # Pad if needed
        while len(features) < self.state_dim:
            features.append(0.0)
        
        return features[:self.state_dim]
    
    def train_step(self, batch_size: int = 32) -> float:
        """Single training step on batch of demonstrations."""
        if not TORCH_AVAILABLE or len(self.demonstrations) < batch_size:
            return 0.0
        
        # Sample batch
        batch = random.sample(list(self.demonstrations), min(batch_size, len(self.demonstrations)))
        states, actions = self._prepare_batch(batch)
        
        # Forward pass
        self.optimizer.zero_grad()
        logits = self.policy(states)
        loss = self.criterion(logits, actions)
        
        # Backward pass
        loss.backward()
        self.optimizer.step()
        
        # Calculate accuracy
        with torch.no_grad():
            preds = torch.argmax(logits, dim=-1)
            accuracy = (preds == actions).float().mean().item()
        
        self.history['loss'].append(loss.item())
        self.history['accuracy'].append(accuracy)
        
        return loss.item()
    
    def train(
        self,
        epochs: int = 100,
        batch_size: int = 32,
        verbose: bool = True
    ) -> Dict:
        """Train policy on demonstrations."""
        if len(self.demonstrations) == 0:
            return {'status': 'no_demonstrations', 'message': 'Add demonstrations before training'}
        
        if not TORCH_AVAILABLE:
            return {'status': 'dummy_mode', 'message': 'Training simulated (PyTorch not available)'}
        
        losses = []
        accuracies = []
        
        for epoch in range(epochs):
            epoch_loss = 0
            epoch_acc = 0
            num_batches = 0
            
            # Shuffle demonstrations
            demo_list = list(self.demonstrations)
            random.shuffle(demo_list)
            
            for i in range(0, len(demo_list), batch_size):
                batch = demo_list[i:i+batch_size]
                if len(batch) < batch_size // 2:
                    continue
                    
                loss = self.train_step(batch_size)
                epoch_loss += loss
                epoch_acc += self.history['accuracy'][-1] if self.history['accuracy'] else 0
                num_batches += 1
            
            if num_batches > 0:
                losses.append(epoch_loss / num_batches)
                accuracies.append(epoch_acc / num_batches)
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {losses[-1]:.4f}, Acc: {accuracies[-1]:.4f}")
        
        return {
            'status': 'trained',
            'final_loss': losses[-1] if losses else 0,
            'final_accuracy': accuracies[-1] if accuracies else 0,
            'num_demonstrations': len(self.demonstrations)
        }
    
    def get_action(self, state: Dict) -> Tuple[int, float]:
        """
        Get action from learned policy.
        
        Returns:
            (action, confidence)
        """
        if not TORCH_AVAILABLE or self.policy is None:
            # Fall back to expert
            return ExpertPolicy.get_action(state), 0.5
        
        with torch.no_grad():
            state_vec = self._state_to_vector(state)
            state_tensor = torch.FloatTensor([state_vec]).to(self.device)
            
            logits = self.policy(state_tensor)
            probs = F.softmax(logits, dim=-1)
            
            action = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, action].item()
        
        return action, confidence
    
    def dagger_iteration(
        self,
        env,
        num_rollouts: int = 10,
        batch_size: int = 32
    ) -> float:
        """
        Perform DAgger iteration.
        
        Collects rollouts with current policy, asks expert for corrections,
        and adds to demonstration buffer.
        
        Args:
            env: Environment to interact with
            num_rollouts: Number of rollouts to collect
            
        Returns:
            Average return of rollouts
        """
        if not TORCH_AVAILABLE:
            return 0.0
        
        total_return = 0
        
        for _ in range(num_rollouts):
            state = env.reset()
            done = False
            episode_return = 0
            steps = 0
            max_steps = 100
            
            while not done and steps < max_steps:
                # Get action from learned policy
                action, _ = self.get_action(state)
                
                # Get expert action
                expert_action = ExpertPolicy.get_action(state)
                
                # Add expert action to demonstrations (DAgger key insight)
                self.add_demonstration(state, expert_action)
                
                # Step environment
                next_state, reward, done, _ = env.step(action)
                
                episode_return += reward
                state = next_state
                steps += 1
            
            total_return += episode_return
        
        avg_return = total_return / num_rollouts
        
        # Train on updated demonstrations
        self.train(batch_size=batch_size, verbose=False)
        
        self.history['dagger_iterations'] += 1
        
        return avg_return
    
    def save(self, path: str):
        """Save policy."""
        if TORCH_AVAILABLE and self.policy:
            torch.save({
                'policy_state_dict': self.policy.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'history': self.history
            }, path)
    
    def load(self, path: str):
        """Load policy."""
        if TORCH_AVAILABLE and os.path.exists(path):
            checkpoint = torch.load(path, map_location=self.device)
            self.policy.load_state_dict(checkpoint['policy_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.history = checkpoint.get('history', self.history)


class DemonstrationCollector:
    """Collects expert demonstrations for imitation learning."""
    
    def __init__(self, save_path: str = "demonstrations"):
        self.save_path = save_path
        self.demonstrations: List[Dict] = []
        os.makedirs(save_path, exist_ok=True)
    
    def collect_from_expert(self, states: List[Dict]) -> List[Dict]:
        """Collect expert actions for given states."""
        demonstrations = []
        
        for state in states:
            expert_action = ExpertPolicy.get_action(state)
            demonstrations.append({
                'state': state,
                'action': expert_action,
                'timestamp': datetime.now().isoformat()
            })
        
        self.demonstrations.extend(demonstrations)
        return demonstrations
    
    def collect_from_rollout(
        self,
        env,
        num_rollouts: int = 100,
        policy=None
    ) -> List[Dict]:
        """
        Collect demonstrations via environmental rollouts.
        
        Args:
            env: Environment
            num_rollouts: Number of episodes
            policy: Optional policy (uses expert if None)
            
        Returns:
            List of demonstrations
        """
        demonstrations = []
        
        for _ in range(num_rollouts):
            state = env.reset()
            done = False
            steps = 0
            max_steps = 100
            
            while not done and steps < max_steps:
                # Use expert or policy
                if policy:
                    action, _ = policy.get_action(state)
                else:
                    action = ExpertPolicy.get_action(state)
                
                # Record demonstration
                demonstrations.append({
                    'state': state.copy(),
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Step
                next_state, _, done, _ = env.step(action)
                state = next_state
                steps += 1
        
        self.demonstrations.extend(demonstrations)
        return demonstrations
    
    def save_demonstrations(self, filename: str = None):
        """Save collected demonstrations to file."""
        if filename is None:
            filename = f"demonstrations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        path = os.path.join(self.save_path, filename)
        
        with open(path, 'w') as f:
            json.dump(self.demonstrations, f, indent=2)
        
        return path
    
    def load_demonstrations(self, filename: str):
        """Load demonstrations from file."""
        path = os.path.join(self.save_path, filename)
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.demonstrations = json.load(f)
        
        return self.demonstrations
    
    def generate_synthetic_demonstrations(
        self,
        num_samples: int = 1000
    ) -> List[Dict]:
        """Generate synthetic demonstrations for training."""
        import random
        
        demonstrations = []
        
        for _ in range(num_samples):
            # Random state
            state = {
                'ns_queue': random.randint(0, 30),
                'ew_queue': random.randint(0, 30),
                'ns_vehicles': random.randint(0, 50),
                'ew_vehicles': random.randint(0, 50),
                'ns_wait_time': random.uniform(0, 60),
                'ew_wait_time': random.uniform(0, 60),
                'ns_throughput': random.randint(0, 30),
                'ew_throughput': random.randint(0, 30),
                'hour': random.randint(0, 23),
                'current_phase': random.randint(0, 3),
                'phase_time': random.randint(0, 60),
                'ns_pedestrians': random.randint(0, 10),
                'ew_pedestrians': random.randint(0, 10),
                'emergency_present': random.choice([0, 0, 0, 1])
            }
            
            action = ExpertPolicy.get_action(state)
            
            demonstrations.append({
                'state': state,
                'action': action,
                'timestamp': datetime.now().isoformat()
            })
        
        self.demonstrations.extend(demonstrations)
        return demonstrations
