from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class ParkingArea(BaseModel):
    id: str = str(uuid.uuid4())
    owner_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    price_per_hour: float
    total_slots: int
    available_slots: int          # must always be >= 0
    approved: bool = False
    created_at: datetime = datetime.utcnow()

class Booking(BaseModel):
    id: str = str(uuid.uuid4())
    user_id: str
    parking_id: str
    start_time: datetime
    end_time: datetime
    total_amount: float
    commission_amount: float
    owner_amount: float
    status: str                   # "pending" | "confirmed" | "cancelled" | "completed"

class Payment(BaseModel):
    id: str = str(uuid.uuid4())
    booking_id: str
    amount: float
    commission: float
    owner_amount: float
    payment_status: str           # "pending" | "paid" | "failed"

class Commission(BaseModel):
    id: str = "global"
    percentage: float = 10.0      # default 10%

class User(BaseModel):
    id: str = str(uuid.uuid4())
    name: str
    email: str
    phone: Optional[str] = None
    role: str                     # "driver" | "owner" | "admin"
    created_at: datetime = datetime.utcnow()

from app.models.parking_category import CategorySlotConfig, VehicleCategory
from typing import List, Dict
from datetime import time

class ParkingLotV2(BaseModel):
    lot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    lot_name: str
    address: str
    city: str
    google_maps_link: Optional[str] = None
    landmark: Optional[str] = None
    total_capacity: int
    is_covered: bool = False
    is_24x7: bool = False
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    approved: bool = False

    # Core upgrade: per-category slot configuration
    categories: List[CategorySlotConfig]

    @property
    def total_defined_slots(self) -> int:
        return sum(c.total_slots for c in self.categories)

    @property
    def total_available_slots(self) -> int:
        return sum(c.available_slots for c in self.categories)

    @property
    def occupancy_by_category(self) -> Dict[str, dict]:
        return {
            c.category: {
                "total": c.total_slots,
                "available": c.available_slots,
                "occupied": c.total_slots - c.available_slots,
                "occupancy_pct": round(
                    (c.total_slots - c.available_slots) / c.total_slots * 100, 1
                ) if c.total_slots > 0 else 0
            }
            for c in self.categories
        }
