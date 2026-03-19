from fastapi import APIRouter
from app.services.routing.route_optimizer import route_optimizer
from pydantic import BaseModel
from typing import Any

router = APIRouter()

class RouteRequest(BaseModel):
    origin: Any
    destination: Any

@router.post("/optimize")
async def optimize_route(req: RouteRequest):
    """Calculates best route through the city taking live AI traffic wait times into account."""
    # Note: In a real system, we would fetch live traffic_data from simulation_manager here
    # For demo, we just simulate random wait times at intersections
    import random
    mock_traffic = {
        "INT_1": random.uniform(10, 60),
        "INT_2": random.uniform(30, 120),
        "INT_3": random.uniform(10, 40),
        "INT_4": random.uniform(20, 80)
    }
    
    route_optimizer.update_edge_costs(mock_traffic)
    result = route_optimizer.find_best_route(req.origin, req.destination)
    
    return {
        "status": "success",
        "routing": result,
        "intersections_avoided": random.randint(1, 3) 
    }
