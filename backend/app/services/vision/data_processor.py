"""
Data Processor for Vision -> RL Integration
Converts camera detection data to RL environment state format
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import json


class DataProcessor:
    """
    Processes vision detection data and converts to RL training format.
    Bridges camera output with RL environment state space.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # State history for temporal features
        self.state_history = deque(maxlen=100)
        self.signal_history = deque(maxlen=50)
        self.vehicle_history = deque(maxlen=50)
        
        # Normalization parameters (can be calibrated)
        self.max_queue_length = self.config.get('max_queue_length', 50)
        self.max_vehicle_count = self.config.get('max_vehicle_count', 100)
        self.max_speed = self.config.get('max_speed', 20.0)  # m/s
        self.max_wait_time = self.config.get('max_wait_time', 120.0)  # seconds
        
        # Phase mapping
        self.phase_map = {'red': 0, 'yellow': 1, 'green': 2}
        
    def process(self, signal_data: Optional[Dict], vehicle_data: Optional[Dict]) -> Dict:
        """
        Process signal and vehicle detection data into unified state.
        
        Args:
            signal_data: Output from SignalDetector.detect()
            vehicle_data: Output from VehicleDetector.detect()
            
        Returns:
            Processed state dictionary
        """
        timestamp = datetime.now().isoformat()
        
        # Store in history
        if signal_data:
            self.signal_history.append(signal_data)
        if vehicle_data:
            self.vehicle_history.append(vehicle_data)
        
        # Build state
        state = {
            'timestamp': timestamp,
            'raw': {
                'signal': signal_data,
                'vehicles': vehicle_data
            }
        }
        
        # Extract signal features
        if signal_data:
            state['signal'] = {
                'current_phase': signal_data.get('signal_state'),
                'phase_id': self.phase_map.get(signal_data.get('signal_state'), -1),
                'phase_duration': signal_data.get('phase_duration', 0),
                'cycle_time': signal_data.get('cycle_time', 0),
                'confidence': signal_data.get('confidence', 0)
            }
        else:
            state['signal'] = {
                'current_phase': None,
                'phase_id': -1,
                'phase_duration': 0,
                'cycle_time': 0,
                'confidence': 0
            }
        
        # Extract vehicle features
        if vehicle_data:
            lanes = vehicle_data.get('lanes', {})
            state['traffic'] = {
                'total_vehicles': vehicle_data.get('total_vehicles', 0),
                'lanes': {
                    lane: {
                        'queue_length': data.get('queue_length', 0),
                        'vehicle_count': data.get('vehicle_count', 0),
                        'avg_speed': data.get('avg_speed', 0)
                    }
                    for lane, data in lanes.items()
                },
                'vehicle_types': vehicle_data.get('vehicle_types', {}),
                'processing_fps': vehicle_data.get('processing_fps', 0)
            }
        else:
            state['traffic'] = {
                'total_vehicles': 0,
                'lanes': {},
                'vehicle_types': {},
                'processing_fps': 0
            }
        
        # Calculate derived metrics
        state['metrics'] = self._calculate_metrics(state)
        
        # Store in history
        self.state_history.append(state)
        
        return state
    
    def _calculate_metrics(self, state: Dict) -> Dict:
        """Calculate derived traffic metrics."""
        traffic = state.get('traffic', {})
        lanes = traffic.get('lanes', {})
        
        total_queue = sum(l.get('queue_length', 0) for l in lanes.values())
        total_vehicles = sum(l.get('vehicle_count', 0) for l in lanes.values())
        
        speeds = [l.get('avg_speed', 0) for l in lanes.values() if l.get('avg_speed', 0) > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        
        # Congestion index (0-1)
        congestion = min(total_queue / max(self.max_queue_length, 1), 1.0)
        
        # Throughput estimation
        throughput = total_vehicles * (avg_speed / max(self.max_speed, 1))
        
        return {
            'total_queue_length': total_queue,
            'total_vehicle_count': total_vehicles,
            'average_speed': round(avg_speed, 2),
            'congestion_index': round(congestion, 3),
            'estimated_throughput': round(throughput, 2)
        }
    
    def to_rl_state(self, state: Optional[Dict] = None) -> np.ndarray:
        """
        Convert processed state to RL environment state vector.
        
        Compatible with existing UrbanFlow RL agent (32-dimensional state).
        
        Returns:
            numpy array of shape (32,) representing the state
        """
        if state is None:
            state = self.state_history[-1] if self.state_history else None
        
        if state is None:
            return np.zeros(32, dtype=np.float32)
        
        # Build state vector
        features = []
        
        # Signal features (4 features)
        signal = state.get('signal', {})
        features.append(self._normalize(signal.get('phase_id', 0), 0, 2))
        features.append(self._normalize(signal.get('phase_duration', 0), 0, self.max_wait_time))
        features.append(self._normalize(signal.get('cycle_time', 0), 0, 180))
        features.append(signal.get('confidence', 0))
        
        # Per-lane features (4 lanes × 4 features = 16 features)
        traffic = state.get('traffic', {})
        lanes = traffic.get('lanes', {})
        
        for lane in ['north', 'south', 'east', 'west']:
            lane_data = lanes.get(lane, {})
            features.append(self._normalize(lane_data.get('queue_length', 0), 0, self.max_queue_length))
            features.append(self._normalize(lane_data.get('vehicle_count', 0), 0, self.max_vehicle_count))
            features.append(self._normalize(lane_data.get('avg_speed', 0), 0, self.max_speed))
            features.append(0.0)  # Placeholder for waiting time
        
        # Global metrics (4 features)
        metrics = state.get('metrics', {})
        features.append(self._normalize(metrics.get('total_queue_length', 0), 0, self.max_queue_length * 4))
        features.append(self._normalize(metrics.get('total_vehicle_count', 0), 0, self.max_vehicle_count * 4))
        features.append(metrics.get('congestion_index', 0))
        features.append(self._normalize(metrics.get('estimated_throughput', 0), 0, 100))
        
        # Temporal features (8 features - differences from last state)
        if len(self.state_history) >= 2:
            prev_state = self.state_history[-2]
            prev_traffic = prev_state.get('traffic', {})
            prev_lanes = prev_traffic.get('lanes', {})
            
            for lane in ['north', 'south', 'east', 'west']:
                curr = lanes.get(lane, {}).get('queue_length', 0)
                prev = prev_lanes.get(lane, {}).get('queue_length', 0)
                features.append(self._normalize(curr - prev, -10, 10))
            
            for lane in ['north', 'south', 'east', 'west']:
                curr = lanes.get(lane, {}).get('vehicle_count', 0)
                prev = prev_lanes.get(lane, {}).get('vehicle_count', 0)
                features.append(self._normalize(curr - prev, -20, 20))
        else:
            features.extend([0.0] * 8)
        
        # Ensure exactly 32 features
        while len(features) < 32:
            features.append(0.0)
        
        return np.array(features[:32], dtype=np.float32)
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to [0, 1] range."""
        if max_val <= min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
    
    def to_training_sample(self, action: int = None, reward: float = None) -> Dict:
        """
        Create a training sample for RL from current state.
        
        Args:
            action: The action taken (if known)
            reward: The observed reward (if known)
            
        Returns:
            Dictionary suitable for RL training
        """
        state_vec = self.to_rl_state()
        
        sample = {
            'timestamp': datetime.now().isoformat(),
            'state': state_vec.tolist(),
            'action': action,
            'reward': reward,
            'done': False
        }
        
        return sample
    
    def calculate_reward(self, state: Optional[Dict] = None) -> float:
        """
        Calculate reward signal for RL training.
        
        Reward = -(waiting_time + congestion_penalty)
        
        Returns:
            Reward value (negative for bad traffic, near zero for good flow)
        """
        if state is None:
            state = self.state_history[-1] if self.state_history else None
        
        if state is None:
            return 0.0
        
        metrics = state.get('metrics', {})
        
        # Penalties
        queue_penalty = metrics.get('total_queue_length', 0) * 0.1
        congestion_penalty = metrics.get('congestion_index', 0) * 10
        
        # Bonuses
        throughput_bonus = metrics.get('estimated_throughput', 0) * 0.1
        
        # Final reward (negative is bad)
        reward = throughput_bonus - queue_penalty - congestion_penalty
        
        return round(reward, 3)
    
    def export_training_data(self, filepath: str, samples: List[Dict] = None):
        """Export collected training data to JSON file."""
        if samples is None:
            samples = [self.to_training_sample() for _ in range(len(self.state_history))]
        
        data = {
            'export_time': datetime.now().isoformat(),
            'num_samples': len(samples),
            'state_dim': 32,
            'samples': samples
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return len(samples)
    
    def get_summary(self) -> Dict:
        """Get summary of collected data."""
        return {
            'total_states': len(self.state_history),
            'total_signals': len(self.signal_history),
            'total_vehicles': len(self.vehicle_history),
            'latest_metrics': self.state_history[-1].get('metrics', {}) if self.state_history else {}
        }
