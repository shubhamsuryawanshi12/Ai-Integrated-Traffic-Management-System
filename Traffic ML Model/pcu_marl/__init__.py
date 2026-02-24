"""
PCU-MARL++ - PCU-Aware Multi-Agent Reinforcement Learning for Traffic Control.

A comprehensive traffic signal control system using multi-agent RL with:
- PCU-weighted reward functions
- Graph attention communication (IDSS)
- Climate-adaptive policy mixing (CATC)
- LLM-based event reasoning (LAUER)
"""

__version__ = "1.0.0"
__author__ = "PCU-MARL Team"

from .env import TrafficEnv, create_env
from .agents import MAPPOAgent, CentralizedMAPPO
from .modules import PCUReward, IDSSModule, CATCModule, LAUERModule
from .training import MARLTrainer, create_trainer
from .utils import get_default_config, create_config

__all__ = [
    # Environment
    "TrafficEnv",
    "create_env",
    # Agents
    "MAPPOAgent",
    "CentralizedMAPPO",
    # Modules
    "PCUReward",
    "IDSSModule",
    "CATCModule",
    "LAUERModule",
    # Training
    "MARLTrainer",
    "create_trainer",
    # Utils
    "get_default_config",
    "create_config",
]
