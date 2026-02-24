"""Tests for IDSS Module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
import torch
from pcu_marl.modules import IDSSModule
from pcu_marl.env import RoadNetwork


def test_idss_creation():
    """Test IDSS module initialization."""
    network = RoadNetwork()
    idss = IDSSModule(n_junctions=12, obs_dim=83, road_network=network)
    
    assert idss.n_junctions == 12
    assert idss.intent_dim == 64


def test_intent_encoding():
    """Test intent encoding."""
    network = RoadNetwork()
    idss = IDSSModule(n_junctions=12, obs_dim=83, road_network=network)
    
    obs = np.random.randn(83).astype(np.float32)
    intent = idss.get_intent(obs)
    
    assert intent.shape == (64,)


def test_idss_update_intents():
    """Test intent update."""
    network = RoadNetwork()
    idss = IDSSModule(n_junctions=12, obs_dim=83, road_network=network)
    
    observations = {i: np.random.randn(83).astype(np.float32) for i in range(12)}
    messages = idss.update_intents(observations)
    
    assert len(messages) == 12
    for jid, msg in messages.items():
        assert msg.shape == (64,)


def test_gat_communication():
    """Test GAT communication."""
    network = RoadNetwork()
    idss = IDSSModule(n_junctions=12, obs_dim=83, road_network=network)
    
    # Test with single observation
    obs = np.random.randn(12, 83).astype(np.float32)
    messages = idss.update_intents({i: obs[i] for i in range(12)})
    
    # Verify all messages are computed
    assert all(isinstance(m, np.ndarray) for m in messages.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
