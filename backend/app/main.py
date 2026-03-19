# Fix encoding for Windows console
import sys
import io
if sys.platform == 'win32' and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import traffic, simulation, parking, prediction, routing
from app.api.routes import ml_model
from app.api.routes import chatbot
from app.api.routes import owner_auth, categories
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
fastapi_app.include_router(parking.router, prefix="/api/v1/parking", tags=["parking"])
fastapi_app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["prediction"])
fastapi_app.include_router(routing.router, prefix="/api/v1/routing", tags=["routing"])
fastapi_app.include_router(ml_model.router, prefix="/api/v1/ml", tags=["ml"])
fastapi_app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["chatbot"])
fastapi_app.include_router(owner_auth.router, prefix="/api/v1/owner", tags=["owner"])
fastapi_app.include_router(categories.router, prefix="/api/v1/lot", tags=["categories"])

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
