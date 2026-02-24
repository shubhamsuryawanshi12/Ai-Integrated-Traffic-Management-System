"""
PCU-MARL++ Integration for UrbanFlow.

PCU-Aware Multi-Agent Reinforcement Learning for Urban Traffic Control.

This module integrates the PCU-MARL++ model with UrbanFlow's traffic management system.
"""

from .config import PCUMARLConfig, get_default_config, create_config
from .pcu_reward import PCUReward, compute_pcu_delay, compute_pcu_queue, get_pcu, PCU_VALUES
from .mappo_agent import MAPPOAgent, CentralizedMAPPO, create_mappo, RolloutBuffer
from .actor_critic import ActorNetwork, CriticNetwork, LocalCriticNetwork
from .idss import IDSSModule, IDSSCoordinator
from .catc import CATCModule, mixing_weights, get_policy_capacity
from .traffic_environment import TrafficEnvironment, create_environment, PHASE_NAMES

__all__ = [
    # Config
    "PCUMARLConfig",
    "get_default_config",
    "create_config",
    # Reward
    "PCUReward",
    "compute_pcu_delay",
    "compute_pcu_queue",
    "get_pcu",
    "PCU_VALUES",
    # Agents
    "MAPPOAgent",
    "CentralizedMAPPO",
    "create_mappo",
    "RolloutBuffer",
    # Networks
    "ActorNetwork",
    "CriticNetwork",
    "LocalCriticNetwork",
    # Modules
    "IDSSModule",
    "IDSSCoordinator",
    "CATCModule",
    "mixing_weights",
    "get_policy_capacity",
    # Environment
    "TrafficEnvironment",
    "create_environment",
    "PHASE_NAMES",
]
