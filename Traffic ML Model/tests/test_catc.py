"""Tests for CATC Module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from pcu_marl.modules import CATCModule, mixing_weights


def test_mixing_weights_clear():
    """Test mixing weights at clear weather."""
    w1, w2, w3 = mixing_weights(0.0)
    
    # Should be mostly clear policy
    assert w1 > 0.8
    assert abs(w1 + w2 + w3 - 1.0) < 0.01


def test_mixing_weights_moderate():
    """Test mixing weights at moderate rain."""
    w1, w2, w3 = mixing_weights(0.45)
    
    # Sum should be 1
    assert abs(w1 + w2 + w3 - 1.0) < 0.01


def test_mixing_weights_heavy():
    """Test mixing weights at heavy rain."""
    w1, w2, w3 = mixing_weights(0.9)
    
    # Should be mostly heavy policy
    assert w3 > 0.8
    assert abs(w1 + w2 + w3 - 1.0) < 0.01


def test_catc_module():
    """Test CATC module."""
    catc = CATCModule(obs_dim=83, action_dim=4)
    
    # Set rain
    catc.set_rain(0.5)
    weights = catc.get_weights()
    
    assert abs(sum(weights) - 1.0) < 0.01


def test_catc_forward():
    """Test CATC forward pass."""
    catc = CATCModule(obs_dim=83, action_dim=4)
    catc.set_rain(0.0)
    
    obs = np.random.randn(1, 83).astype(np.float32)
    import torch
    obs_tensor = torch.from_numpy(obs)
    
    logits = catc.forward(obs_tensor)
    
    assert logits.shape == (1, 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
