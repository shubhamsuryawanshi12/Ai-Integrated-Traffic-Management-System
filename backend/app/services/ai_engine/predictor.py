import pandas as pd
from typing import List, Dict
import datetime

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("WARNING: Prophet not available. Traffic prediction will return empty results.")

class TrafficPredictor:
    def __init__(self):
        self.model = None
        self.is_fitted = False

    def train(self, historical_data: List[Dict]):
        """
        Train the Prophet model on historical data.
        historical_data: List of dicts with 'timestamp' and 'vehicle_count'
        """
        if not PROPHET_AVAILABLE:
            print("WARNING: Prophet not installed. Skipping training.")
            return

        df = pd.DataFrame(historical_data)
        if 'timestamp' not in df.columns or 'vehicle_count' not in df.columns:
            raise ValueError("Data must have 'timestamp' and 'vehicle_count' columns")
            
        df = df.rename(columns={'timestamp': 'ds', 'vehicle_count': 'y'})
        
        self.model = Prophet()
        self.model.fit(df)
        self.is_fitted = True

    def predict(self, periods: int = 60, freq: str = 'min') -> List[Dict]:
        """
        Predict future traffic.
        periods: Number of periods to predict
        freq: Frequency (e.g., 'min', 'H', 'D')
        """
        if not self.is_fitted or self.model is None:
            return []
            
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)
        
        # Return only future part
        future_forecast = forecast.tail(periods)
        
        result = []
        for _, row in future_forecast.iterrows():
            result.append({
                'timestamp': row['ds'],
                'predicted_vehicle_count': row['yhat'],
                'lower_bound': row['yhat_lower'],
                'upper_bound': row['yhat_upper']
            })
            
        return result
