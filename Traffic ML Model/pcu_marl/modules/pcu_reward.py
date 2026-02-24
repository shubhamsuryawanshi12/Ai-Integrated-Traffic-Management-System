"""
PCU-Aware Reward Module for PCU-MARL++.

Implements the innovation reward function that considers:
- PCU-weighted delay
- Overflow penalties
- Phase oscillation penalties  
- Throughput bonuses
- Coordination bonuses
- Lyapunov stability term
"""

from typing import List, Optional
import numpy as np
from scipy import signal as sp_signal


# Reward weights
ALPHA = 1.0   # PCU-weighted delay penalty
BETA = 2.0    # overflow penalty
GAMMA = 0.5   # phase oscillation penalty
DELTA = 0.8   # throughput bonus
EPSILON = 0.3 # coordination bonus

# Lyapunov stability weight
LAMBDA_STAB = 0.1


class PCUReward:
    """
    PCU-aware reward function for traffic signal control.
    
    Combines multiple factors:
    - W_pcu: PCU-weighted waiting time
    - O: Overflow indicator
    - Phi: Phase oscillation penalty
    - T: Throughput bonus
    - C: Coordination bonus
    """
    
    def __init__(
        self,
        alpha: float = ALPHA,
        beta: float = BETA,
        gamma: float = GAMMA,
        delta: float = DELTA,
        epsilon: float = EPSILON,
        lyapunov_lambda: float = LAMBDA_STAB,
    ):
        """
        Initialize PCU reward calculator.
        
        Args:
            alpha: Delay weight
            beta: Overflow weight
            gamma: Oscillation weight
            delta: Throughput weight
            epsilon: Coordination weight
            lyapunov_lambda: Lyapunov stability weight
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.epsilon = epsilon
        self.lyapunov_lambda = lyapunov_lambda
        
        # For Lyapunov term
        self.prev_global_queue = 0.0
    
    def compute(
        self,
        pcu_queue: np.ndarray,
        throughput: float,
        overflow: np.ndarray,
        prev_phase: int,
        curr_phase: int,
        neighbor_discharge_times: Optional[List[float]] = None,
        waiting_times: Optional[np.ndarray] = None,
    ) -> float:
        """
        Compute PCU-aware reward.
        
        Args:
            pcu_queue: PCU queue per approach (shape: (4,))
            throughput: PCU cleared this step
            overflow: Boolean overflow flags (shape: (4,))
            prev_phase: Previous phase
            curr_phase: Current phase
            neighbor_discharge_times: Neighbor junction discharge times for coordination
            waiting_times: Wait time per approach (shape: (4,))
            
        Returns:
            Reward value
        """
        # Default waiting times if not provided
        if waiting_times is None:
            waiting_times = np.ones(4) * 30.0  # Assume 30s average wait
        
        # PCU-weighted wait (delay)
        W_pcu = float(np.sum(pcu_queue * waiting_times))
        
        # Overflow penalty
        O = float(np.any(overflow))
        
        # Phase oscillation penalty (switching)
        Phi = float(curr_phase != prev_phase)
        
        # Throughput bonus
        T = throughput
        
        # Coordination bonus (cross-correlation with neighbors)
        C = 0.0
        if neighbor_discharge_times is not None and len(neighbor_discharge_times) > 0:
            C = self._compute_coordination_bonus(
                neighbor_discharge_times,
                throughput,
            )
        
        # Total reward
        reward = (
            -self.alpha * W_pcu
            -self.beta * O
            -self.gamma * Phi
            +self.delta * T
            +self.epsilon * C
        )
        
        return reward
    
    def _compute_coordination_bonus(
        self,
        neighbor_discharge_times: List[float],
        self_discharge: float,
    ) -> float:
        """
        Compute coordination bonus based on correlation with neighbors.
        
        Higher bonus when this junction's discharge is aligned with
        neighbors (green waves).
        
        Args:
            neighbor_discharge_times: List of neighbor junction discharges
            self_discharge: This junction's discharge
            
        Returns:
            Coordination bonus value
        """
        if not neighbor_discharge_times:
            return 0.0
        
        # Simple correlation: how similar is this discharge to neighbors
        neighbors = np.array(neighbor_discharge_times)
        
        # Normalized difference
        if np.mean(neighbors) > 0:
            diff = 1.0 - np.abs(self_discharge - np.mean(neighbors)) / (
                np.mean(neighbors) + 1.0
            )
            return max(0, diff)
        
        return 0.0
    
    def compute_lyapunov_term(
        self,
        current_global_queue: float,
    ) -> float:
        """
        Compute Lyapunov stability term.
        
        Encourages global queue reduction:
        L = max(0, Q(t) - Q(t-1))
        
        Args:
            current_global_queue: Total PCU in system
            
        Returns:
            Lyapunov penalty value
        """
        delta_queue = current_global_queue - self.prev_global_queue
        self.prev_global_queue = current_global_queue
        
        return self.lyapunov_lambda * max(0, delta_queue)
    
    def compute_batch(
        self,
        pcu_queues: np.ndarray,
        throughputs: np.ndarray,
        overflows: np.ndarray,
        prev_phases: np.ndarray,
        curr_phases: np.ndarray,
        neighbor_times: Optional[List[List[float]]] = None,
    ) -> np.ndarray:
        """
        Compute rewards for a batch of junctions.
        
        Args:
            pcu_queues: Shape (n_junctions, 4)
            throughputs: Shape (n_junctions,)
            overflows: Shape (n_junctions, 4)
            prev_phases: Shape (n_junctions,)
            curr_phases: Shape (n_junctions,)
            neighbor_times: Optional list of neighbor times
            
        Returns:
            Rewards array of shape (n_junctions,)
        """
        n_junctions = len(pcu_queues)
        rewards = np.zeros(n_junctions)
        
        for i in range(n_junctions):
            neighbors = None
            if neighbor_times is not None and i < len(neighbor_times):
                neighbors = neighbor_times[i]
            
            rewards[i] = self.compute(
                pcu_queue=pcu_queues[i],
                throughput=throughputs[i],
                overflow=overflows[i],
                prev_phase=prev_phases[i],
                curr_phase=curr_phases[i],
                neighbor_discharge_times=neighbors,
            )
        
        return rewards
    
    def reset(self):
        """Reset internal state."""
        self.prev_global_queue = 0.0
    
    def get_weights(self) -> dict:
        """Get current reward weights."""
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "delta": self.delta,
            "epsilon": self.epsilon,
            "lyapunov_lambda": self.lyapunov_lambda,
        }


def compute_pcu_delay(
    pcu_queue: np.ndarray,
    dt: float = 5.0,
) -> float:
    """
    Compute total delay in PCU-seconds.
    
    Args:
        pcu_queue: PCU queue per approach
        dt: Time step in seconds
        
    Returns:
        Total delay
    """
    # Assuming average speed of 20 km/h for queued vehicles
    avg_speed_kmh = 20.0
    avg_speed_ms = avg_speed_kmh * 1000 / 3600  # m/s
    
    delay = 0.0
    for q in pcu_queue:
        # Time to clear queue: distance / speed
        # Assuming average position of 50m from stop line
        avg_distance = 50.0
        travel_time = avg_distance / avg_speed_ms
        delay += q * travel_time
    
    return delay * dt


def compute_overflow_penalty(
    overflow: np.ndarray,
    beta: float = BETA,
) -> float:
    """
    Compute overflow penalty.
    
    Args:
        overflow: Boolean array of overflow flags
        beta: Penalty weight
        
    Returns:
        Penalty value
    """
    return -beta * np.any(overflow)


def compute_phase_penalty(
    prev_phase: int,
    curr_phase: int,
    gamma: float = GAMMA,
) -> float:
    """
    Compute phase oscillation penalty.
    
    Args:
        prev_phase: Previous phase
        curr_phase: Current phase  
        gamma: Penalty weight
        
    Returns:
        Penalty value
    """
    return -gamma * (curr_phase != prev_phase)


def compute_throughput_bonus(
    throughput: float,
    delta: float = DELTA,
) -> float:
    """
    Compute throughput bonus.
    
    Args:
        throughput: PCU cleared
        delta: Bonus weight
        
    Returns:
        Bonus value
    """
    return delta * throughput
