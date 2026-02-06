"""
Vehicle Detector using YOLOv8
Detects vehicles, counts by lane, calculates queue length and speed
"""

import cv2
import numpy as np
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import json
import time

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARNING] ultralytics not installed. Using mock detections. Install with: pip install ultralytics")


class VehicleDetector:
    """
    Detects and tracks vehicles using YOLOv8.
    Provides counting, queue length, and speed estimation.
    """
    
    # COCO class IDs for vehicles
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck',
        1: 'bicycle'
    }
    
    def __init__(self, model_path: str = 'yolov8n.pt', config: Optional[Dict] = None):
        """
        Initialize the vehicle detector.
        
        Args:
            model_path: Path to YOLOv8 model (will download if not exists)
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.model_path = model_path
        self.model = None
        
        # Detection parameters
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.iou_threshold = self.config.get('iou_threshold', 0.45)
        self.img_size = self.config.get('img_size', 640)
        
        # Lane definitions (can be configured)
        # Each lane is defined by a polygon: [(x1,y1), (x2,y2), ...]
        self.lanes = self.config.get('lanes', {
            'north': None,
            'south': None,
            'east': None,
            'west': None
        })
        
        # Tracking for speed estimation
        self.prev_detections = {}
        self.prev_time = None
        self.track_history = defaultdict(lambda: deque(maxlen=30))
        
        # Statistics
        self.frame_count = 0
        self.total_vehicles_detected = 0
        self.detection_history = deque(maxlen=100)
        
        # Speed estimation parameters
        self.pixels_per_meter = self.config.get('pixels_per_meter', 10)  # Calibrate this
        self.stopped_threshold = self.config.get('stopped_threshold', 2.0)  # m/s
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 model."""
        if not YOLO_AVAILABLE:
            print("[WARNING] YOLOv8 not available. Using mock detections.")
            return
            
        try:
            self.model = YOLO(self.model_path)
            print(f"[OK] YOLOv8 model loaded: {self.model_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            self.model = None
    
    def detect(self, frame: np.ndarray) -> Dict:
        """
        Detect vehicles in a frame.
        
        Args:
            frame: BGR image frame from camera
            
        Returns:
            Dictionary with detection results
        """
        timestamp = datetime.now().isoformat()
        current_time = time.time()
        self.frame_count += 1
        
        # Run detection
        if self.model:
            detections = self._run_yolo(frame)
        else:
            detections = self._mock_detections(frame)
        
        # Filter for vehicles only
        vehicles = [d for d in detections if d['class_id'] in self.VEHICLE_CLASSES]
        
        # Assign to lanes
        lane_data = self._assign_to_lanes(vehicles, frame.shape)
        
        # Calculate speeds
        speeds = self._calculate_speeds(vehicles, current_time)
        
        # Calculate queue lengths (stopped vehicles)
        queue_lengths = self._calculate_queue_lengths(lane_data, speeds)
        
        # Count by vehicle type
        vehicle_types = self._count_vehicle_types(vehicles)
        
        # Update tracking
        self._update_tracking(vehicles, current_time)
        
        result = {
            'timestamp': timestamp,
            'frame_number': self.frame_count,
            'total_vehicles': len(vehicles),
            'lanes': {
                lane: {
                    'vehicle_count': len(data),
                    'queue_length': queue_lengths.get(lane, 0),
                    'avg_speed': self._avg_speed_for_lane(data, speeds),
                    'vehicles': data
                }
                for lane, data in lane_data.items()
            },
            'vehicle_types': vehicle_types,
            'all_detections': vehicles,
            'processing_fps': self._calculate_fps(current_time)
        }
        
        self.detection_history.append(result)
        self.total_vehicles_detected += len(vehicles)
        self.prev_time = current_time
        
        return result
    
    def _run_yolo(self, frame: np.ndarray) -> List[Dict]:
        """Run YOLOv8 inference."""
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.img_size,
            verbose=False
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    detections.append({
                        'id': i,
                        'class_id': cls,
                        'class_name': self.VEHICLE_CLASSES.get(cls, 'unknown'),
                        'confidence': round(conf, 2),
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'center': [int((x1+x2)/2), int((y1+y2)/2)]
                    })
        
        return detections
    
    def _mock_detections(self, frame: np.ndarray) -> List[Dict]:
        """Generate mock detections when YOLO is not available."""
        h, w = frame.shape[:2]
        num_vehicles = np.random.randint(5, 20)
        
        detections = []
        for i in range(num_vehicles):
            x1 = np.random.randint(0, w - 100)
            y1 = np.random.randint(0, h - 100)
            x2 = x1 + np.random.randint(50, 100)
            y2 = y1 + np.random.randint(50, 100)
            
            cls = np.random.choice(list(self.VEHICLE_CLASSES.keys()))
            
            detections.append({
                'id': i,
                'class_id': cls,
                'class_name': self.VEHICLE_CLASSES[cls],
                'confidence': round(np.random.uniform(0.5, 0.99), 2),
                'bbox': [x1, y1, x2, y2],
                'center': [(x1+x2)//2, (y1+y2)//2]
            })
        
        return detections
    
    def _assign_to_lanes(self, vehicles: List[Dict], frame_shape: Tuple) -> Dict[str, List]:
        """Assign vehicles to lanes based on position."""
        h, w = frame_shape[:2]
        
        # Default lane regions if not configured
        if not any(self.lanes.values()):
            # Divide frame into quadrants
            self.lanes = {
                'north': [(0, 0), (w, 0), (w, h//2), (0, h//2)],
                'south': [(0, h//2), (w, h//2), (w, h), (0, h)],
                'east': [(w//2, 0), (w, 0), (w, h), (w//2, h)],
                'west': [(0, 0), (w//2, 0), (w//2, h), (0, h)]
            }
        
        lane_data = {lane: [] for lane in self.lanes}
        
        for vehicle in vehicles:
            cx, cy = vehicle['center']
            
            for lane_name, polygon in self.lanes.items():
                if polygon and self._point_in_polygon(cx, cy, polygon):
                    lane_data[lane_name].append(vehicle)
                    break
        
        return lane_data
    
    def _point_in_polygon(self, x: int, y: int, polygon: List[Tuple]) -> bool:
        """Check if point is inside polygon using ray casting."""
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def _calculate_speeds(self, vehicles: List[Dict], current_time: float) -> Dict[int, float]:
        """Calculate speed for each vehicle using frame-to-frame tracking."""
        speeds = {}
        
        if self.prev_time is None:
            return speeds
        
        dt = current_time - self.prev_time
        if dt <= 0:
            return speeds
        
        for vehicle in vehicles:
            vid = vehicle['id']
            cx, cy = vehicle['center']
            
            if vid in self.prev_detections:
                prev_cx, prev_cy = self.prev_detections[vid]
                
                # Calculate displacement in pixels
                dx = cx - prev_cx
                dy = cy - prev_cy
                distance_px = np.sqrt(dx**2 + dy**2)
                
                # Convert to meters
                distance_m = distance_px / self.pixels_per_meter
                
                # Speed in m/s
                speed = distance_m / dt
                speeds[vid] = round(speed, 2)
        
        return speeds
    
    def _calculate_queue_lengths(self, lane_data: Dict, speeds: Dict) -> Dict[str, int]:
        """Calculate number of stopped vehicles per lane."""
        queue_lengths = {}
        
        for lane, vehicles in lane_data.items():
            stopped = 0
            for vehicle in vehicles:
                vid = vehicle['id']
                speed = speeds.get(vid, 0)
                if speed < self.stopped_threshold:
                    stopped += 1
            queue_lengths[lane] = stopped
        
        return queue_lengths
    
    def _avg_speed_for_lane(self, vehicles: List[Dict], speeds: Dict) -> float:
        """Calculate average speed for vehicles in a lane."""
        lane_speeds = [speeds.get(v['id'], 0) for v in vehicles]
        if lane_speeds:
            return round(sum(lane_speeds) / len(lane_speeds), 2)
        return 0.0
    
    def _count_vehicle_types(self, vehicles: List[Dict]) -> Dict[str, int]:
        """Count vehicles by type."""
        counts = defaultdict(int)
        for vehicle in vehicles:
            counts[vehicle['class_name']] += 1
        return dict(counts)
    
    def _update_tracking(self, vehicles: List[Dict], current_time: float):
        """Update tracking history."""
        self.prev_detections = {
            v['id']: v['center'] for v in vehicles
        }
        
        for vehicle in vehicles:
            vid = vehicle['id']
            self.track_history[vid].append(vehicle['center'])
    
    def _calculate_fps(self, current_time: float) -> float:
        """Calculate processing FPS."""
        if self.prev_time:
            return round(1.0 / max(current_time - self.prev_time, 0.001), 1)
        return 0.0
    
    def draw_detections(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """Draw detection results on frame."""
        output = frame.copy()
        
        # Colors for vehicle types
        colors = {
            'car': (0, 255, 0),
            'truck': (0, 165, 255),
            'bus': (255, 165, 0),
            'motorcycle': (255, 0, 255),
            'bicycle': (255, 255, 0)
        }
        
        # Draw bounding boxes
        for vehicle in result['all_detections']:
            x1, y1, x2, y2 = vehicle['bbox']
            color = colors.get(vehicle['class_name'], (128, 128, 128))
            
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            label = f"{vehicle['class_name']} {vehicle['confidence']:.0%}"
            cv2.putText(output, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw lane boundaries (if defined)
        for lane_name, polygon in self.lanes.items():
            if polygon:
                pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
                cv2.polylines(output, [pts], True, (255, 255, 255), 1)
        
        # Draw statistics overlay
        h = frame.shape[0]
        cv2.rectangle(output, (10, h-150), (250, h-10), (0, 0, 0), -1)
        cv2.rectangle(output, (10, h-150), (250, h-10), (255, 255, 255), 2)
        
        cv2.putText(output, f"Total Vehicles: {result['total_vehicles']}", 
                   (20, h-120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(output, f"FPS: {result['processing_fps']}", 
                   (20, h-90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Lane stats
        y_offset = h - 60
        for lane, data in result['lanes'].items():
            if data['vehicle_count'] > 0:
                text = f"{lane}: {data['vehicle_count']} ({data['queue_length']} stopped)"
                cv2.putText(output, text, (20, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 20
        
        return output
    
    def export_data(self, filepath: str):
        """Export detection history to JSON file."""
        data = {
            'export_time': datetime.now().isoformat(),
            'total_frames': self.frame_count,
            'total_vehicles_detected': self.total_vehicles_detected,
            'detection_history': list(self.detection_history)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return data
    
    def get_rl_state(self) -> Dict:
        """
        Convert detection data to RL environment state format.
        Compatible with existing UrbanFlow RL training.
        """
        if not self.detection_history:
            return None
            
        latest = self.detection_history[-1]
        
        state = {
            'timestamp': latest['timestamp'],
            'queue_length_north': latest['lanes'].get('north', {}).get('queue_length', 0),
            'queue_length_south': latest['lanes'].get('south', {}).get('queue_length', 0),
            'queue_length_east': latest['lanes'].get('east', {}).get('queue_length', 0),
            'queue_length_west': latest['lanes'].get('west', {}).get('queue_length', 0),
            'vehicle_count_north': latest['lanes'].get('north', {}).get('vehicle_count', 0),
            'vehicle_count_south': latest['lanes'].get('south', {}).get('vehicle_count', 0),
            'vehicle_count_east': latest['lanes'].get('east', {}).get('vehicle_count', 0),
            'vehicle_count_west': latest['lanes'].get('west', {}).get('vehicle_count', 0),
            'avg_speed_north': latest['lanes'].get('north', {}).get('avg_speed', 0),
            'avg_speed_south': latest['lanes'].get('south', {}).get('avg_speed', 0),
            'avg_speed_east': latest['lanes'].get('east', {}).get('avg_speed', 0),
            'avg_speed_west': latest['lanes'].get('west', {}).get('avg_speed', 0),
            'total_vehicles': latest['total_vehicles']
        }
        
        return state
