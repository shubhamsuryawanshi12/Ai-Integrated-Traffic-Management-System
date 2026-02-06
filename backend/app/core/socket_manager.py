import socketio
from fastapi import FastAPI

# Create a Socket.IO server
# async_mode='asgi' is important for compatibility with uvicorn
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('connection_status', {'connected': True}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

# Broadcast function to be called from simulation loop
async def broadcast_traffic_update(data):
    print("SocketManager: Emitting traffic_update")
    await sio.emit('traffic_update', data)

async def broadcast_ai_decision(data):
    await sio.emit('ai_decision', data)
