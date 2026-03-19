import os
import joblib
import pandas as pd
import numpy as np

try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("WARNING: xgboost not installed. Occupancy predictor will return mock values.")

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'parking_model.pkl')

class OccupancyPredictor:
    def __init__(self):
        self.model = None
        # Zone type mapping for encoding
        self.zone_type_map = {
            "transit": 0,
            "landmark": 1,
            "commercial": 2
        }
        self.load_or_train_model()

    def generate_synthetic_data(self, n_samples=2000):
        """Generate synthetic parking data for Solapur."""
        np.random.seed(42)
        
        # Features: [hour_of_day, day_of_week, is_festival, is_rain, zone_type_encoded]
        hours = np.random.randint(0, 24, n_samples)
        days = np.random.randint(0, 7, n_samples)
        festivals = np.random.choice([0, 1], n_samples, p=[0.95, 0.05])
        rains = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
        zone_types = np.random.choice([0, 1, 2], n_samples)
        
        # Calculate target: occupancy_percentage
        occupancy = np.zeros(n_samples)
        
        for i in range(n_samples):
            base_occ = 0.3
            
            # Peak hours (9-11 AM, 5-8 PM)
            if 9 <= hours[i] <= 11 or 17 <= hours[i] <= 20:
                base_occ += 0.4
                
            # Weakends
            if days[i] >= 5:
                if zone_types[i] == 2:  # Commercial busy on weekends
                    base_occ += 0.2
                elif zone_types[i] == 1:  # Landmarks busy on weekends
                    base_occ += 0.3
                    
            # Festivals
            if festivals[i]:
                base_occ += 0.3
                
            # Rain (less people go out)
            if rains[i]:
                base_occ -= 0.15
                
            # Thursday Local Bazaar
            if days[i] == 3 and zone_types[i] == 2:
                base_occ += 0.2
                
            # Add some noise
            base_occ += np.random.normal(0, 0.05)
            
            # Clip between 0 and 1
            occupancy[i] = np.clip(base_occ, 0, 1)
            
        return pd.DataFrame({
            "hour_of_day": hours,
            "day_of_week": days,
            "is_festival": festivals,
            "is_rain": rains,
            "zone_type_encoded": zone_types,
            "occupancy_percentage": occupancy
        })

    def load_or_train_model(self):
        if not XGB_AVAILABLE:
            return
            
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                print("Loaded existing XGBoost parking predictor model.")
                return
            except Exception as e:
                print(f"Error loading model: {e}. Retraining...")

        print("Training new XGBoost parking predictor model...")
        df = self.generate_synthetic_data()
        X = df.drop("occupancy_percentage", axis=1)
        y = df["occupancy_percentage"]
        
        self.model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1)
        self.model.fit(X, y)
        
        # Save model
        joblib.dump(self.model, MODEL_PATH)
        print(f"Saved model to {MODEL_PATH}")

    def predict_occupancy(self, zone_type: str, hour: int, day: int, is_festival: int, is_rain: int) -> float:
        """Predict occupancy (0 to 1)."""
        if not self.model or not XGB_AVAILABLE:
            # Fallback simple heuristic
            base = 0.5
            if 9 <= hour <= 19: base += 0.3
            if is_festival: base += 0.2
            return min(1.0, max(0.0, base))
            
        zone_enc = self.zone_type_map.get(zone_type, 0)
        X_pred = pd.DataFrame([{
            "hour_of_day": hour,
            "day_of_week": day,
            "is_festival": is_festival,
            "is_rain": is_rain,
            "zone_type_encoded": zone_enc
        }])
        
        pred = self.model.predict(X_pred)[0]
        return float(np.clip(pred, 0, 1))

# Singleton instance
occupancy_predictor = OccupancyPredictor()
