from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from app.services.parking import parking_manager, parking_store

router = APIRouter()

# ── Zones ─────────────────────────────────────────────────────────────────────

@router.get("/zones")
def get_all_zones():
    """All approved parking zones. Frontend filters by distance client-side."""
    return parking_manager.get_all_approved_zones()

@router.get("/zones/{zone_id}")
def get_zone(zone_id: str):
    zone = parking_store.parking_areas.get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

@router.get("/zones/nearby")
def get_nearby(lat: float, lng: float, radius_km: float = 5.0):
    """
    Returns approved zones within radius_km sorted by distance.
    Frontend passes user's GPS coordinates.
    """
    return parking_manager.get_nearby_zones(lat, lng, radius_km)

@router.get("/predict/{zone_id}")
def predict_occupancy(zone_id: str, hour: int = 12):
    """
    XGBoost occupancy prediction.
    Returns predicted occupancy percentage for given hour.
    """
    zone = parking_store.parking_areas.get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    # Import from existing occupancy_predictor
    from app.services.parking.occupancy_predictor import occupancy_predictor
    
    now = datetime.now()
    day = now.weekday()
    
    # We pass the zone_type to the predictor 
    prediction = occupancy_predictor.predict_occupancy(
        zone_type=zone.get("type", "on-street"),
        hour=hour,
        day=day,
        is_festival=0,
        is_rain=0
    )
    return {"zone_id": zone_id, "hour": hour, "predicted_occupancy_percent": prediction}

# ── Bookings ───────────────────────────────────────────────────────────────────

class BookingRequest(BaseModel):
    user_id: str
    parking_id: str
    start_time: datetime
    end_time: datetime

@router.post("/book")
async def book_slot(req: BookingRequest):
    """
    Atomic booking. Equivalent to Supabase book_parking_slot RPC.
    Uses threading.Lock — no double booking possible.
    """
    result = parking_manager.book_parking_slot(
        user_id=req.user_id,
        parking_id=req.parking_id,
        start_time=req.start_time,
        end_time=req.end_time
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
        
    # Broadcast the parking update
    from app.core.socket_manager import broadcast_parking_update
    await broadcast_parking_update()
    
    return result

@router.get("/bookings/user/{user_id}")
def get_user_bookings(user_id: str):
    """Driver's booking history."""
    return [b for b in parking_store.bookings.values() if b["user_id"] == user_id]

@router.get("/bookings/owner/{owner_id}")
def get_owner_bookings(owner_id: str):
    """All bookings across owner's parking zones."""
    return parking_manager.get_owner_bookings(owner_id)

@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str):
    booking = parking_store.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")
    booking["status"] = "cancelled"
    parking_manager.release_slot(booking["parking_id"])
    
    # Broadcast the parking update
    from app.core.socket_manager import broadcast_parking_update
    await broadcast_parking_update()
    
    return {"success": True, "message": "Booking cancelled, slot released"}

# ── Payments ───────────────────────────────────────────────────────────────────

@router.post("/payments/{booking_id}/confirm")
def confirm_payment(booking_id: str):
    """
    Called after user completes payment (Razorpay callback or mock confirmation).
    Updates payment status to 'paid'.
    """
    payment = next((p for p in parking_store.payments.values() if p["booking_id"] == booking_id), None)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment["payment_status"] = "paid"
    # Also mark booking as active
    booking = parking_store.bookings.get(booking_id)
    if booking:
        booking["status"] = "confirmed"
    return {"success": True, "payment_id": payment["id"]}

# ── Owner ──────────────────────────────────────────────────────────────────────

class AddZoneRequest(BaseModel):
    owner_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    price_per_hour: float
    total_slots: int

@router.post("/zones/add")
def add_zone(req: AddZoneRequest):
    """Owner adds a new parking zone — goes into pending approval."""
    import uuid
    zone_id = f"PZ_{str(uuid.uuid4())[:8].upper()}"
    zone = {
        "id": zone_id,
        "owner_id": req.owner_id,
        "name": req.name,
        "address": req.address,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "price_per_hour": req.price_per_hour,
        "total_slots": req.total_slots,
        "available_slots": req.total_slots,
        "approved": False,
        "type": "on-street",
        "created_at": datetime.utcnow().isoformat()
    }
    parking_store.parking_areas[zone_id] = zone
    return {"success": True, "zone_id": zone_id, "message": "Zone submitted for admin approval"}

@router.get("/owner/{owner_id}/zones")
def owner_zones(owner_id: str):
    return parking_manager.get_owner_zones(owner_id)

@router.get("/owner/{owner_id}/earnings")
def owner_earnings(owner_id: str):
    return parking_manager.get_owner_earnings(owner_id)

# ── Admin ──────────────────────────────────────────────────────────────────────

@router.get("/admin/pending")
def pending_zones():
    return parking_manager.get_pending_zones()

@router.post("/admin/approve/{zone_id}")
async def approve(zone_id: str):
    if not parking_manager.approve_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
        
    from app.core.socket_manager import broadcast_parking_update
    await broadcast_parking_update()
        
    return {"success": True, "message": f"Zone {zone_id} approved"}

@router.post("/admin/reject/{zone_id}")
def reject(zone_id: str):
    if not parking_manager.reject_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"success": True, "message": f"Zone {zone_id} rejected and removed"}

@router.get("/admin/revenue")
def admin_revenue():
    return parking_manager.get_admin_revenue_dashboard()

@router.get("/admin/users")
def all_users():
    return list(parking_store.users.values())

@router.get("/commission")
def get_commission():
    return parking_store.commission_store

@router.put("/commission")
def update_commission(percentage: float):
    if percentage < 0 or percentage > 100:
        raise HTTPException(status_code=400, detail="Commission must be between 0 and 100")
    parking_store.commission_store["percentage"] = percentage
    return {"success": True, "new_percentage": percentage}

# ── Nominatim Reverse Geocoding Proxy ─────────────────────────────────────────

@router.get("/geocode/reverse")
async def reverse_geocode(lat: float, lng: float):
    """
    Proxies Nominatim reverse geocoding.
    Called when owner taps map to get address from coordinates.
    No API key needed — Nominatim is free.
    """
    import httpx
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
    headers = {"User-Agent": "UrbanFlow-SAMVED-2026"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Geocoding service unavailable")
    data = resp.json()
    return {
        "display_name": data.get("display_name", ""),
        "address": data.get("address", {})
    }
