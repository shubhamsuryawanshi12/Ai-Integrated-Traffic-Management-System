from fastapi import APIRouter, HTTPException
from typing import List
from app.models.traffic_models import IntersectionStatus, TrafficData, SignalState
from datetime import datetime

router = APIRouter()

# Mock Database/State
intersections = {
    "int_1": {
        "id": "int_1",
        "name": "Main St & 1st Ave",
        "current_status": {"intersection_id": "int_1", "phase": "green", "duration": 30},
        "traffic_data": {"intersection_id": "int_1", "vehicle_count": 15, "queue_length": 3, "average_wait_time": 12.5}
    }
}

@router.get("/", response_model=List[IntersectionStatus])
async def get_all_intersections():
    """Get status of all intersections"""
    return list(intersections.values())

@router.get("/{intersection_id}", response_model=IntersectionStatus)
async def get_intersection_status(intersection_id: str):
    """Get specific intersection status"""
    if intersection_id not in intersections:
        raise HTTPException(status_code=404, detail="Intersection not found")
    return intersections[intersection_id]

@router.post("/{intersection_id}/control", response_model=SignalState)
async def update_signal(intersection_id: str, state: SignalState):
    """Manual override or AI control signal change"""
    if intersection_id not in intersections:
        raise HTTPException(status_code=404, detail="Intersection not found")
    
    # Update state logic here
    intersections[intersection_id]["current_status"] = state.dict()
    return state
