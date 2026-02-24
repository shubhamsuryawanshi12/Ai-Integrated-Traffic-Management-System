"""
Meta-Learning Module for UrbanFlow

Implements Model-Agnostic Meta-Learning (MAML) for rapid adaptation
to new intersections with minimal data.

Features:
- MAML algorithm for few-shot learning
- Task distribution for traffic intersections
- Online adaptation
- Transfer learning support
"""

from typing import Dict, List, Tuple, Optional, Any, Callable
import copy

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
    print("WARNING: PyTorch not available. Meta-learning will use dummy mode.")


class TaskDistribution:
    """Defines task distribution for meta-learning."""
    
    def __init__(self, num_intersections: int = 9):
        self.num_intersections = num_intersections
        
        # Task parameters for different intersection types
        self.task_params = {
            'small': {
                'queues': (0, 10),
                'vehicles': (0, 30),
                'phases': 4,
                'peak_factor': 1.0
            },
            'medium': {
                'queues': (5, 25),
                'vehicles': (20, 80),
                'phases': 4,
                'peak_factor': 1.5
            },
            'large': {
                'queues': (10, 50),
                'vehicles': (50, 150),
                'phases': 4,
                'peak_factor': 2.0
            }
        }
    
    def sample_task(self, task_type: str = 'random') -> Dict:
        """Sample a task from distribution."""
        if task_type == 'random':
            task_type = np.random.choice(list(self.task_params.keys()))
        
        params = self.task_params[task_type]
        
        return {
            'type': task_type,
            'queues': tuple(
                np.random.uniform(*params['queues'])
                for _ in range(self.num_intersections)
            ),
            'vehicles': tuple(
                np.random.uniform(*params['vehicles'])
                for _ in range(self.num_intersections)
            ),
            'peak_factor': params['peak_factor'],
            'hour': np.random.randint(0, 24)
        }
    
    def generate_task_batch(
        self,
        num_tasks: int,
        task_types: Dict[str, float] = None
    ) -> List[Dict]:
        """Generate batch of tasks."""
        if task_types is None:
            task_types = {'small': 0.4, 'medium': 0.4, 'large': 0.2}
        
        tasks = []
        types = list(task_types.keys())
        probs = list(task_types.values())
        
        for _ in range(num_tasks):
            task_type = np.random.choice(types, p=probs)
            tasks.append(self.sample_task(task_type))
        
        return tasks


class MAML(nn.Module):
    """
    Model-Agnostic Meta-Learning implementation.
    
    Learns a good initialization that can quickly adapt to new tasks.
    """
    
    def __init__(
        self,
        input_dim: int = 12,
        hidden_dim: int = 64,
        output_dim: int = 4,
        inner_lr: float = 0.01,
        outer_lr: float = 1e-3
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.inner_lr = inner_lr
        
        # Meta-learned network
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
        
        # Meta-optimizer
        self.meta_optimizer = optim.Adam(self.parameters(), lr=outer_lr)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.net(x)
    
    def inner_update(
        self,
        support_x: torch.Tensor,
        support_y: torch.Tensor,
        inner_steps: int = 5
    ) -> nn.Module:
        """
        Perform inner gradient steps on support set.
        
        Returns:
            Adapted model
        """
        # Create a copy for adaptation
        adapted_net = copy.deepcopy(self)
        adapted_net.train()
        
        # Use a simple optimizer for inner loop
        optimizer = optim.SGD(adapted_net.parameters(), lr=self.inner_lr)
        
        for _ in range(inner_steps):
            # Forward pass
            predictions = adapted_net(support_x)
            
            # Compute loss
            loss = F.cross_entropy(predictions, support_y)
            
            # Inner gradient update
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        return adapted_net
    
    def meta_loss(
        self,
        query_x: torch.Tensor,
        query_y: torch.Tensor,
        support_x: torch.Tensor,
        support_y: torch.Tensor,
        inner_steps: int = 5
    ) -> torch.Tensor:
        """
        Compute meta-loss on query set using adapted model.
        """
        # Adapt on support set
        adapted_net = self.inner_update(
            support_x, support_y, inner_steps
        )
        
        # Evaluate on query set
        query_preds = adapted_net(query_x)
        meta_loss = F.cross_entropy(query_preds, query_y)
        
        return meta_loss
    
    def forward_with_adaptation(
        self,
        x: torch.Tensor,
        adaptation_x: torch.Tensor,
        adaptation_y: torch.Tensor,
        inner_steps: int = 5
    ) -> Tuple[torch.Tensor, nn.Module]:
        """
        Forward pass with adaptation.
        
        Returns:
            (predictions, adapted_model)
        """
        adapted_net = self.inner_update(
            adaptation_x, adaptation_y, inner_steps
        )
        
        predictions = adapted_net(x)
        
        return predictions, adapted_net


class MetaLearner:
    """
    High-level meta-learning interface for traffic signal control.
    """
    
    def __init__(
        self,
        input_dim: int = 12,
        hidden_dim: int = 64,
        inner_lr: float = 0.01,
        outer_lr: float = 1e-3,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.device = device
        self.task_dist = TaskDistribution()
        
        # Initialize MAML
        if TORCH_AVAILABLE:
            self.maml = MAML(
                input_dim=input_dim,
                hidden_dim=hidden_dim,
                output_dim=4,  # 4 signal phases
                inner_lr=inner_lr,
                outer_lr=outer_lr
            ).to(device)
        else:
            self.maml = None
        
        # Training history
        self.history = {
            'meta_losses': [],
            'adaptation_losses': [],
            'tasks_seen': 0
        }
    
    def _prepare_task_data(
        self,
        task: Dict,
        num_support: int = 10,
        num_query: int = 10
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Prepare support and query sets for a task."""
        if not TORCH_AVAILABLE:
            return None, None, None, None
        
        # Generate samples
        n = num_support + num_query
        
        queues = list(task.get('queues', [10] * 9))[:9]
        vehicles = list(task.get('vehicles', [20] * 9))[:9]
        hour = task.get('hour', 12)
        
        # Feature vectors
        features = []
        labels = []
        
        for i in range(n):
            # Features: [queue, vehicles, hour_sin, hour_cos, ...]
            q = queues[i % len(queues)] if i < len(queues) else queues[-1]
            v = vehicles[i % len(vehicles)] if i < len(vehicles) else vehicles[-1]
            
            feat = [
                q / 50.0,
                v / 100.0,
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24),
                np.sin(2 * np.pi * i / n),
                np.cos(2 * np.pi * i / n),
                task.get('peak_factor', 1.0),
                0.0, 0.0, 0.0, 0.0, 0.0
            ][:self.maml.input_dim]
            
            # Label: optimal phase (simplified)
            label = 0 if q > v else 2
            
            features.append(feat)
            labels.append(label)
        
        features = torch.FloatTensor(features).to(self.device)
        labels = torch.LongTensor(labels).to(self.device)
        
        # Split into support and query
        support_x = features[:num_support]
        support_y = labels[:num_support]
        query_x = features[num_support:]
        query_y = labels[num_support:]
        
        return support_x, support_y, query_x, query_y
    
    def meta_train_step(
        self,
        num_tasks: int = 4,
        num_support: int = 10,
        num_query: int = 10,
        inner_steps: int = 5
    ) -> float:
        """
        Perform one meta-training step.
        
        Args:
            num_tasks: Number of tasks in batch
            num_support: Support set size per task
            num_query: Query set size per task
            inner_steps: Inner gradient steps
            
        Returns:
            Meta-loss
        """
        if not TORCH_AVAILABLE or self.maml is None:
            return 0.0
        
        # Sample tasks
        tasks = self.task_dist.generate_task_batch(num_tasks)
        
        meta_loss_sum = 0
        
        for task in tasks:
            # Prepare data
            support_x, support_y, query_x, query_y = self._prepare_task_data(
                task, num_support, num_query
            )
            
            # Compute meta-loss
            meta_loss = self.maml.meta_loss(
                query_x, query_y, support_x, support_y, inner_steps
            )
            
            meta_loss_sum += meta_loss.item()
        
        # Average meta-loss
        meta_loss = meta_loss_sum / num_tasks
        
        # Meta-update
        self.maml.meta_optimizer.zero_grad()
        meta_loss.backward()
        self.maml.meta_optimizer.step()
        
        self.history['meta_losses'].append(meta_loss)
        self.history['tasks_seen'] += num_tasks
        
        return meta_loss
    
    def adapt_to_intersection(
        self,
        intersection_data: List[Dict],
        adaptation_steps: int = 10
    ) -> bool:
        """
        Adapt meta-learned model to a specific intersection.
        
        Args:
            intersection_data: Historical data for intersection
            adaptation_steps: Number of gradient steps
            
        Returns:
            Success status
        """
        if not TORCH_AVAILABLE or self.maml is None:
            return False
        
        # Prepare adaptation data
        if len(intersection_data) < 5:
            return False
        
        # Extract features and labels
        features = []
        labels = []
        
        for data in intersection_data:
            feat = [
                data.get('queue', 0) / 50.0,
                data.get('vehicles', 0) / 100.0,
                np.sin(2 * np.pi * data.get('hour', 12) / 24),
                np.cos(2 * np.pi * data.get('hour', 12) / 24),
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            ][:self.maml.input_dim]
            
            label = data.get('optimal_phase', 0)
            
            features.append(feat)
            labels.append(label)
        
        support_x = torch.FloatTensor(features).to(self.device)
        support_y = torch.LongTensor(labels).to(self.device)
        
        # Perform inner updates
        adapted_net = self.maml.inner_update(
            support_x, support_y, adaptation_steps
        )
        
        return True
    
    def predict(
        self,
        state: Dict,
        adaptation_data: List[Dict] = None,
        adaptation_steps: int = 5
    ) -> Tuple[int, float]:
        """
        Make prediction using adapted model.
        
        Args:
            state: Current traffic state
            adaptation_data: Optional data for quick adaptation
            adaptation_steps: Adaptation steps
            
        Returns:
            (predicted_phase, confidence)
        """
        if not TORCH_AVAILABLE or self.maml is None:
            # Fall back to rule-based
            return self._rule_based_predict(state), 0.5
        
        # Prepare state features
        feat = [
            state.get('queue', 0) / 50.0,
            state.get('vehicles', 0) / 100.0,
            np.sin(2 * np.pi * state.get('hour', 12) / 24),
            np.cos(2 * np.pi * state.get('hour', 12) / 24),
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ][:self.maml.input_dim]
        
        state_tensor = torch.FloatTensor([feat]).to(self.device)
        
        # If adaptation data provided, adapt first
        if adaptation_data and len(adaptation_data) >= 3:
            # Prepare adaptation set
            adapt_features = []
            adapt_labels = []
            
            for data in adaptation_data[-5:]:
                adapt_features.append([
                    data.get('queue', 0) / 50.0,
                    data.get('vehicles', 0) / 100.0,
                    np.sin(2 * np.pi * data.get('hour', 12) / 24),
                    np.cos(2 * np.pi * data.get('hour', 12) / 24),
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                ][:self.maml.input_dim])
                adapt_labels.append(data.get('optimal_phase', 0))
            
            adapt_x = torch.FloatTensor([adapt_features]).to(self.device)
            adapt_y = torch.LongTensor([adapt_labels]).to(self.device)
            
            # Adapt
            with torch.no_grad():
                pred, adapted = self.maml.forward_with_adaptation(
                    state_tensor, adapt_x.squeeze(0), adapt_y.squeeze(0), adaptation_steps
                )
        else:
            # Use meta-learned model directly
            with torch.no_grad():
                pred = self.maml(state_tensor)
        
        # Get prediction
        probs = F.softmax(pred, dim=-1)
        action = torch.argmax(probs, dim=-1).item()
        confidence = probs[0, action].item()
        
        return action, confidence
    
    def _rule_based_predict(self, state: Dict) -> int:
        """Rule-based fallback prediction."""
        queue = state.get('queue', 0)
        vehicles = state.get('vehicles', 0)
        
        if queue > vehicles * 0.5:
            return 0  # Give green to congested direction
        else:
            return 2
    
    def save(self, path: str):
        """Save meta-learned model."""
        if TORCH_AVAILABLE and self.maml:
            torch.save(self.maml.state_dict(), path)
    
    def load(self, path: str):
        """Load meta-learned model."""
        if TORCH_AVAILABLE and self.maml:
            self.maml.load_state_dict(torch.load(path, map_location=self.device))


class FewShotAdapter:
    """
    Few-shot adapter for rapid intersection deployment.
    """
    
    def __init__(self, meta_learner: MetaLearner = None):
        self.meta_learner = meta_learner
        self.adapted_models: Dict[str, Any] = {}
    
    def deploy_to_intersection(
        self,
        intersection_id: str,
        initial_data: List[Dict],
        adaptation_steps: int = 10
    ) -> bool:
        """
        Deploy meta-learned model to new intersection.
        
        Args:
            intersection_id: Unique intersection identifier
            initial_data: Initial historical data
            adaptation_steps: Steps for adaptation
            
        Returns:
            Success
        """
        if self.meta_learner is None:
            return False
        
        # Adapt to intersection
        success = self.meta_learner.adapt_to_intersection(
            initial_data, adaptation_steps
        )
        
        if success:
            self.adapted_models[intersection_id] = {
                'deployed_at': datetime.now().isoformat(),
                'data_samples': len(initial_data),
                'adaptation_steps': adaptation_steps
            }
        
        return success
    
    def get_intersection_model(self, intersection_id: str) -> Optional[Any]:
        """Get adapted model for intersection."""
        return self.adapted_models.get(intersection_id)
    
    def list_deployments(self) -> List[Dict]:
        """List all deployed intersections."""
        return [
            {'intersection_id': k, **v}
            for k, v in self.adapted_models.items()
        ]


# Factory function
def create_meta_learner(
    input_dim: int = 12,
    hidden_dim: int = 64
) -> MetaLearner:
    """Create meta-learner."""
    return MetaLearner(input_dim=input_dim, hidden_dim=hidden_dim)
