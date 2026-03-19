from fastapi import APIRouter, HTTPException, Depends
from app.models.owner import ParkingOwner, OwnerProfileUpdate
from app.models.parking_models import ParkingLotV2
from typing import List, Optional
import uuid

router = APIRouter(prefix="/owner", tags=["Owner Auth"])

# In-memory stores for hackathon (mimicking production database)
_OWNERS_DB = {}
_LOTS_DB = {}

@router.post("/register")
async def register_owner(owner_data: ParkingOwner, lot_data: ParkingLotV2):
    """
    Registers a new parking owner and their associated lot with category configurations.
    """
    if owner_data.email in _OWNERS_DB:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Associate lot and owner
    owner_id = str(uuid.uuid4())
    lot_id = f"LOT_{str(uuid.uuid4())[:8].upper()}"
    
    owner_data.id = owner_id
    owner_data.lot_id = lot_id
    
    lot_data.lot_id = lot_id
    lot_data.owner_id = owner_id
    
    _OWNERS_DB[owner_data.email] = {
        "owner": owner_data,
        "password": "hashed_password_placeholder" # In real app, hash password
    }
    _LOTS_DB[lot_id] = lot_data
    
    return {
        "status": "success",
        "owner_id": owner_id,
        "lot_id": lot_id,
        "message": "Registration successful. Welcome to UrbanFlow v2.0!"
    }

@router.post("/login")
async def login_owner(login_payload: dict):
    """
    Login endpoint for Owner / Manager / Staff roles.
    """
    email = login_payload.get("email")
    password = login_payload.get("password")
    role = login_payload.get("role", "owner")
    
    if email not in _OWNERS_DB:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Validation logic placeholder
    owner_data = _OWNERS_DB[email]["owner"]
    
    # In v2.0 we support multi-role login
    return {
        "access_token": f"mock_jwt_token_{uuid.uuid4()}",
        "token_type": "bearer",
        "user": {
            "id": owner_data.id,
            "name": owner_data.name,
            "email": owner_data.email,
            "role": role,
            "lot_id": owner_data.lot_id,
            "business_name": owner_data.business_name
        }
    }

@router.get("/profile/{owner_id}")
async def get_owner_profile(owner_id: str):
    """Get profile and lot status."""
    for email, data in _OWNERS_DB.items():
        if data["owner"].id == owner_id:
            owner = data["owner"]
            lot = _LOTS_DB.get(owner.lot_id)
            return {
                "owner": owner,
                "lot": lot
            }
    raise HTTPException(status_code=404, detail="Owner not found")
