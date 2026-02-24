"""Tests for LAUER Module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from pcu_marl.modules import LAUERModule
from pcu_marl.env import RoadNetwork


def test_lauer_creation():
    """Test LAUER module initialization."""
    lauer = LAUERModule(n_junctions=12, llm_backend="rule_based")
    
    assert lauer.n_junctions == 12
    assert lauer.llm_backend == "rule_based"


def test_lauer_rule_parser():
    """Test rule-based parser."""
    lauer = LAUERModule(n_junctions=12, llm_backend="rule_based")
    
    event_text = "Ganesh Chaturthi procession on Chord Road, 6 PM to 11 PM"
    parsed = lauer.parse_event(event_text)
    
    assert parsed.event_type == "festival"
    assert parsed.peak_demand_multiplier >= 1.0


def test_lauer_context_vector():
    """Test event context vector generation."""
    network = RoadNetwork()
    lauer = LAUERModule(n_junctions=12, road_network=network, llm_backend="rule_based")
    
    # Create mock event
    from pcu_marl.modules.lauer import ParsedEvent
    event = ParsedEvent(
        event_type="festival",
        start_time="18:00",
        end_time="23:00",
        affected_corridors=["Main Road 1"],
        peak_demand_multiplier=2.0,
        spatial_radius_km=1.5,
    )
    
    ctx = lauer.build_event_context_vector(event)
    
    assert ctx.shape == (12,)
    # All values should be >= 1.0
    assert np.all(ctx >= 1.0)
    # All values should be <= 3.0
    assert np.all(ctx <= 3.0)


def test_lauer_fetch_events():
    """Test event fetching."""
    lauer = LAUERModule(n_junctions=12)
    events = lauer.fetch_events()
    
    # Should return mock events
    assert isinstance(events, list)


def test_lauer_update_events():
    """Test event update."""
    network = RoadNetwork()
    lauer = LAUERModule(n_junctions=12, road_network=network)
    
    ctx = lauer.update_events()
    
    assert ctx.shape == (12,)
    assert np.all(ctx >= 1.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
