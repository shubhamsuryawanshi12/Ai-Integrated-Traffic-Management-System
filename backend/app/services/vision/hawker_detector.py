import cv2
import numpy as np
from collections import deque
import time

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

class HawkerDetector:
    def __init__(self, model_path="yolov8n.pt"):
        self.enabled = YOLO_AVAILABLE
        if self.enabled:
            # We assume model is loaded in memory elsewhere, or we load it here
            # Since mobile_camera_server already loads YOLO, we can just pass detections
            pass
            
        # Track objects across frames: id -> [(cx, cy, timestamp), ...]
        self.tracked_objects = {}
        # Simple ID counter for basic tracking logic
        self.next_id = 0
        
        # Keep track of recent alerts to avoid spamming
        self.last_alert_time = 0
        self.cooldown_seconds = 5.0
        
        # Target classes: person (0), bicycle (1), motorcycle (3), truck (7)
        self.target_classes = [0, 1, 3, 7]
        
    def detect(self, frame_shape, detections):
        """
        frame_shape: (height, width, channels)
        detections: list of dicts [{'class': int, 'bbox': [x1,y1,x2,y2], 'conf': float}]
        """
        if not detections:
            return {"detected": False, "severity": None, "object_count": 0, "blocked_percentage": 0.0, "alert_message": ""}

        height, width = frame_shape[:2]
        
        # Define lane area (middle 60% of frame width)
        lane_x1 = int(width * 0.2)
        lane_x2 = int(width * 0.8)
        lane_width = lane_x2 - lane_x1
        
        current_time = time.time()
        current_objects = []
        
        # Filter detections to targets inside lane
        lane_objects = []
        for det in detections:
            cls = int(det.get("class", -1))
            if cls not in self.target_classes:
                continue
                
            x1, y1, x2, y2 = det.get("bbox", [0,0,0,0])
            cx = (x1 + x2) / 2
            
            # Check if in center lane (ignoring sidewalks)
            if lane_x1 <= cx <= lane_x2:
                lane_objects.append(det)
                
        # Basic stationarity logic (simplified for hackathon demo)
        # We just count how many target objects are in the lane.
        # If there's a lot, we say there's a hawker/obstruction.
        obj_count = len(lane_objects)
        
        if obj_count == 0:
             return {"detected": False, "severity": None, "object_count": 0, "blocked_percentage": 0.0, "alert_message": ""}
        
        # Estimate blocked width (union of bounding boxes horizontally)
        blocked_segments = []
        for obj in lane_objects:
            x1, y1, x2, y2 = obj['bbox']
            # clip to lane
            bx1 = max(lane_x1, x1)
            bx2 = min(lane_x2, x2)
            if bx1 < bx2:
                blocked_segments.append((bx1, bx2))
                
        # Merge overlapping segments
        blocked_segments.sort()
        merged = []
        for seg in blocked_segments:
            if not merged:
                merged.append(seg)
            else:
                last_start, last_end = merged[-1]
                if seg[0] <= last_end:
                    merged[-1] = (last_start, max(last_end, seg[1]))
                else:
                    merged.append(seg)
                    
        total_blocked_width = sum([end - start for start, end in merged])
        blocked_percentage = total_blocked_width / float(lane_width) if lane_width > 0 else 0
        
        # Classify Severity
        severity = None
        if blocked_percentage > 0.4:
            severity = "HIGH"
        elif blocked_percentage > 0.2:
            severity = "MEDIUM"
        elif blocked_percentage > 0.1:
            severity = "LOW"
            
        if severity:
            msg = f"Obstruction detected: {int(blocked_percentage*100)}% lane blocked."
            if severity == "HIGH":
                msg = f"CRITICAL OBSTRUCTION: Lane severely blocked ({int(blocked_percentage*100)}%)."
            return {
                "detected": True,
                "severity": severity,
                "object_count": obj_count,
                "blocked_percentage": float(blocked_percentage),
                "alert_message": msg
            }
            
        return {"detected": False, "severity": None, "object_count": obj_count, "blocked_percentage": float(blocked_percentage), "alert_message": ""}
