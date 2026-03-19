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
