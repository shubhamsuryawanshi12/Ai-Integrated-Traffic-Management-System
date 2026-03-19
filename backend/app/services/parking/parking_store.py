import uuid
from datetime import datetime

# Commission config
commission_store = {"id": "global", "percentage": 10.0}

# Seed: parking areas in Solapur with real coordinates
parking_areas = {
    "PZ_001": {
        "id": "PZ_001",
        "owner_id": "OWNER_001",
        "name": "Station Road Parking Lot",
        "address": "Station Road, Near Solapur Railway Station, Solapur - 413001",
        "latitude": 17.6722,
        "longitude": 75.9043,
        "price_per_hour": 20.0,
        "total_slots": 50,
        "available_slots": 35,
        "approved": True,
        "type": "structured",
        "created_at": "2026-01-01T00:00:00"
    },
    "PZ_002": {
        "id": "PZ_002",
        "owner_id": "OWNER_001",
        "name": "Siddheshwar Temple Parking",
        "address": "Near Siddheshwar Temple, Solapur - 413002",
        "latitude": 17.6868,
        "longitude": 75.9060,
        "price_per_hour": 15.0,
        "total_slots": 80,
        "available_slots": 12,
        "approved": True,
        "type": "on-street",
        "created_at": "2026-01-01T00:00:00"
    },
    "PZ_003": {
        "id": "PZ_003",
        "owner_id": "OWNER_002",
        "name": "Market Yard Parking",
        "address": "Market Yard, Solapur - 413003",
        "latitude": 17.6599,
        "longitude": 75.8983,
        "price_per_hour": 10.0,
        "total_slots": 100,
        "available_slots": 67,
        "approved": True,
        "type": "on-street",
        "created_at": "2026-01-01T00:00:00"
    },
    "PZ_004": {
        "id": "PZ_004",
        "owner_id": "OWNER_002",
        "name": "Bus Stand Multi-Level Parking",
        "address": "Central Bus Stand, Solapur - 413001",
        "latitude": 17.6750,
        "longitude": 75.9100,
        "price_per_hour": 25.0,
        "total_slots": 200,
        "available_slots": 143,
        "approved": True,
        "type": "structured",
        "created_at": "2026-01-01T00:00:00"
    },
    "PZ_005": {
        "id": "PZ_005",
        "owner_id": "OWNER_003",
        "name": "Hotgi Road Parking",
        "address": "Hotgi Road, Solapur - 413005",
        "latitude": 17.6900,
        "longitude": 75.9200,
        "price_per_hour": 12.0,
        "total_slots": 40,
        "available_slots": 5,
        "approved": False,   # pending approval — for admin demo
        "type": "on-street",
        "created_at": "2026-03-15T10:00:00"
    },
}

bookings = {}    # booking_id -> booking dict
payments = {}    # payment_id -> payment dict
users = {
    "ADMIN_001": {
        "id": "ADMIN_001",
        "name": "SMC Admin",
        "email": "admin@solapurmc.gov.in",
        "role": "admin"
    },
    "OWNER_001": {
        "id": "OWNER_001",
        "name": "Ramesh Kulkarni",
        "email": "ramesh@owner.com",
        "role": "owner"
    },
    "OWNER_002": {
        "id": "OWNER_002",
        "name": "Suresh Patil",
        "email": "suresh@owner.com",
        "role": "owner"
    },
    "DRIVER_001": {
        "id": "DRIVER_001",
        "name": "Anil Sharma",
        "email": "anil@driver.com",
        "role": "driver"
    },
}
