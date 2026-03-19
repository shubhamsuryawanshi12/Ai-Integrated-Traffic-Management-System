import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List, Dict

class AnomalyDetector:
    """
    Detects traffic anomalies (accidents, broken lights, extreme congestion) 
    in real-time using an Isolation Tree Forest model.
    """
    def __init__(self):
        # We pre-train or initialize a generic IsolationForest
        self.clf = IsolationForest(contamination=0.05, random_state=42)
        # We will keep a moving window of data to refit or predict upon
        self.history = []
        
        # A simple synthetic training baseline: [wait_time, vehicle_count, avg_speed]
        baseline_data = [
            [20.0, 10, 12.0],
            [15.0, 15, 11.0],
            [40.0, 25, 8.0],
            [10.0, 5, 15.0],
            [30.0, 20, 10.0],
            [25.0, 18, 9.5],
        ]
        X = np.array(baseline_data)
        self.clf.fit(X)
        
    def detect_anomalies(self, intersections_data: List[Dict]) -> List[Dict]:
        anomalies = []
        for d in intersections_data:
            ts_id = d.get('id', 'Unknown')
            td = d.get('traffic_data', {})
            wait_time = float(td.get('average_wait_time', 0.0))
            veh_count = float(td.get('vehicle_count', 0.0))
            speed = float(td.get('avg_speed', 0.0))
            
            # Predict
            X_test = np.array([[wait_time, veh_count, speed]])
            pred = self.clf.predict(X_test)[0]
            
            # Additional heuristic rules for the demo
            # e.g., if wait time is massively high but speed is zero
            if pred == -1 or (wait_time > 150 and speed < 1.0):
                severity = "HIGH" if wait_time > 200 else "MEDIUM"
                anomalies.append({
                    "intersection_id": ts_id,
                    "type": "Traffic Anomaly",
                    "severity": severity,
                    "message": f"Anomalous traffic pattern at {ts_id}: {int(wait_time)}s wait, speed {speed:.1f}m/s",
                    "metrics": {
                        "wait_time": wait_time,
                        "vehicles": veh_count,
                        "speed": speed
                    }
                })
                
        return anomalies

anomaly_detector = AnomalyDetector()
