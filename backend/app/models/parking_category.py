from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, time

class VehicleCategory(str, Enum):
    TWO_WHEELER           = "2w"           # Bike / Scooter (petrol)
    TWO_WHEELER_EV        = "2w_ev"        # Electric scooter / bike
    FOUR_WHEELER_COMPACT  = "4w_compact"   # Hatchback / small car  (< 4.0 m)
    FOUR_WHEELER_MIDSIZE  = "4w_midsize"   # Sedan / compact SUV (4.0–4.5 m)
    FOUR_WHEELER_LARGE    = "4w_large"     # Full-size SUV / MUV (4.5–5.0 m)
    FOUR_WHEELER_XL       = "4w_xl"        # Luxury / premium SUV (> 5.0 m)
    FOUR_WHEELER_EV       = "4w_ev"        # Any 4W electric (needs charger)

class SlotStatus(str, Enum):
    AVAILABLE   = "available"
    OCCUPIED    = "occupied"
    RESERVED    = "reserved"
    MAINTENANCE = "maintenance"

class CategorySlotConfig(BaseModel):
    category: VehicleCategory
    total_slots: int = Field(..., ge=1)
    available_slots: int
    reserved_slots: int = 0
    has_ev_charging: bool = False

    # Physical slot dimensions in metres
    slot_width_m: float
    slot_length_m: float

    # Pricing
    price_per_hour: float = Field(..., ge=0)
    price_first_hour: Optional[float] = None   # Special rate for first hour
    daily_cap: Optional[float] = None          # Maximum charge per day
    overnight_flat: Optional[float] = None     # Flat rate 10 PM – 6 AM
    ev_charging_per_hour: Optional[float] = None  # Only if has_ev_charging

    class Config:
        json_schema_extra = {
            "example": {
                "category": "4w_large",
                "total_slots": 15,
                "available_slots": 11,
                "has_ev_charging": False,
                "slot_width_m": 2.8,
                "slot_length_m": 5.5,
                "price_per_hour": 40.0,
                "price_first_hour": 60.0,
                "daily_cap": 500.0,
                "overnight_flat": 150.0
            }
        }

class ParkingSlot(BaseModel):
    slot_id: str                         # e.g. "LOT042-4L-007"
    lot_id: str
    category: VehicleCategory
    row: Optional[str] = None            # e.g. "H" from layout map
    column: Optional[int] = None         # e.g. 7 from layout map
    status: SlotStatus = SlotStatus.AVAILABLE
    current_booking_id: Optional[str] = None
    has_ev_charger: bool = False
    charger_type: Optional[str] = None   # "AC_SLOW" | "DC_FAST"
