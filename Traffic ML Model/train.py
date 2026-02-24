#!/usr/bin/env python
"""
Training script for PCU-MARL++.

Usage:
    python train.py --episodes 5 --junctions 12 --weather random
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pcu_marl.training import MARLTrainer
from pcu_marl.utils import create_config


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Train PCU-MARL++ agents')
    
    parser.add_argument(
        '--episodes', 
        type=int, 
        default=100,
        help='Number of training episodes'
    )
    
    parser.add_argument(
        '--junctions', 
        type=int, 
        default=12,
        help='Number of junctions'
    )
    
    parser.add_argument(
        '--weather',
        type=str,
        default='random',
        choices=['random', 'clear', 'monsoon'],
        help='Weather schedule'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        help='Device (cpu/cuda)'
    )
    
    parser.add_argument(
        '--checkpoint',
        type=str,
        default=None,
        help='Load checkpoint to resume training'
    )
    
    parser.add_argument(
        '--save-dir',
        type=str,
        default='checkpoints',
        help='Directory for checkpoints'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    
    return parser.parse_args()


def main():
    """Main training function."""
    args = parse_args()
    
    print("=" * 60)
    print("PCU-MARL++ Training")
    print("=" * 60)
    print(f"Episodes: {args.episodes}")
    print(f"Junctions: {args.junctions}")
    print(f"Weather: {args.weather}")
    print(f"Device: {args.device}")
    print(f"Seed: {args.seed}")
    print("=" * 60)
    
    # Create config
    config = {
        "n_junctions": args.junctions,
        "n_episodes": args.episodes,
        "weather": args.weather,
        "device": args.device,
        "seed": args.seed,
    }
    
    # Create trainer
    trainer = MARLTrainer(
        config=config,
        checkpoint_dir=args.save_dir,
    )
    
    # Load checkpoint if provided
    if args.checkpoint:
        print(f"Loading checkpoint: {args.checkpoint}")
        trainer.load_checkpoint(args.checkpoint)
    
    # Run training
    try:
        trainer.train()
    except KeyboardInterrupt:
        print("\nTraining interrupted!")
        trainer.save_checkpoint("interrupt.pt")
    finally:
        trainer.close()
    
    print("Training complete!")


if __name__ == '__main__':
    main()
