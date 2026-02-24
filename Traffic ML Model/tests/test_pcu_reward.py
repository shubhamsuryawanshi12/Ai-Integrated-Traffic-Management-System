"""Tests for PCU Reward Module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from pcu_marl.modules import PCUReward


def test_pcu_reward_creation():
    """Test PCU reward initialization."""
    reward = PCUReward()
    assert reward.alpha == 1.0
    assert reward.beta == 2.0
    assert reward.gamma == 0.5


def test_pcu_reward_compute():
    """Test reward computation."""
    reward = PCUReward()
    
    pcu_queue = np.array([5.0, 3.0, 4.0, 2.0])
    throughput = 10.0
    overflow = np.array([False, False, False, False])
    
    r = reward.compute(
        pcu_queue=pcu_queue,
        throughput=throughput,
        overflow=overflow,
        prev_phase=0,
        curr_phase=0,
    )
    
    # Should be negative (penalty) + positive (throughput bonus)
    assert isinstance(r, float)


def test_pcu_reward_overflow():
    """Test overflow penalty."""
    reward = PCUReward()
    
    pcu_queue = np.array([5.0, 3.0, 4.0, 2.0])
    throughput = 0.0
    
    # No overflow
    overflow = np.array([False, False, False, False])
    r1 = reward.compute(
        pcu_queue=pcu_queue,
        throughput=throughput,
        overflow=overflow,
        prev_phase=0,
        curr_phase=0,
    )
    
    # With overflow
    overflow = np.array([True, False, False, False])
    r2 = reward.compute(
        pcu_queue=pcu_queue,
        throughput=throughput,
        overflow=overflow,
        prev_phase=0,
        curr_phase=0,
    )
    
    # Overflow should give more negative reward
    assert r2 < r1


def test_lyapunov_term():
    """Test Lyapunov stability term."""
    reward = PCUReward(lyapunov_lambda=0.1)
    
    # First call
    l1 = reward.compute_lyapunov_term(current_global_queue=100.0)
    assert l1 == 0.0  # First call has no previous
    
    # Queue increased
    l2 = reward.compute_lyapunov_term(current_global_queue=150.0)
    assert l2 > 0  # Penalty for increase
    
    # Queue decreased
    l3 = reward.compute_lyapunov_term(current_global_queue=80.0)
    assert l3 == 0  # No penalty for decrease


def test_pcu_reward_weights():
    """Test reward weights."""
    reward = PCUReward(alpha=2.0, beta=3.0)
    weights = reward.get_weights()
    
    assert weights["alpha"] == 2.0
    assert weights["beta"] == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
