"""
Configuration module for PCU-MARL++.

Centralized hyperparameters using dataclasses.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json


@dataclass
class EnvConfig:
    """Environment configuration."""
    n_junctions: int = 12
    n_rows: int = 3
    n_cols: int = 4
    capacity_per_junction: float = 20.0
    arrival_rate: float = 400
    weather_source: str = "mock"
    dt: float = 5.0
    max_steps: int = 1000
    seed: Optional[int] = None


@dataclass
class AgentConfig:
    """Agent configuration."""
    obs_dim: int = 83
    action_dim: int = 4
    actor_hidden: int = 256
    critic_hidden: int = 128
    lr_actor: float = 3e-4
    lr_critic: float = 1e-3
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_eps: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    lyapunov_lambda: float = 0.1
    max_grad_norm: float = 0.5


@dataclass
class IDSSConfig:
    """IDSS module configuration."""
    intent_dim: int = 64
    gat_heads: int = 4
    comm_radius: float = 800.0


@dataclass
class CATCConfig:
    """CATC module configuration."""
    capacity_clear: float = 1.0
    capacity_moderate: float = 0.8
    capacity_heavy: float = 0.6


@dataclass
class RewardConfig:
    """Reward function configuration."""
    alpha: float = 1.0   # delay weight
    beta: float = 2.0    # overflow weight
    gamma: float = 0.5   # oscillation weight
    delta: float = 0.8   # throughput weight
    epsilon: float = 0.3  # coordination weight
    lyapunov_lambda: float = 0.1


@dataclass
class TrainingConfig:
    """Training configuration."""
    n_episodes: int = 1000
    rollout_steps: int = 400
    n_epochs: int = 10
    batch_size: int = 64
    federated_rounds: int = 1
    save_frequency: int = 100
    eval_frequency: int = 10
    device: str = "cpu"


@dataclass
class LAUERConfig:
    """LAUER module configuration."""
    llm_backend: str = "rule_based"
    poll_interval: int = 1800  # 30 minutes


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 5000
    refresh_rate: float = 5.0  # seconds


@dataclass
class PCUMARLConfig:
    """Complete PCU-MARL++ configuration."""
    env: EnvConfig = field(default_factory=EnvConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    idss: IDSSConfig = field(default_factory=IDSSConfig)
    catc: CATCConfig = field(default_factory=CATCConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    lauer: LAUERConfig = field(default_factory=LAUERConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "env": self.env.__dict__,
            "agent": self.agent.__dict__,
            "idss": self.idss.__dict__,
            "catc": self.catc.__dict__,
            "reward": self.reward.__dict__,
            "training": self.training.__dict__,
            "lauer": self.lauer.__dict__,
            "dashboard": self.dashboard.__dict__,
        }
    
    def save(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> "PCUMARLConfig":
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        config = cls()
        config.env = EnvConfig(**data.get("env", {}))
        config.agent = AgentConfig(**data.get("agent", {}))
        config.idss = IDSSConfig(**data.get("idss", {}))
        config.catc = CATCConfig(**data.get("catc", {}))
        config.reward = RewardConfig(**data.get("reward", {}))
        config.training = TrainingConfig(**data.get("training", {}))
        config.lauer = LAUERConfig(**data.get("lauer", {}))
        config.dashboard = DashboardConfig(**data.get("dashboard", {}))
        
        return config


# Default configuration
DEFAULT_CONFIG = PCUMARLConfig()


def get_default_config() -> PCUMARLConfig:
    """Get default configuration."""
    return PCUMARLConfig()


def create_config(
    n_junctions: int = 12,
    n_episodes: int = 1000,
    device: str = "cpu",
    weather: str = "mock",
    **kwargs,
) -> PCUMARLConfig:
    """
    Create custom configuration.
    
    Args:
        n_junctions: Number of junctions
        n_episodes: Number of training episodes
        device: Device (cpu/cuda)
        weather: Weather source
        **kwargs: Additional overrides
        
    Returns:
        PCUMARLConfig instance
    """
    config = PCUMARLConfig()
    config.env.n_junctions = n_junctions
    config.training.n_episodes = n_episodes
    config.training.device = device
    config.env.weather_source = weather
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config
