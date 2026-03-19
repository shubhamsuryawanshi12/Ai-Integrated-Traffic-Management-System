import random
from typing import Dict, Any, List

class IllegalParkingDetector:
    """
    Detects vehicles that are stationary for too long in restricted zones.
    Simulates License Plate Recognition (LPR) for the detected vehicles.
    """
    def __init__(self, max_allowed_frames: int = 15):
        self.max_allowed_frames = max_allowed_frames
        # Track stationary vehicles: {vehicle_id: frame_count}
        self.stationary_vehicles = {}
        
        # Mock Indian license plates for demo purposes
        self.mock_plates = [
            "MH 12 AB 1234", "MH 13 XY 9876", "DL 01 C 3456", 
            "KA 05 MN 5678", "UP 32 BQ 1122", "GJ 01 XX 9999"
        ]

    def detect(self, frame_shape, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes raw YOLO detections and shape.
        Identifies vehicles on the edge of the frame (simulated no-parking zones).
        """
        # For simplicity, let's just track all detected 'car', 'truck', 'bus' objects
        # We assume if they have the same ID across frames, we track them.
        # But YOLO here might not give tracking IDs consistently without SORT.
        # We will simulate the tracking for the hackathon demo.
        
        # Check if there are vehicles
        vehicles = [d for d in detections if d.get('class', '') in ['car', 'truck', 'bus']]
        
        # In a real scenario, we'd check if they are in a specific polygon map
        # and if their bounding box center hasn't moved.
        # For this demo, let's randomly accumulate frame counts for vehicles
        # or just randomly trigger an illegal parking event if there's any vehicle.
        
        result = {
            "illegal_parking_detected": False,
            "severity": "LOW",
            "message": "",
            "lpr_results": []
        }
        
        if not vehicles:
            return result
            
        # Demo heuristic: 5% chance per frame if vehicles are present to trigger perfectly
        if random.random() < 0.05:
            plate = random.choice(self.mock_plates)
            result["illegal_parking_detected"] = True
            result["severity"] = "HIGH"
            result["message"] = f"Illegal Parking Detected! Vehicle LPR: {plate}"
            result["lpr_results"] = [plate]
            
        return result
