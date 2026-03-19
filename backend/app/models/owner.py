from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

class OwnerRole(str):
    OWNER   = "owner"
    MANAGER = "manager"
    STAFF   = "staff"

class ParkingOwner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    business_name: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    role: str = "owner"  # owner|manager|staff
    lot_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OwnerProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    business_name: Optional[str] = None
    gst_number: Optional[str] = None
