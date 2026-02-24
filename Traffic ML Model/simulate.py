#!/usr/bin/env python
"""
Evaluation and dashboard script for PCU-MARL++.

Usage:
    python simulate.py --checkpoint checkpoints/latest.pt --dashboard
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pcu_marl.env import TrafficEnv
from pcu_marl.agents import CentralizedMAPPO
import torch
import numpy as np


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Run PCU-MARL++ simulation')
    
    parser.add_argument(
        '--checkpoint',
        type=str,
        default=None,
        help='Checkpoint to load'
    )
    
    parser.add_argument(
        '--episodes',
        type=int,
        default=10,
        help='Number of evaluation episodes'
    )
    
    parser.add_argument(
        '--steps',
        type=int,
        default=400,
        help='Steps per episode'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        help='Device (cpu/cuda)'
    )
    
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Start dashboard server'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Dashboard port'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    
    return parser.parse_args()


def evaluate(env, agents, n_episodes=10, max_steps=400):
    """Run evaluation."""
    print("=" * 60)
    print("PCU-MARL++ Evaluation")
    print("=" * 60)
    
    all_rewards = []
    
    for episode in range(n_episodes):
        obs, _ = env.reset()
        total_reward = 0
        
        for step in range(max_steps):
            # Select actions (deterministic)
            actions = {}
            for jid in range(12):
                action, _, _ = agents.agents[jid].select_action(
                    obs[jid], deterministic=True
                )
                actions[jid] = action
            
            obs, rewards, dones, _ = env.step(actions)
            
            for jid in range(12):
                total_reward += rewards[jid]
        
        avg_reward = total_reward / max_steps
        all_rewards.append(avg_reward)
        print(f"Episode {episode + 1}: Avg Reward = {avg_reward:.2f}")
    
    print("=" * 60)
    print(f"Mean Reward: {np.mean(all_rewards):.2f} ± {np.std(all_rewards):.2f}")
    print("=" * 60)
    
    return all_rewards


def run_dashboard():
    """Run the dashboard server."""
    from dashboard.app import run_dashboard
    import threading
    
    # Start dashboard in background
    thread = threading.Thread(
        target=run_dashboard,
        kwargs={'host': '0.0.0.0', 'port': args.port},
        daemon=True
    )
    thread.start()
    
    print(f"Dashboard running at http://localhost:{args.port}")
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDashboard stopped")


def main():
    """Main function."""
    global args
    
    args = parse_args()
    
    print("=" * 60)
    print("PCU-MARL++ Simulation")
    print("=" * 60)
    
    # Create environment
    env = TrafficEnv(n_junctions=12, seed=args.seed)
    
    # Create agents
    agents = CentralizedMAPPO(n_agents=12, device=args.device)
    
    # Load checkpoint if provided
    if args.checkpoint:
        print(f"Loading checkpoint: {args.checkpoint}")
        checkpoint = torch.load(args.checkpoint, map_location=args.device)
        
        if 'agents' in checkpoint:
            for i, agent_params in enumerate(checkpoint['agents']):
                if i < len(agents.agents):
                    agents.agents[i].load_actor_params(agent_params)
    
    # Start dashboard if requested
    if args.dashboard:
        print("Starting dashboard...")
        run_dashboard()
    
    # Run evaluation
    evaluate(env, agents, args.episodes, args.steps)
    
    print("Simulation complete!")


if __name__ == '__main__':
    main()
