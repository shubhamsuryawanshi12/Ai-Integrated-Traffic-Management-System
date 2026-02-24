"""
Trainer module for PCU-MARL++.

Main training orchestrator for multi-agent reinforcement learning.
"""

import os
import time
from typing import Dict, Optional, List
import numpy as np
import torch

from ..env import TrafficEnv
from ..agents import CentralizedMAPPO
from ..modules import PCUReward, IDSSModule, CATCModule, LAUERModule
from .logger import TrainingLogger, MetricsTracker
from .federated import FedAvg


# Default training configuration
TRAINING_CONFIG = {
    "n_junctions": 12,
    "n_episodes": 1000,
    "rollout_steps": 400,
    "n_epochs": 10,
    "batch_size": 64,
    "lr_actor": 3e-4,
    "lr_critic": 1e-3,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "clip_eps": 0.2,
    "entropy_coef": 0.01,
    "lyapunov_lambda": 0.1,
    "federated_rounds": 1,
    "weather_schedule": "random",
    "intent_dim": 64,
    "gat_heads": 4,
    "device": "cpu",
}


class MARLTrainer:
    """
    Multi-Agent RL Trainer for PCU-MARL++.
    
    Orchestrates training of all agents with:
    - PCU-aware reward
    - IDSS communication
    - CATC climate adaptation
    - LAUER event reasoning
    - Federated aggregation
    """
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        env: Optional[TrafficEnv] = None,
        checkpoint_dir: str = "checkpoints",
    ):
        """
        Initialize trainer.
        
        Args:
            config: Training configuration
            env: Traffic environment
            checkpoint_dir: Directory for checkpoints
        """
        # Configuration
        self.config = {**TRAINING_CONFIG}
        if config:
            self.config.update(config)
        
        # Device
        self.device = self.config["device"]
        
        # Environment
        if env is None:
            self.env = TrafficEnv(
                n_junctions=self.config["n_junctions"],
                weather_source=self.config.get("weather", "mock"),
            )
        else:
            self.env = env
        
        # Create agents
        self.mappo = CentralizedMAPPO(
            n_agents=self.config["n_junctions"],
            obs_dim=83,
            action_dim=4,
            actor_hidden=256,
            critic_hidden=128,
            lr_actor=self.config["lr_actor"],
            lr_critic=self.config["lr_critic"],
            gamma=self.config["gamma"],
            gae_lambda=self.config["gae_lambda"],
            clip_eps=self.config["clip_eps"],
            entropy_coef=self.config["entropy_coef"],
            lyapunov_lambda=self.config["lyapunov_lambda"],
            device=self.device,
        ).to(self.device)
        
        # Modules
        self.pcu_reward = PCUReward()
        self.idss = IDSSModule(
            n_junctions=self.config["n_junctions"],
            obs_dim=83,
            intent_dim=self.config["intent_dim"],
            n_heads=self.config["gat_heads"],
            road_network=self.env.road_network,
        )
        self.catc = CATCModule(obs_dim=83, action_dim=4)
        self.lauer = LAUERModule(
            n_junctions=self.config["n_junctions"],
            road_network=self.env.road_network,
        )
        
        # Federated averaging
        self.federated = FedAvg(n_agents=self.config["n_junctions"])
        
        # Logger
        self.logger = TrainingLogger(
            log_dir="logs",
            experiment_name=f"pcu_marl_{int(time.time())}",
        )
        self.logger.save_config(self.config)
        
        # Metrics tracker
        self.metrics_tracker = MetricsTracker(window_size=100)
        
        # Checkpoint directory
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Training state
        self.current_episode = 0
        self.global_step = 0
        self.best_reward = float('-inf')
    
    def train(self):
        """Run training loop."""
        n_episodes = self.config["n_episodes"]
        rollout_steps = self.config["rollout_steps"]
        
        print(f"Starting training for {n_episodes} episodes...")
        print(f"Device: {self.device}")
        
        for episode in range(n_episodes):
            self.current_episode = episode
            
            # Run episode
            episode_metrics = self._run_episode(rollout_steps)
            
            # Log metrics
            self.logger.log_episode_metrics(episode, episode_metrics)
            
            # Print progress
            if episode % 10 == 0:
                print(f"Episode {episode}/{n_episodes} - "
                      f"Reward: {episode_metrics.get('reward', 0):.2f}, "
                      f"Throughput: {episode_metrics.get('throughput', 0):.2f}")
            
            # Save checkpoint
            if episode % 100 == 0:
                self.save_checkpoint(f"checkpoint_ep{episode}.pt")
            
            # Track best
            reward = episode_metrics.get('reward', 0)
            if reward > self.best_reward:
                self.best_reward = reward
                self.save_checkpoint("best.pt")
        
        print("Training complete!")
        self.save_checkpoint("latest.pt")
    
    def _run_episode(self, max_steps: int) -> Dict:
        """
        Run a single episode.
        
        Args:
            max_steps: Maximum steps in episode
            
        Returns:
            Episode metrics
        """
        # Reset environment
        obs, info = self.env.reset()
        
        # Reset modules
        self.pcu_reward.reset()
        self.idss.update_intents(obs)
        self.lauer.update_events()
        
        # Get event context
        event_ctx = self.lauer.get_event_context()
        
        # Update observations with event context
        for jid in obs:
            obs[jid][71:83] = event_ctx
        
        # Get weather
        rain = self.env.weather.current_rain_intensity
        self.catc.set_rain(rain)
        
        # Track metrics
        total_reward = 0.0
        total_throughput = 0.0
        total_delay = 0.0
        step_count = 0
        
        # Initial global queue for Lyapunov
        prev_global_queue = sum(
            j.get_total_pcu() for j in self.env.junctions
        )
        
        for step in range(max_steps):
            self.global_step += 1
            step_count += 1
            
            # Select actions
            actions_dict = {}
            log_probs_dict = {}
            values_dict = {}
            
            for jid in range(self.config["n_junctions"]):
                action, log_prob, value = self.mappo.agents[jid].select_action(obs[jid])
                actions_dict[jid] = action
                log_probs_dict[jid] = log_prob
                values_dict[jid] = value
            
            # Step environment
            next_obs, rewards, dones, infos = self.env.step(actions_dict)
            
            # Update modules
            self.idss.update_intents(next_obs)
            self.lauer.update_events()
            event_ctx = self.lauer.get_event_context()
            
            # Add event context to observations
            for jid in next_obs:
                next_obs[jid][71:83] = event_ctx
            
            # Compute rewards with PCU reward module
            pcu_rewards = {}
            for jid in range(self.config["n_junctions"]):
                junction = self.env.junctions[jid]
                pcu_queue = junction.compute_pcu_queue()
                overflow = junction.compute_overflow()
                throughput = junction.get_throughput()
                
                reward = self.pcu_reward.compute(
                    pcu_queue=pcu_queue,
                    throughput=throughput,
                    overflow=overflow,
                    prev_phase=junction.prev_phase,
                    curr_phase=junction.current_phase,
                )
                
                pcu_rewards[jid] = reward
            
            # Store transitions
            for jid in range(self.config["n_junctions"]):
                self.mappo.store_transitions(
                    agent_id=jid,
                    obs=obs[jid],
                    action=actions_dict[jid],
                    reward=pcu_rewards[jid],
                    log_prob=log_probs_dict[jid],
                    value=values_dict[jid],
                    done=dones.get(jid, False),
                )
            
            # Update for Lyapunov
            global_queue = sum(j.get_total_pcu() for j in self.env.junctions)
            for jid in range(self.config["n_junctions"]):
                self.mappo.agents[jid].buffer.store_global_queue(global_queue)
            
            # Accumulate metrics
            for jid in range(self.config["n_junctions"]):
                total_reward += pcu_rewards[jid]
            
            total_throughput += sum(
                j.get_throughput() for j in self.env.junctions
            )
            
            # Move to next state
            obs = next_obs
        
        # Compute GAE and update
        final_values = [0.0] * self.config["n_junctions"]
        for agent in self.mappo.agents:
            agent.buffer.compute_gae(final_value=0.0)
        
        # Update agents
        losses = self.mappo.update_all(
            global_obs=np.zeros((1, 996)),
            n_epochs=self.config["n_epochs"],
            batch_size=self.config["batch_size"],
        )
        
        # Federated aggregation
        if self.current_episode % self.config["federated_rounds"] == 0:
            global_params = self.federated.aggregate(self.mappo.agents)
            self.federated.distribute(self.mappo.agents)
        
        # Reset buffers
        self.mappo.reset_all_buffers()
        
        # Get env metrics
        env_metrics = self.env.get_metrics()
        
        # Return metrics
        return {
            "reward": total_reward / max_steps,
            "throughput": total_throughput,
            "avg_delay": env_metrics.get("avg_delay", 0),
            "overflow_rate": env_metrics.get("overflow_rate", 0),
            "rain_intensity": self.env.weather.current_rain_intensity,
            "steps": step_count,
        }
    
    def save_checkpoint(self, filename: str):
        """Save training checkpoint."""
        checkpoint_path = os.path.join(self.checkpoint_dir, filename)
        
        checkpoint = {
            "episode": self.current_episode,
            "global_step": self.global_step,
            "config": self.config,
            "best_reward": self.best_reward,
            "agents": [
                agent.get_actor_params() 
                for agent in self.mappo.agents
            ],
        }
        
        torch.save(checkpoint, checkpoint_path)
        print(f"Checkpoint saved: {checkpoint_path}")
    
    def load_checkpoint(self, filepath: str):
        """Load training checkpoint."""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.current_episode = checkpoint["episode"]
        self.global_step = checkpoint["global_step"]
        self.best_reward = checkpoint.get("best_reward", float('-inf'))
        
        # Load agent params
        agent_params = checkpoint["agents"]
        for i, params in enumerate(agent_params):
            if i < len(self.mappo.agents):
                self.mappo.agents[i].load_actor_params(params)
        
        print(f"Checkpoint loaded: {filepath}")
    
    def evaluate(self, n_episodes: int = 10) -> Dict:
        """Evaluate trained agents."""
        eval_rewards = []
        
        for episode in range(n_episodes):
            obs, _ = self.env.reset()
            total_reward = 0
            
            for step in range(self.config["rollout_steps"]):
                # Deterministic actions
                actions_dict = {}
                for jid in range(self.config["n_junctions"]):
                    action, _, _ = self.mappo.agents[jid].select_action(
                        obs[jid], deterministic=True
                    )
                    actions_dict[jid] = action
                
                obs, rewards, dones, _ = self.env.step(actions_dict)
                
                for jid in range(self.config["n_junctions"]):
                    total_reward += rewards[jid]
            
            eval_rewards.append(total_reward)
        
        return {
            "mean_reward": np.mean(eval_rewards),
            "std_reward": np.std(eval_rewards),
        }
    
    def close(self):
        """Clean up resources."""
        self.env.close()
        self.logger.close()


def create_trainer(
    n_episodes: int = 1000,
    n_junctions: int = 12,
    device: str = "cpu",
    **kwargs,
) -> MARLTrainer:
    """
    Factory function to create trainer.
    
    Args:
        n_episodes: Number of episodes
        n_junctions: Number of junctions
        device: Device
        **kwargs: Additional config
        
    Returns:
        MARLTrainer instance
    """
    config = {
        "n_episodes": n_episodes,
        "n_junctions": n_junctions,
        "device": device,
        **kwargs,
    }
    
    return MARLTrainer(config=config)
