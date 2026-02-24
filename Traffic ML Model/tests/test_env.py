"""Tests for Traffic Environment."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from pcu_marl.env import TrafficEnv, Junction, Vehicle


def test_junction_creation():
    """Test junction initialization."""
    j = Junction(junction_id=0, capacity_per_approach=20.0)
    assert j.id == 0
    assert j.current_phase == 0
    assert j.phase_elapsed == 0.0


def test_junction_step():
    """Test junction step."""
    j = Junction(junction_id=0)
    
    # Add vehicles
    for i in range(5):
        v = Vehicle(
            id=f"veh_{i}",
            type="car",
            pcu=1.0,
            approach=0,
            position=50.0,
            speed=40.0,
        )
        j.add_vehicle(v)
    
    # Step junction
    obs, metrics = j.step(action=0, dt=5.0)
    
    assert "pcu_queue" in obs
    assert obs["pcu_queue"].shape == (4,)
    assert "phase" in obs
    assert obs["phase"] in [0, 1, 2, 3]


def test_traffic_env_reset():
    """Test environment reset."""
    env = TrafficEnv(n_junctions=12, seed=42)
    obs, info = env.reset()
    
    assert len(obs) == 12
    for jid in range(12):
        assert obs[jid].shape == (83,)


def test_traffic_env_step():
    """Test environment step."""
    env = TrafficEnv(n_junctions=12, seed=42)
    obs, info = env.reset()
    
    # Take step with random actions
    actions = {i: i % 4 for i in range(12)}
    next_obs, rewards, dones, infos = env.step(actions)
    
    assert len(next_obs) == 12
    assert len(rewards) == 12
    assert len(dones) == 12


def test_env_observation_shape():
    """Test observation shapes."""
    env = TrafficEnv(n_junctions=12, seed=42)
    obs, _ = env.reset()
    
    for jid, ob in obs.items():
        assert ob.shape == (83,), f"Expected shape (83,), got {ob.shape}"
        assert ob.dtype == np.float32


def test_env_action_space():
    """Test action space."""
    env = TrafficEnv()
    assert env.action_space.n == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
