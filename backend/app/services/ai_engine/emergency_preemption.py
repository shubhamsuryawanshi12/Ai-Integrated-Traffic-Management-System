"""
Emergency Vehicle Preemption System for UrbanFlow

Detects and prioritizes emergency vehicles (ambulances, fire trucks, police)
at intersections to ensure fast and safe passage.

Features:
- Siren detection via audio
- Visual detection of emergency vehicles
- Preemption signal coordination
- Green wave creation
- Multi-intersection coordination
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from enum import Enum
import json

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class EmergencyType(Enum):
    """Types of emergency vehicles."""
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"
    OTHER = "other"


class EmergencyStatus(Enum):
    """Status of emergency response."""
    IDLE = "idle"
    DETECTED = "detected"
    APPROACHING = "approaching"
    IN_TRANSIT = "in_transit"
    CLEARED = "cleared"


class SirenDetector:
    """
    Detects emergency vehicle sirens from audio input.
    Uses frequency analysis to identify characteristic siren patterns.
    """
    
    # Siren frequencies (typical)
    SIREN_FREQUENCIES = {
        'wail': (400, 1200),      # Hz range for wail
        'yelp': (1200, 2000),     # Hz range for yelp
        'piercer': (2000, 3500),  # Hz range for piercer
    }
    
    # Audio processing parameters
    SAMPLE_RATE = 44100  # Hz
    FFT_SIZE = 2048
    HOP_LENGTH = 512
    
    @staticmethod
    def detect_siren(audio_data: np.ndarray) -> Tuple[bool, float, Optional[str]]:
        """
        Detect siren in audio data.
        
        Args:
            audio_data: Audio samples as numpy array
            
        Returns:
            (detected, confidence, siren_type)
        """
        if not NUMPY_AVAILABLE or len(audio_data) < SirenDetector.FFT_SIZE:
            return False, 0.0, None
        
        try:
            # Compute spectrogram
            import scipy.signal as signal
            
            frequencies, times, spectrogram = signal.spectrogram(
                audio_data,
                fs=SirenDetector.SAMPLE_RATE,
                nperseg=SirenDetector.FFT_SIZE,
                noverlap=SirenDetector.HOP_LENGTH
            )
            
            # Look for characteristic siren patterns
            for siren_type, (low_freq, high_freq) in SirenDetector.SIREN_FREQUENCIES.items():
                # Find frequency bins in siren range
                freq_mask = (frequencies >= low_freq) & (frequencies <= high_freq)
                
                if np.any(freq_mask):
                    # Check if there's energy in siren frequencies
                    siren_energy = np.mean(spectrogram[freq_mask, :])
                    total_energy = np.mean(spectrogram)
                    
                    if total_energy > 0:
                        ratio = siren_energy / total_energy
                        
                        if ratio > 0.3:  # Threshold
                            confidence = min(ratio, 1.0)
                            return True, confidence, siren_type
            
            return False, 0.0, None
            
        except Exception as e:
            print(f"Siren detection error: {e}")
            return False, 0.0, None
    
    @staticmethod
    def simulate_detection() -> Tuple[bool, float, Optional[str]]:
        """Simulate siren detection for testing."""
        import random
        
        # 5% chance of detection for demo
        if random.random() < 0.05:
            siren_types = list(SirenDetector.SIREN_FREQUENCIES.keys())
            return True, random.uniform(0.7, 0.95), random.choice(siren_types)
        
        return False, 0.0, None


class EmergencyVehicleDetector:
    """
    Detects emergency vehicles from camera feed.
    Uses visual features and optionally V2X communication.
    """
    
    EMERGENCY_COLORS = {
        'red': (255, 0, 0),
        'white': (255, 255, 255),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
    }
    
    @staticmethod
    def detect_from_frame(frame: np.ndarray) -> Tuple[bool, Optional[EmergencyType], float]:
        """
        Detect emergency vehicle in video frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            (detected, vehicle_type, confidence)
        """
        # This would use YOLO or similar in production
        # Simulating detection for demo
        if not NUMPY_AVAILABLE:
            return False, None, 0.0
        
        # For demo, return false (no detection)
        # In production, would use:
        # - Object detection for vehicles
        # - Color analysis for emergency lights
        # - License plate recognition
        # - V2X messages
        
        return False, None, 0.0
    
    @staticmethod
    def detect_from_v2x(message: Dict) -> Tuple[bool, Optional[EmergencyType], float]:
        """
        Detect emergency vehicle from V2X message.
        
        Args:
            message: V2X BSM (Basic Safety Message) or similar
            
        Returns:
            (detected, vehicle_type, confidence)
        """
        if not message:
            return False, None, 0.0
        
        # Check message for emergency indicators
        if message.get('vehicle_type') == 'emergency':
            ev_type = message.get('emergency_type', 'other')
            return True, ev_type, 0.95
        
        return False, None, 0.0


class PreemptionController:
    """
    Controls traffic signals to prioritize emergency vehicles.
    Creates green waves and clears intersections.
    """
    
    # Phase mapping for preemption
    PHASE_MAP = {
        0: 'NS_GREEN',
        1: 'NS_YELLOW',
        2: 'EW_GREEN',
        3: 'EW_YELLOW',
    }
    
    # Direction to phase
    DIRECTION_TO_PHASE = {
        'north': 0,  # NS Green
        'south': 0,
        'east': 2,   # EW Green
        'west': 2,
    }
    
    def __init__(self):
        self.active_preemptions: Dict[str, Dict] = {}
    
    def request_preemption(
        self,
        intersection_id: str,
        emergency_vehicle_id: str,
        direction: str,
        distance: float,
        speed: float
    ) -> Dict:
        """
        Request preemption for an emergency vehicle.
        
        Args:
            intersection_id: Target intersection
            emergency_vehicle_id: ID of emergency vehicle
            direction: Direction of travel (north, south, east, west)
            distance: Distance to intersection (meters)
            speed: Vehicle speed (m/s)
            
        Returns:
            Preemption plan
        """
        # Calculate time to arrival
        time_to_arrival = distance / speed if speed > 0 else 999
        
        # Determine required phase
        required_phase = self.DIRECTION_TO_PHASE.get(direction, 0)
        
        # Create preemption plan
        plan = {
            'intersection_id': intersection_id,
            'emergency_vehicle_id': emergency_vehicle_id,
            'direction': direction,
            'distance': distance,
            'speed': speed,
            'time_to_arrival': time_to_arrival,
            'required_phase': required_phase,
            'required_phase_name': self.PHASE_MAP[required_phase],
            'status': EmergencyStatus.APPROACHING.value,
            'created_at': datetime.now().isoformat(),
            'priority': 1,  # Highest priority
        }
        
        self.active_preemptions[emergency_vehicle_id] = plan
        
        return plan
    
    def get_preemption_action(
        self,
        intersection_id: str,
        current_phase: int,
        phase_time: float
    ) -> Tuple[int, str]:
        """
        Get signal action for preemption.
        
        Args:
            intersection_id: Intersection ID
            current_phase: Current signal phase
            phase_time: Time in current phase
            
        Returns:
            (action, reason)
        """
        # Find active preemption for this intersection
        preempt = None
        for ev_id, p in self.active_preemptions.items():
            if p['intersection_id'] == intersection_id:
                preempt = p
                break
        
        if not preempt:
            return current_phase, "normal"
        
        # Check if we need to switch
        required_phase = preempt['required_phase']
        
        if current_phase == required_phase:
            # Already in correct phase
            return current_phase, f"preemption_active:{preempt['emergency_vehicle_id']}"
        
        # Need to switch to required phase
        # Calculate shortest path to required phase
        # (e.g., if in phase 2 (EW_GREEN) and need phase 0 (NS_GREEN),
        # we need to go through yellow phases)
        
        # For simplicity, go directly to required phase
        return required_phase, f"preemption_switch:{preempt['emergency_vehicle_id']}"
    
    def clear_preemption(self, emergency_vehicle_id: str):
        """Clear preemption after vehicle passes."""
        if emergency_vehicle_id in self.active_preemptions:
            self.active_preemptions[emergency_vehicle_id]['status'] = EmergencyStatus.CLEARED.value
            # Remove after delay
            del self.active_preemptions[emergency_vehicle_id]
    
    def get_active_preemptions(self) -> List[Dict]:
        """Get all active preemptions."""
        return list(self.active_preemptions.values())


class GreenWaveCoordinator:
    """
    Coordinates green waves across multiple intersections for emergency vehicles.
    """
    
    def __init__(self):
        self.preemption_controller = PreemptionController()
        self.green_wave_active = False
    
    def create_green_wave(
        self,
        emergency_vehicle_id: str,
        route: List[Dict]
    ) -> Dict:
        """
        Create green wave along vehicle route.
        
        Args:
            emergency_vehicle_id: ID of emergency vehicle
            route: List of intersections with distance/speed info
            
        Returns:
            Green wave plan
        """
        preemptions = []
        
        for intersection in route:
            plan = self.preemption_controller.request_preemption(
                intersection_id=intersection['id'],
                emergency_vehicle_id=emergency_vehicle_id,
                direction=intersection['direction'],
                distance=intersection['distance'],
                speed=intersection['speed']
            )
            preemptions.append(plan)
        
        self.green_wave_active = True
        
        return {
            'emergency_vehicle_id': emergency_vehicle_id,
            'route': route,
            'preemptions': preemptions,
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
    
    def clear_green_wave(self, emergency_vehicle_id: str):
        """Clear green wave after vehicle passes."""
        self.preemption_controller.clear_preemption(emergency_vehicle_id)
        
        # Check if any preemptions remain
        if not self.preemption_controller.get_active_preemptions():
            self.green_wave_active = False
    
    def calculate_timing(
        self,
        route: List[Dict],
        desired_speed: float = 15.0  # m/s (~54 km/h)
    ) -> List[float]:
        """
        Calculate optimal signal timing for green wave.
        
        Args:
            route: List of intersections
            desired_speed: Desired travel speed
            
        Returns:
            List of phase start times for each intersection
        """
        timings = []
        cumulative_time = 0.0
        
        for i, intersection in enumerate(route):
            if i == 0:
                timings.append(0.0)
            else:
                # Time to travel between intersections
                distance = route[i]['distance']
                travel_time = distance / desired_speed
                cumulative_time += travel_time
                timings.append(cumulative_time)
        
        return timings


class EmergencyPreemptionSystem:
    """
    Main emergency preemption system coordinating all components.
    """
    
    def __init__(self):
        self.siren_detector = SirenDetector()
        self.vehicle_detector = EmergencyVehicleDetector()
        self.preemption_controller = PreemptionController()
        self.green_wave_coordinator = GreenWaveCoordinator()
        
        self.alerts: List[Dict] = []
        self.statistics = {
            'total_detections': 0,
            'total_preemptions': 0,
            'avg_response_time': 0.0,
            'by_type': {
                'ambulance': 0,
                'fire_truck': 0,
                'police': 0,
            }
        }
    
    def detect_emergency(
        self,
        audio_data: Optional[np.ndarray] = None,
        frame: Optional[np.ndarray] = None,
        v2x_message: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Detect emergency vehicle from any available input.
        
        Args:
            audio_data: Audio samples
            frame: Video frame
            v2x_message: V2X message
            
        Returns:
            (detected, detection_info)
        """
        detection = None
        
        # Check V2X first (most reliable)
        if v2x_message:
            detected, ev_type, confidence = self.vehicle_detector.detect_from_v2x(v2x_message)
            if detected:
                detection = {
                    'type': ev_type,
                    'confidence': confidence,
                    'source': 'v2x'
                }
        
        # Check audio
        if detection is None and audio_data is not None:
            detected, confidence, siren_type = self.siren_detector.detect_siren(audio_data)
            if detected:
                detection = {
                    'type': EmergencyType.AMBULANCE.value,
                    'confidence': confidence,
                    'siren_type': siren_type,
                    'source': 'audio'
                }
        
        # Check video
        if detection is None and frame is not None:
            detected, ev_type, confidence = self.vehicle_detector.detect_from_frame(frame)
            if detected:
                detection = {
                    'type': ev_type.value if ev_type else EmergencyType.OTHER.value,
                    'confidence': confidence,
                    'source': 'camera'
                }
        
        if detection:
            self.statistics['total_detections'] += 1
            detection['timestamp'] = datetime.now().isoformat()
            self.alerts.append(detection)
            
            # Update by type
            ev_type = detection.get('type', 'other')
            if ev_type in self.statistics['by_type']:
                self.statistics['by_type'][ev_type] += 1
        
        return detection is not None, detection
    
    def activate_preemption(
        self,
        intersection_id: str,
        detection_info: Dict,
        route: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Activate preemption for detected emergency vehicle.
        
        Args:
            intersection_id: Target intersection
            detection_info: Detection information
            route: Optional route for green wave
            
        Returns:
            Preemption result
        """
        # Create emergency vehicle ID
        ev_id = f"EV_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # If route provided, create green wave
        if route:
            result = self.green_wave_coordinator.create_green_wave(ev_id, route)
            self.statistics['total_preemptions'] += 1
            return result
        
        # Single intersection preemption
        plan = self.preemption_controller.request_preemption(
            intersection_id=intersection_id,
            emergency_vehicle_id=ev_id,
            direction=detection_info.get('direction', 'north'),
            distance=detection_info.get('distance', 100),
            speed=detection_info.get('speed', 10)
        )
        
        self.statistics['total_preemptions'] += 1
        
        return {
            'status': 'preemption_active',
            'plan': plan,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_signal_action(
        self,
        intersection_id: str,
        current_phase: int,
        phase_time: float
    ) -> Tuple[int, str]:
        """Get signal action considering emergency preemption."""
        return self.preemption_controller.get_preemption_action(
            intersection_id, current_phase, phase_time
        )
    
    def get_status(self) -> Dict:
        """Get current system status."""
        return {
            'active_preemptions': self.preemption_controller.get_active_preemptions(),
            'green_wave_active': self.green_wave_coordinator.green_wave_active,
            'recent_alerts': self.alerts[-10:],
            'statistics': self.statistics
        }
    
    def clear_alert(self, alert_id: int):
        """Clear an alert."""
        if 0 <= alert_id < len(self.alerts):
            self.alerts.pop(alert_id)


# Singleton instance
_emergency_system = None

def get_emergency_system() -> EmergencyPreemptionSystem:
    """Get singleton emergency preemption system."""
    global _emergency_system
    if _emergency_system is None:
        _emergency_system = EmergencyPreemptionSystem()
    return _emergency_system
