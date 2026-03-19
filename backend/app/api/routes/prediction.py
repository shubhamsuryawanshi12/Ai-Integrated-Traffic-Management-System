from fastapi import APIRouter
from app.services.ai_engine.traffic_predictor import traffic_predictor

router = APIRouter()

@router.get("/forecast")
async def get_traffic_forecast():
    """Returns a 24-hour hybrid Prophet+LSTM traffic flow forecast."""
    prediction = traffic_predictor.generate_forecast()
    return {
        "status": "success",
        "model": "Prophet+LSTM Hybrid",
        "forecast": prediction
    }
