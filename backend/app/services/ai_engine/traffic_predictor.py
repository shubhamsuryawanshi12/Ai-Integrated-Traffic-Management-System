import datetime
import math
import random
from typing import List, Dict

class TrafficPredictor:
    """
    Traffic Flow Predictor.
    For the hackathon demo, this simulates a hybrid Prophet + LSTM model output 
    to forecast traffic volume and wait times over the next 24 hours.
    """
    def __init__(self):
        # Base daily curve: peak at 9 AM and 6 PM
        self.peak_hours = [9, 18]
        
    def generate_forecast(self, current_time=None) -> List[Dict]:
        if current_time is None:
            current_time = datetime.datetime.now()
            
        forecast = []
        for i in range(24): # Next 24 hours
            forecast_time = current_time + datetime.timedelta(hours=i)
            hour = forecast_time.hour
            
            # Simulated cyclical patterns (bimodal for morning and evening limits)
            base_volume = 100
            if 7 <= hour <= 10:
                base_volume += 150 * math.sin((hour - 7) * math.pi / 3)
            elif 16 <= hour <= 20:
                base_volume += 180 * math.sin((hour - 16) * math.pi / 4)
            else:
                base_volume += 50 * math.cos(hour * math.pi / 12) + 50
                
            # Add some LSTM "noise" / micro-variations
            volume = max(20, int(base_volume + random.uniform(-15, 15)))
            
            # Projected wait times (baseline vs AI)
            # Baseline is roughly proportional to volume * 1.5
            baseline_wait = max(30, int(volume * 1.5 + random.uniform(-10, 20)))
            
            # AI (A3C + Route Optimization) is significantly lower, caps out earlier
            ai_wait = max(15, int(volume * 0.5 + random.uniform(-5, 10)))
            
            forecast.append({
                "time": forecast_time.strftime("%H:00"),
                "predicted_volume": volume,
                "baseline_wait_sec": baseline_wait,
                "ai_wait_sec": ai_wait,
                "confidence_score": round(random.uniform(0.85, 0.98), 2)
            })
            
        return forecast

traffic_predictor = TrafficPredictor()
