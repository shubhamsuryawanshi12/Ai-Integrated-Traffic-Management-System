import threading
import uuid
from datetime import datetime
from .parking_store import parking_areas, bookings, payments, commission_store

# Use a lock to prevent race conditions (equivalent to Supabase atomic RPC)
_booking_lock = threading.Lock()

def book_parking_slot(user_id: str, parking_id: str, start_time: datetime, end_time: datetime) -> dict:
    """
    Atomic booking function. Equivalent to the Supabase book_parking_slot RPC.
    Uses threading.Lock to prevent double booking (same guarantee as DB transaction).
    """
    with _booking_lock:
        # 1. Fetch parking area
        zone = parking_areas.get(parking_id)
        if not zone:
            return {"success": False, "error": "Parking area not found"}

        if not zone["approved"]:
            return {"success": False, "error": "Parking area not approved"}

        # 2. Check slot availability (equivalent to: available_slots > 0 check)
        if zone["available_slots"] <= 0:
            return {"success": False, "error": "No slots available"}

        # 3. Calculate duration and amount
        duration_hours = (end_time - start_time).total_seconds() / 3600
        if duration_hours <= 0:
            return {"success": False, "error": "Invalid time range"}

        total_amount = round(duration_hours * zone["price_per_hour"], 2)

        # 4. Fetch commission percentage
        commission_pct = commission_store["percentage"] / 100
        commission_amount = round(total_amount * commission_pct, 2)
        owner_amount = round(total_amount - commission_amount, 2)

        # 5. Decrement available_slots atomically
        zone["available_slots"] -= 1

        # 6. Create booking record
        booking_id = str(uuid.uuid4())
        booking = {
            "id": booking_id,
            "user_id": user_id,
            "parking_id": parking_id,
            "parking_name": zone["name"],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_amount": total_amount,
            "commission_amount": commission_amount,
            "owner_amount": owner_amount,
            "status": "confirmed",
            "created_at": datetime.utcnow().isoformat()
        }
        bookings[booking_id] = booking

        # 7. Create payment record
        payment_id = str(uuid.uuid4())
        payments[payment_id] = {
            "id": payment_id,
            "booking_id": booking_id,
            "amount": total_amount,
            "commission": commission_amount,
            "owner_amount": owner_amount,
            "payment_status": "pending"   # updated to "paid" after payment confirmation
        }

        return {
            "success": True,
            "booking_id": booking_id,
            "total_amount": total_amount,
            "commission_amount": commission_amount,
            "owner_amount": owner_amount,
            "available_slots_remaining": zone["available_slots"]
        }

def release_slot(parking_id: str) -> bool:
    """Increment available_slots when booking is cancelled."""
    with _booking_lock:
        zone = parking_areas.get(parking_id)
        if not zone:
            return False
        if zone["available_slots"] < zone["total_slots"]:
            zone["available_slots"] += 1
        return True

def get_all_approved_zones() -> list:
    return [z for z in parking_areas.values() if z["approved"]]

def get_pending_zones() -> list:
    return [z for z in parking_areas.values() if not z["approved"]]

def approve_zone(parking_id: str) -> bool:
    zone = parking_areas.get(parking_id)
    if zone:
        zone["approved"] = True
        return True
    return False

def reject_zone(parking_id: str) -> bool:
    return bool(parking_areas.pop(parking_id, None))

def get_owner_zones(owner_id: str) -> list:
    return [z for z in parking_areas.values() if z["owner_id"] == owner_id]

def get_owner_bookings(owner_id: str) -> list:
    owner_zone_ids = {z["id"] for z in get_owner_zones(owner_id)}
    return [b for b in bookings.values() if b["parking_id"] in owner_zone_ids]

def get_owner_earnings(owner_id: str) -> dict:
    owner_bookings = get_owner_bookings(owner_id)
    confirmed = [b for b in owner_bookings if b["status"] == "confirmed"]
    total_revenue = sum(b["total_amount"] for b in confirmed)
    total_commission = sum(b["commission_amount"] for b in confirmed)
    owner_earnings = sum(b["owner_amount"] for b in confirmed)
    return {
        "total_revenue": round(total_revenue, 2),
        "total_commission_paid": round(total_commission, 2),
        "owner_net_earnings": round(owner_earnings, 2),
        "total_bookings": len(confirmed)
    }

def get_admin_revenue_dashboard() -> dict:
    all_confirmed = [b for b in bookings.values() if b["status"] == "confirmed"]
    return {
        "total_bookings": len(all_confirmed),
        "total_revenue": round(sum(b["total_amount"] for b in all_confirmed), 2),
        "total_commission_earned": round(sum(b["commission_amount"] for b in all_confirmed), 2),
        "total_owner_payouts": round(sum(b["owner_amount"] for b in all_confirmed), 2),
        "active_zones": len(get_all_approved_zones()),
        "pending_zones": len(get_pending_zones())
    }

def haversine_distance(lat1, lng1, lat2, lng2) -> float:
    """
    Haversine formula — returns distance in kilometers.
    Used for finding nearby parking zones.
    """
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_nearby_zones(lat: float, lng: float, radius_km: float = 5.0) -> list:
    """Return approved zones within radius_km of given coordinates."""
    result = []
    for zone in get_all_approved_zones():
        dist = haversine_distance(lat, lng, zone["latitude"], zone["longitude"])
        if dist <= radius_km:
            result.append({**zone, "distance_km": round(dist, 2)})
    return sorted(result, key=lambda z: z["distance_km"])
