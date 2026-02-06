from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import traffic, simulation
from app.core.socket_manager import sio
import socketio
import asyncio

fastapi_app = FastAPI(title="UrbanFlow API", version="1.0.0")

# Configure CORS
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(traffic.router, prefix="/api/v1/traffic", tags=["traffic"])
fastapi_app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])

@fastapi_app.get("/")
async def root():
    return {"message": "UrbanFlow API is running", "status": "online"}

@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Start broadcast loop on first WebSocket connection using Socket.IO events
broadcast_task_started = False

@sio.event
async def connect(sid, environ):
    global broadcast_task_started
    print(f"Client connected: {sid}")
    if not broadcast_task_started:
        broadcast_task_started = True
        print("MAIN: Starting broadcast loop on first connection...")
        asyncio.create_task(simulation.broadcast_loop())

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

# Wrap FastAPI with Socket.IO
app = socketio.ASGIApp(sio, fastapi_app)
