"""
Hybrid Environment for UrbanFlow
Combines SUMO simulation data with real-world camera data
"""

import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime
import time

from ..sumo.environment import SumoEnvironment
from ..vision.camera_stream import MobileCamera
from ..vision.signal_detector import SignalDetector
from ..vision.vehicle_detector import VehicleDetector
from ..vision.data_processor import DataProcessor


class HybridEnvironment:
    """
    Hybrid traffic environment that can use:
    - SUMO simulation only
    - Real-world camera data only
    - Combined (hybrid) mode
    """
    
    def __init__(self, 
                 mode: str = 'simulation',
                 config: Optional[Dict] = None):
        """
        Initialize the hybrid environment.
        
        Args:
            mode: One of 'simulation', 'real_world', or 'hybrid'
            config: Configuration dictionary
        """
        self.mode = mode
        self.config = config or {}
        
        # Components
        self.sumo_env = None
        self.camera = None
        self.signal_detector = None
        self.vehicle_detector = None
        self.data_processor = None
        
        # State
        self.current_state = None
        self.last_update = None
        self.step_count = 0
        
        # Hybrid weights
        self.sim_weight = self.config.get('sim_weight', 0.7)
        self.real_weight = self.config.get('real_weight', 0.3)
        
        # Initialize components based on mode
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize required components based on mode."""
        if self.mode in ['simulation', 'hybrid']:
            try:
                net_file = self.config.get('net_file', 'sumo_files/networks/simple_grid.net.xml')
                rou_file = self.config.get('rou_file', 'sumo_files/routes/traffic_routes.rou.xml')
                self.sumo_env = SumoEnvironment(net_file, rou_file, use_gui=False)
                print("[OK] SUMO environment initialized")
            except Exception as e:
                print(f"[WARNING] SUMO initialization failed: {e}")
                if self.mode == 'simulation':
                    raise
        
        if self.mode in ['real_world', 'hybrid']:
            try:
                self.camera = MobileCamera(config=self.config.get('camera', {}))
                self.signal_detector = SignalDetector(config=self.config.get('signal', {}))
                self.vehicle_detector = VehicleDetector(
                    model_path=self.config.get('yolo_model', 'yolov8n.pt'),
                    config=self.config.get('vehicle', {})
                )
                self.data_processor = DataProcessor(config=self.config.get('processor', {}))
                print("[OK] Camera-based detection initialized")
            except Exception as e:
                print(f"[WARNING] Camera initialization failed: {e}")
                if self.mode == 'real_world':
                    raise
    
    def start(self) -> bool:
        """Start the environment."""
        success = True
        
        if self.sumo_env:
            try:
                self.sumo_env.start()
            except Exception as e:
                print(f"[WARNING] SUMO start failed: {e}")
                success = False
        
        if self.camera:
            self.camera.start()
        
        return success
    
    def stop(self):
        """Stop the environment."""
        if self.sumo_env:
            self.sumo_env.close()
        
        if self.camera:
            self.camera.stop()
    
    def step(self, action: Optional[int] = None) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to take (traffic signal phase, optional)
            
        Returns:
            Tuple of (state, reward, done, info)
        """
        self.step_count += 1
        
        # Get data from appropriate sources
        sim_state = None
        real_state = None
        
        if self.mode == 'simulation' and self.sumo_env:
            # Get SUMO simulation data
            if action is not None:
                states = self.sumo_env.get_state()
                for ts_id in states:
                    self.sumo_env.apply_actions({ts_id: action})
            self.sumo_env.step()
            sim_state = self._process_sumo_state()
        
        elif self.mode == 'real_world' and self.camera:
            # Get camera data
            real_state = self._process_camera_state()
        
        elif self.mode == 'hybrid':
            # Get both and combine
            if self.sumo_env:
                if action is not None:
                    states = self.sumo_env.get_state()
                    for ts_id in states:
                        self.sumo_env.apply_actions({ts_id: action})
                self.sumo_env.step()
                sim_state = self._process_sumo_state()
            
            if self.camera:
                real_state = self._process_camera_state()
        
        # Combine states
        state = self._combine_states(sim_state, real_state)
        
        # Calculate reward
        reward = self._calculate_reward(state)
        
        # Check if done
        done = self.step_count >= self.config.get('max_steps', 10000)
        
        # Build info
        info = {
            'step': self.step_count,
            'mode': self.mode,
            'sim_state': sim_state.tolist() if sim_state is not None else None,
            'real_state': real_state.tolist() if real_state is not None else None,
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_state = state
        self.last_update = time.time()
        
        return state, reward, done, info
    
    def _process_sumo_state(self) -> np.ndarray:
        """Process SUMO simulation state into feature vector."""
        states = self.sumo_env.get_state()
        
        features = []
        for ts_id, state in states.items():
            # state is [queue_length, num_vehicles, avg_speed, phase]
            features.extend(state)
        
        # Pad or truncate to fixed size
        target_size = 32
        features = features[:target_size]
        while len(features) < target_size:
            features.append(0.0)
        
        return np.array(features, dtype=np.float32)
    
    def _process_camera_state(self) -> np.ndarray:
        """Process camera data into feature vector."""
        frame = self.camera.get_frame()
        
        if frame is None:
            return np.zeros(32, dtype=np.float32)
        
        # Run detections
        signal_result = self.signal_detector.detect(frame)
        vehicle_result = self.vehicle_detector.detect(frame)
        
        # Process into unified state
        processed = self.data_processor.process(signal_result, vehicle_result)
        
        # Convert to RL state vector
        return self.data_processor.to_rl_state(processed)
    
    def _combine_states(self, sim_state: Optional[np.ndarray], 
                       real_state: Optional[np.ndarray]) -> np.ndarray:
        """Combine simulation and real-world states."""
        if sim_state is None and real_state is None:
            return np.zeros(32, dtype=np.float32)
        
        if sim_state is None:
            return real_state
        
        if real_state is None:
            return sim_state
        
        # Weighted combination
        combined = (self.sim_weight * sim_state + 
                   self.real_weight * real_state)
        
        return combined.astype(np.float32)
    
    def _calculate_reward(self, state: np.ndarray) -> float:
        """Calculate reward from state."""
        # Extract queue-related features (first 4 features per lane)
        queue_features = state[:4]
        total_queue = np.sum(queue_features)
        
        # Reward: negative queue length (less queue = better)
        reward = -total_queue
        
        # Bonus for flow
        if total_queue < 5:
            reward += 10
        
        return float(reward)
    
    def get_state(self) -> np.ndarray:
        """Get current state without stepping."""
        if self.current_state is not None:
            return self.current_state
        return np.zeros(32, dtype=np.float32)
    
    def get_mode(self) -> str:
        """Get current mode."""
        return self.mode
    
    def set_mode(self, mode: str):
        """Change environment mode."""
        if mode not in ['simulation', 'real_world', 'hybrid']:
            raise ValueError(f"Invalid mode: {mode}")
        
        self.mode = mode
        self._initialize_components()
    
    def get_stats(self) -> Dict:
        """Get environment statistics."""
        return {
            'mode': self.mode,
            'step_count': self.step_count,
            'last_update': self.last_update,
            'sim_weight': self.sim_weight,
            'real_weight': self.real_weight,
            'sumo_available': self.sumo_env is not None,
            'camera_available': self.camera is not None
        }
