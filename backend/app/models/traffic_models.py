from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TrafficData(BaseModel):
    intersection_id: str
    vehicle_count: int
    queue_length: int
    average_wait_time: float
    timestamp: datetime = datetime.now()

class SignalState(BaseModel):
    intersection_id: str
    phase: str  # "red", "yellow", "green"
    duration: int

class IntersectionStatus(BaseModel):
    id: str
    name: str
    current_status: SignalState
    traffic_data: TrafficData
