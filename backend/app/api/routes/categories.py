from fastapi import APIRouter, HTTPException, Path, Body
from app.models.parking_category import VehicleCategory, CategorySlotConfig
from app.api.routes.owner_auth import _LOTS_DB
from typing import List, Dict
import datetime

router = APIRouter(prefix="/lot", tags=["Slot & Category Management"])

@router.get("/{lot_id}/categories")
async def get_all_categories(lot_id: str):
    """List all categories supported by the lot."""
    lot = _LOTS_DB.get(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")
    
    return {
        "lot_id": lot_id,
        "lot_name": lot.lot_name,
        "categories": lot.categories
    }

@router.put("/{lot_id}/categories/{category}")
async def update_category_config(
    lot_id: str, 
    category: VehicleCategory,
    update_data: CategorySlotConfig = Body(...)
):
    """Update slot count or pricing for a specific category."""
    lot = _LOTS_DB.get(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")
    
    for i, config in enumerate(lot.categories):
        if config.category == category:
            # Check availability (can't reduce below current bookings)
            if update_data.total_slots < (config.total_slots - config.available_slots):
                raise HTTPException(status_code=400, detail="Cannot reduce total slots below active bookings count")
            
            # Recalculate available_slots if total changed
            diff = update_data.total_slots - config.total_slots
            update_data.available_slots = config.available_slots + diff
            
            # Update
            lot.categories[i] = update_data
            return {
                "status": "updated",
                "category": category,
                "new_config": update_data
            }
            
    # If category doesn't exist, we add it
    lot.categories.append(update_data)
    return {"status": "added", "category": category, "config": update_data}

@router.get("/{lot_id}/availability")
async def get_full_availability(lot_id: str):
    """
    Returns a detailed snapshot of the lot's availability across ALL categories.
    Powers the v2.0 Owner Dashboard and Citizen search results.
    """
    lot = _LOTS_DB.get(lot_id)
    if not lot:
        # Fallback for mock lot
        return {
            "lot_id": lot_id,
            "lot_name": "Demo Parking Central",
            "total_capacity": 100,
            "total_available": 45,
            "categories": {
                "2w": {"total": 50, "available": 20, "price_per_hour": 10},
                "4w_compact": {"total": 30, "available": 15, "price_per_hour": 30},
                "4w_midsize": {"total": 10, "available": 5, "price_per_hour": 40},
                "4w_large": {"total": 5, "available": 3, "price_per_hour": 60},
                "4w_ev": {"total": 5, "available": 2, "price_per_hour": 50}
            }
        }
    
    return {
        "lot_id": lot.lot_id,
        "lot_name": lot.lot_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_capacity": lot.total_capacity,
        "total_available": lot.total_available_slots,
        "categories": {
            c.category: {
                "total": c.total_slots,
                "available": c.available_slots,
                "occupied": c.total_slots - c.available_slots,
                "occupancy_pct": round((c.total_slots - c.available_slots) / c.total_slots * 100, 1) if c.total_slots > 0 else 0,
                "price_per_hour": c.price_per_hour
            }
            for c in lot.categories
        }
    }
