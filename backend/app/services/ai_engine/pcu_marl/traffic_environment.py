"""
Traffic Environment for PCU-MARL++.

Implements a Gym-style environment for traffic signal control
with PCU-weighted queuing and weather adaptation.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import random

try:
    import gymnasium as gym
    GYM_AVAILABLE = True
except ImportError:
    try:
        import gym
        GYM_AVAILABLE = True
    except ImportError:
        GYM_AVAILABLE = False
        print("WARNING: Gym not available. Using simple environment wrapper.")

from .pcu_reward import PCUReward, compute_pcu_queue, get_pcu
from .catc import CATCModule, mixing_weights
from .idss import IDSSCoordinator


# Action definitions (traffic signal phases)
# 0: NS Green, 1: NS Yellow, 2: EW Green, 3: EW Yellow
PHASE_NAMES = {
    0: "NS_GREEN",
    1: "NS_YELLOW", 
    2: "EW_GREEN",
    3: "EW_YELLOW",
}

# Minimum green time (seconds)
MIN_GREEN_TIME = 15
MAX_GREEN_TIME = 60
YELLOW_TIME = 5


class TrafficEnvironment:
    """
    Traffic signal control environment.
    
    Implements a multi-intersection traffic simulation with:
    - PCU-weighted vehicle queues
    - Weather-adaptive capacity
    - Inter-junction communication (IDSS)
    - Climate-adaptive policies (CATC)
    """
    
    def __init__(
        self,
        n_junctions: int = 12,
        n_rows: int = 3,
        n_cols: int = 4,
        dt: float = 5.0,
        capacity_per_junction: float = 20.0,
        arrival_rate: float = 400,
        weather_source: str = "mock",
        seed: Optional[int] = None,
    ):
        """
        Initialize traffic environment.
        
        Args:
            n_junctions: Number of junctions
            n_rows: Number of rows in grid
            n_cols: Number of columns in grid
            dt: Time step in seconds
            capacity_per_junction: Max PCU capacity per junction
            arrival_rate: Vehicle arrival rate (vehicles per hour)
            weather_source: "mock" or path to weather data
            seed: Random seed
        """
        self.n_junctions = n_junctions
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.dt = dt
        self.capacity_per_junction = capacity_per_junction
        self.arrival_rate = arrival_rate
        self.weather_source = weather_source
        self.seed = seed
        
        # Initialize random seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # State variables
        self.current_step = 0
        self.max_steps = 1000
        
        # Junction states
        # For each junction: [phase, elapsed_time, queue_NS, queue_EW, throughput]
        self.junction_states = np.zeros((n_junctions, 5))
        self.phases = np.zeros(n_junctions, dtype=int)  # Current phase
        self.elapsed_time = np.zeros(n_junctions)  # Time in current phase
        
        # Vehicle queues (in PCU)
        self.queues = {
            i: {
                "NS": 0.0,  # North-South queue
                "EW": 0.0,  # East-West queue
            }
            for i in range(n_junctions)
        }
        
        # Historical data
        self.total_throughput = np.zeros(n_junctions)
        self.total_delay = np.zeros(n_junctions)
        self.episode_rewards = []
        
        # Weather
        self.rain_intensity = 0.0
        self.capacity_factor = 1.0
        
        # Initialize modules
        self.reward_calculator = PCUReward()
        self.catc = CATCModule()
        self.idss = IDSSCoordinator(n_junctions=n_junctions)
        
        # Observation dimension: 83
        # - queue (4): PCU queues per approach
        # - phase (1): current phase
        # - elapsed (1): time in current phase  
        # - rain (1): rain intensity
        # - intent (64): IDSS communication intent
        # - event (12): event features
        self.obs_dim = 83
    
    def reset(self, seed: Optional[int] = None) -> Dict[int, np.ndarray]:
        """
        Reset environment to initial state.
        
        Args:
            seed: Random seed
            
        Returns:
            Initial observations for all junctions
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.current_step = 0
        self.junction_states = np.zeros((self.n_junctions, 5))
        self.phases = np.random.randint(0, 4, self.n_junctions).astype(int)
        self.elapsed_time = np.zeros(self.n_junctions)
        
        # Reset queues
        self.queues = {
            i: {"NS": random.uniform(0, 10), "EW": random.uniform(0, 10)}
            for i in range(self.n_junctions)
        }
        
        self.total_throughput = np.zeros(self.n_junctions)
        self.total_delay = np.zeros(self.n_junctions)
        self.episode_rewards = []
        
        # Reset weather
        self.rain_intensity = 0.0
        self.capacity_factor = 1.0
        self.catc.set_rain(0.0)
        
        # Reset modules
        self.reward_calculator.reset()
        self.idss.reset()
        
        return self._get_observations()
    
    def step(
        self,
        actions: Dict[int, int],
    ) -> Tuple[Dict[int, np.ndarray], Dict[int, float], Dict[int, bool], Dict]:
        """
        Execute one time step.
        
        Args:
            actions: Dict mapping junction_id to action (phase)
            
        Returns:
            Tuple of (observations, rewards, dones, info)
        """
        self.current_step += 1
        
        # Update phases and elapsed time
        for jid in range(self.n_junctions):
            action = actions.get(jid, self.phases[jid])
            
            # Check if phase change is allowed
            if self.elapsed_time[jid] >= MIN_GREEN_TIME and action != self.phases[jid]:
                # Phase change
                self.phases[jid] = action
                self.elapsed_time[jid] = 0
            else:
                self.elapsed_time[jid] += self.dt
        
        # Update queues (arrivals and departures)
        self._update_queues()
        
        # Get observations and rewards
        observations = self._get_observations()
        rewards, reward_breakdown = self._compute_rewards()
        
        # Check done
        dones = {jid: False for jid in range(self.n_junctions)}
        if self.current_step >= self.max_steps:
            for jid in range(self.n_junctions):
                dones[jid] = True
        
        # Info
        info = {
            "step": self.current_step,
            "phases": {jid: PHASE_NAMES[self.phases[jid]] for jid in range(self.n_junctions)},
            "queues": {jid: dict(self.queues[jid]) for jid in range(self.n_junctions)},
            "throughput": self.total_throughput.copy(),
            "rain_intensity": self.rain_intensity,
            "capacity_factor": self.capacity_factor,
            "reward_breakdown": reward_breakdown,
            "idss_stats": self.idss.get_stats(),
            "catc_stats": self.catc.get_mixing_stats(),
        }
        
        return observations, rewards, dones, info
    
    def _update_queues(self):
        """Update vehicle queues (arrivals and departures)."""
        # Calculate arrival rate (vehicles per time step)
        arrival_rate_per_step = self.arrival_rate / 3600 * self.dt
        
        for jid in range(self.n_junctions):
            # Random arrivals
            arrivals_NS = np.random.poisson(arrival_rate_per_step * 0.5)
            arrivals_EW = np.random.poisson(arrival_rate_per_step * 0.5)
            
            # Convert to PCU
            self.queues[jid]["NS"] += arrivals_NS * 1.0  # Assume cars
            self.queues[jid]["EW"] += arrivals_EW * 1.0
            
            # Departures based on phase
            phase = self.phases[jid]
            
            if phase == 0:  # NS Green
                # Departure rate depends on capacity
                departure_rate = self.capacity_factor * 2.0  # PCU per step
                departures = min(self.queues[jid]["NS"], departure_rate)
                self.queues[jid]["NS"] -= departures
                self.total_throughput[jid] += departures
                
            elif phase == 2:  # EW Green
                departure_rate = self.capacity_factor * 2.0
                departures = min(self.queues[jid]["EW"], departure_rate)
                self.queues[jid]["EW"] -= departures
                self.total_throughput[jid] += departures
            
            # Delay accumulation
            self.total_delay[jid] += (self.queues[jid]["NS"] + self.queues[jid]["EW"]) * self.dt
    
    def _get_observations(self) -> Dict[int, np.ndarray]:
        """Get observations for all junctions."""
        # Update weather (mock)
        self._update_weather()
        
        # Update IDSS communication
        obs_dict = {}
        for jid in range(self.n_junctions):
            obs_dict[jid] = self._get_junction_observation(jid)
        
        # Get intent messages from IDSS (pass base obs of 19 dims)
        intents = self.idss.update(obs_dict)
        
        # Build final observations (83 dims = 19 base + 64 intent)
        observations = {}
        for jid in range(self.n_junctions):
            obs = obs_dict[jid]
            
            # Append intent (64 dims)
            intent = intents.get(jid, np.zeros(64))
            obs_full = np.concatenate([obs, intent])
            
            observations[jid] = obs_full.astype(np.float32)
        
        return observations
    
    def _get_junction_observation(self, jid: int) -> np.ndarray:
        """Get observation for a single junction."""
        # Queue (4 dims)
        queue_NS = self.queues[jid]["NS"]
        queue_EW = self.queues[jid]["EW"]
        
        # Approaching queues
        queue_N = queue_NS * 0.4
        queue_S = queue_NS * 0.4
        queue_E = queue_EW * 0.4
        queue_W = queue_EW * 0.4
        
        queue_obs = np.array([queue_N, queue_S, queue_E, queue_W])
        
        # Phase (1 dim)
        phase_obs = np.array([self.phases[jid]])
        
        # Elapsed time (1 dim)
        elapsed_obs = np.array([self.elapsed_time[jid]])
        
        # Rain (1 dim)
        rain_obs = np.array([self.rain_intensity])
        
        # Event features (12 dims) - placeholder
        event_obs = np.zeros(12)
        
        # Combine
        obs = np.concatenate([
            queue_obs,      # 4
            phase_obs,      # 1
            elapsed_obs,    # 1
            rain_obs,       # 1
            event_obs,      # 12
        ])
        
        return obs.astype(np.float32)
    
    def _compute_rewards(self) -> Tuple[Dict[int, float], Dict]:
        """Compute rewards for all junctions."""
        rewards = {}
        reward_breakdown = {}
        
        for jid in range(self.n_junctions):
            # PCU queue
            pcu_queue = np.array([
                self.queues[jid]["NS"] * 0.4,
                self.queues[jid]["NS"] * 0.4,
                self.queues[jid]["EW"] * 0.4,
                self.queues[jid]["EW"] * 0.4,
            ])
            
            # Throughput
            throughput = self.total_throughput[jid]
            
            # Overflow
            overflow = pcu_queue > self.capacity_per_junction * self.capacity_factor
            
            # Phases
            prev_phase = 0  # Simplified
            curr_phase = self.phases[jid]
            
            # Neighbor discharge times (from IDSS)
            neighbors = self.idss.get_neighbors(jid)
            neighbor_times = []
            for nid in neighbors:
                neighbor_times.append(self.total_throughput[nid])
            
            # Compute reward
            reward = self.reward_calculator.compute(
                pcu_queue=pcu_queue,
                throughput=throughput,
                overflow=overflow,
                prev_phase=prev_phase,
                curr_phase=curr_phase,
                neighbor_discharge_times=neighbor_times if neighbor_times else None,
            )
            
            rewards[jid] = reward
            reward_breakdown[jid] = {
                "total": reward,
                "queue": float(np.sum(pcu_queue)),
                "throughput": throughput,
            }
        
        return rewards, reward_breakdown
    
    def _update_weather(self):
        """Update weather conditions (mock)."""
        # Simple weather simulation
        time_of_day = (self.current_step * self.dt) / 3600  # Hours
        
        # Rain is more likely in afternoon
        if 12 <= time_of_day <= 18:
            target_rain = 0.3 + 0.4 * np.sin(time_of_day * np.pi / 12)
        else:
            target_rain = 0.0
        
        # Smooth transition
        self.rain_intensity = 0.9 * self.rain_intensity + 0.1 * target_rain
        
        # Update capacity factor
        self.capacity_factor = self.catc.get_capacity_factor()
        
        # Update CATC
        self.catc.set_rain(self.rain_intensity)
    
    def get_state(self) -> Dict:
        """Get current environment state."""
        return {
            "step": self.current_step,
            "phases": {jid: PHASE_NAMES[self.phases[jid]] for jid in range(self.n_junctions)},
            "queues": {jid: dict(self.queues[jid]) for jid in range(self.n_junctions)},
            "elapsed_time": self.elapsed_time.tolist(),
            "total_throughput": self.total_throughput.tolist(),
            "total_delay": self.total_delay.tolist(),
            "rain_intensity": self.rain_intensity,
            "capacity_factor": self.capacity_factor,
            "catc_stats": self.catc.get_mixing_stats(),
            "idss_stats": self.idss.get_stats(),
        }
    
    def render(self):
        """Render the environment (for debugging)."""
        print(f"Step: {self.current_step}")
        for jid in range(self.n_junctions):
            print(f"  Junction {jid}: Phase={PHASE_NAMES[self.phases[jid]]}, "
                  f"Queue_NS={self.queues[jid]['NS']:.1f}, "
                  f"Queue_EW={self.queues[jid]['EW']:.1f}")


def create_environment(
    n_junctions: int = 12,
    dt: float = 5.0,
    seed: Optional[int] = None,
) -> TrafficEnvironment:
    """
    Create a traffic environment.
    
    Args:
        n_junctions: Number of junctions
        dt: Time step
        seed: Random seed
        
    Returns:
        TrafficEnvironment instance
    """
    return TrafficEnvironment(
        n_junctions=n_junctions,
        dt=dt,
        seed=seed,
    )
