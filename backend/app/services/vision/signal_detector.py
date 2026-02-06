"""
Traffic Signal Detector using OpenCV
Detects traffic lights and classifies their color (Red/Yellow/Green)
Tracks phase durations and cycle times
"""

import cv2
import numpy as np
from datetime import datetime
from collections import deque
from typing import Dict, List, Tuple, Optional
import json
import time


class SignalDetector:
    """
    Detects traffic signals in video frames using color detection and shape analysis.
    Tracks signal state changes and timing information.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the signal detector.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # HSV color ranges for traffic lights (adjustable for different lighting)
        self.color_ranges = {
            'red': {
                'lower1': np.array([0, 100, 100]),
                'upper1': np.array([10, 255, 255]),
                'lower2': np.array([160, 100, 100]),  # Red wraps around in HSV
                'upper2': np.array([180, 255, 255])
            },
            'yellow': {
                'lower': np.array([15, 100, 100]),
                'upper': np.array([35, 255, 255])
            },
            'green': {
                'lower': np.array([40, 50, 50]),
                'upper': np.array([90, 255, 255])
            }
        }
        
        # State tracking
        self.current_state = None
        self.state_start_time = None
        self.state_history = deque(maxlen=100)
        self.phase_durations = {'red': [], 'yellow': [], 'green': []}
        self.last_detection_time = None
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        
        # Detection parameters
        self.min_radius = self.config.get('min_radius', 10)
        self.max_radius = self.config.get('max_radius', 50)
        self.detection_region = self.config.get('detection_region', None)  # (x, y, w, h)
        
    def detect(self, frame: np.ndarray) -> Dict:
        """
        Detect traffic signal in a frame.
        
        Args:
            frame: BGR image frame from camera
            
        Returns:
            Dictionary with detection results
        """
        timestamp = datetime.now().isoformat()
        
        # Apply detection region if specified
        if self.detection_region:
            x, y, w, h = self.detection_region
            roi = frame[y:y+h, x:x+w]
        else:
            roi = frame
            
        # Convert to HSV
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Detect each color
        detections = {}
        for color in ['red', 'yellow', 'green']:
            mask = self._create_color_mask(hsv, color)
            circles = self._detect_circles(mask)
            confidence = self._calculate_confidence(mask, circles)
            detections[color] = {
                'detected': len(circles) > 0,
                'confidence': confidence,
                'circles': circles
            }
        
        # Determine current signal state
        signal_state = self._determine_state(detections)
        
        # Update state tracking
        self._update_state_tracking(signal_state, timestamp)
        
        # Calculate phase duration
        phase_duration = 0
        if self.state_start_time:
            phase_duration = (datetime.now() - self.state_start_time).total_seconds()
        
        # Calculate average cycle time
        cycle_time = self._calculate_cycle_time()
        
        result = {
            'timestamp': timestamp,
            'signal_state': signal_state,
            'phase_duration': round(phase_duration, 1),
            'cycle_time': cycle_time,
            'confidence': detections.get(signal_state, {}).get('confidence', 0) if signal_state else 0,
            'detections': detections,
            'state_history': list(self.state_history)[-10:]  # Last 10 states
        }
        
        self.last_detection_time = time.time()
        return result
    
    def _create_color_mask(self, hsv: np.ndarray, color: str) -> np.ndarray:
        """Create a binary mask for the specified color."""
        if color == 'red':
            # Red requires two ranges due to HSV wraparound
            mask1 = cv2.inRange(hsv, 
                               self.color_ranges['red']['lower1'],
                               self.color_ranges['red']['upper1'])
            mask2 = cv2.inRange(hsv,
                               self.color_ranges['red']['lower2'],
                               self.color_ranges['red']['upper2'])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv,
                              self.color_ranges[color]['lower'],
                              self.color_ranges[color]['upper'])
        
        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _detect_circles(self, mask: np.ndarray) -> List[Tuple[int, int, int]]:
        """Detect circular shapes in mask using Hough Transform."""
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(mask, (9, 9), 2)
        
        # Detect circles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=self.min_radius,
            maxRadius=self.max_radius
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype(int)
            return [(x, y, r) for x, y, r in circles]
        return []
    
    def _calculate_confidence(self, mask: np.ndarray, circles: List) -> float:
        """Calculate detection confidence based on mask coverage and circles."""
        if len(circles) == 0:
            return 0.0
            
        # Calculate percentage of mask that's white
        mask_coverage = np.sum(mask > 0) / mask.size
        
        # Normalize confidence
        circle_confidence = min(len(circles) / 3, 1.0)  # Max 3 circles
        coverage_confidence = min(mask_coverage * 100, 1.0)  # Max 1% coverage
        
        confidence = (circle_confidence * 0.7 + coverage_confidence * 0.3)
        return round(confidence, 2)
    
    def _determine_state(self, detections: Dict) -> Optional[str]:
        """Determine the current signal state based on detections."""
        # Priority: Red > Yellow > Green (safety first)
        for color in ['red', 'yellow', 'green']:
            if (detections[color]['detected'] and 
                detections[color]['confidence'] >= self.confidence_threshold):
                return color
        return None
    
    def _update_state_tracking(self, new_state: Optional[str], timestamp: str):
        """Update state tracking and calculate phase durations."""
        if new_state is None:
            return
            
        if self.current_state != new_state:
            # State changed
            if self.current_state and self.state_start_time:
                # Record duration of previous state
                duration = (datetime.now() - self.state_start_time).total_seconds()
                self.phase_durations[self.current_state].append(duration)
                
                # Keep only last 20 durations
                if len(self.phase_durations[self.current_state]) > 20:
                    self.phase_durations[self.current_state].pop(0)
            
            # Update to new state
            self.current_state = new_state
            self.state_start_time = datetime.now()
            
            # Record in history
            self.state_history.append({
                'state': new_state,
                'timestamp': timestamp
            })
    
    def _calculate_cycle_time(self) -> float:
        """Calculate average cycle time from recorded phase durations."""
        total_durations = []
        for color in ['red', 'yellow', 'green']:
            if self.phase_durations[color]:
                avg = sum(self.phase_durations[color]) / len(self.phase_durations[color])
                total_durations.append(avg)
        
        if len(total_durations) == 3:
            return round(sum(total_durations), 1)
        return 0
    
    def draw_detections(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """Draw detection results on frame."""
        output = frame.copy()
        
        # Draw detection region
        if self.detection_region:
            x, y, w, h = self.detection_region
            cv2.rectangle(output, (x, y), (x+w, y+h), (255, 255, 255), 2)
        
        # Draw detected circles
        colors_bgr = {
            'red': (0, 0, 255),
            'yellow': (0, 255, 255),
            'green': (0, 255, 0)
        }
        
        for color, detection in result['detections'].items():
            if detection['detected']:
                for x, y, r in detection['circles']:
                    if self.detection_region:
                        x += self.detection_region[0]
                        y += self.detection_region[1]
                    cv2.circle(output, (x, y), r, colors_bgr[color], 3)
                    cv2.circle(output, (x, y), 2, colors_bgr[color], 3)
        
        # Draw status overlay
        state = result['signal_state'] or 'unknown'
        confidence = result['confidence']
        phase_duration = result['phase_duration']
        
        # Background for text
        cv2.rectangle(output, (10, 10), (300, 120), (0, 0, 0), -1)
        cv2.rectangle(output, (10, 10), (300, 120), (255, 255, 255), 2)
        
        # Signal state
        state_color = colors_bgr.get(state, (128, 128, 128))
        cv2.putText(output, f"Signal: {state.upper()}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, state_color, 2)
        
        # Confidence
        cv2.putText(output, f"Confidence: {confidence:.0%}", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Phase duration
        cv2.putText(output, f"Duration: {phase_duration:.1f}s", (20, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return output
    
    def export_data(self, filepath: str):
        """Export timing data to JSON file."""
        data = {
            'export_time': datetime.now().isoformat(),
            'phase_durations': {
                color: {
                    'recordings': durations,
                    'average': sum(durations) / len(durations) if durations else 0,
                    'min': min(durations) if durations else 0,
                    'max': max(durations) if durations else 0
                }
                for color, durations in self.phase_durations.items()
            },
            'cycle_time': self._calculate_cycle_time(),
            'state_history': list(self.state_history)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    
    def calibrate_colors(self, frame: np.ndarray) -> Dict:
        """
        Helper function to calibrate HSV ranges.
        Returns current HSV values at center of frame.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = hsv.shape[:2]
        center_region = hsv[h//2-10:h//2+10, w//2-10:w//2+10]
        
        return {
            'h_mean': int(np.mean(center_region[:, :, 0])),
            'h_std': int(np.std(center_region[:, :, 0])),
            's_mean': int(np.mean(center_region[:, :, 1])),
            's_std': int(np.std(center_region[:, :, 1])),
            'v_mean': int(np.mean(center_region[:, :, 2])),
            'v_std': int(np.std(center_region[:, :, 2]))
        }
