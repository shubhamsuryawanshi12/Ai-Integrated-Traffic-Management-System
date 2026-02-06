from fastapi import APIRouter, BackgroundTasks
from app.services.sumo.environment import SumoEnvironment
from app.services.ai_engine.rl_agent import RLAgent
from typing import Dict
import threading
import time
import os

router = APIRouter()

# Global state for simulation
# Ideally this should be a singleton service
class SimulationManager:
    def __init__(self):
        self.env = None
        self.agent = None
        self.running = False
        self.thread = None

    def start_simulation(self):
        if self.running:
            return
        
        # Paths - assuming execution from backend root
        base_dir = os.path.abspath(".")
        net_file = os.path.join(base_dir, "sumo_files/networks/simple_grid.net.xml")
        rou_file = os.path.join(base_dir, "sumo_files/routes/traffic_routes.rou.xml")
        
        # Check if files exist
        if not os.path.exists(net_file):
             # Try fallback to relative path if run from d:/Hackathon
             net_file = "../sumo_files/networks/simple_grid.net.xml"
             rou_file = "../sumo_files/routes/traffic_routes.rou.xml"

        self.env = SumoEnvironment(net_file, rou_file, use_gui=False)
        self.agent = RLAgent(state_dim=4, action_dim=4)
        
        try:
            self.env.start()
            self.running = True
            print(f"Simulation started. Mock mode: {self.env.mock_mode}")
            
            # Start loop in background
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"Failed to start simulation: {e}")
            # Try to start in mock mode anyway
            self.env.mock_mode = True
            self.env.is_running = True
            self.env.ts_ids = ["gneJ0", "gneJ1", "gneJ2", "gneJ3"]
            self.running = True
            print("Falling back to MOCK MODE")
            
            # Start loop in background
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()

    def stop_simulation(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            self.env.close()

    def _simulation_loop(self):
        print("Simulation loop started.")
        try:
            while self.running:
                self.env.step() # Advance Physics
                states = self.env.get_state()
                
                # For each intersection, get action
                actions = {}
                for ts_id, state in states.items():
                    action, _, _ = self.agent.get_action(state)
                    actions[ts_id] = action
                
                self.env.apply_actions(actions)
                
                # Update latest state for broadcast
                self.latest_state = {
                    "intersections": [
                         {
                             "id": k, 
                             "name": f"Intersection {k}",
                             "current_status": {"phase": "green" if v[3] == 0 else "red"}, 
                             "traffic_data": {"vehicle_count": int(v[1]), "average_wait_time": float(v[0])},
                             # Fix: Generate coordinates VERY close to map center
                             # Using simple offsets. Range: 0-4 * 50 = 200 units. 
                             # At scale 0.0001, 200 * 0.0001 = 0.02 deg ~ 2km. Still a bit wide but okay.
                             # Let's reduce grid step to 10.
                             "location": {
                                 "x": (hash(k) % 5) * 50, 
                                 "y": (hash(k) % 5) * 50
                             } 
                         } for k, v in states.items()
                    ],
                    "snapshot": {
                        "timestamp": time.time() * 1000,
                        "avg_queue_length": float(sum(float(v[0]) for v in states.values()) / max(1, len(states)))
                    }
                }
                
                time.sleep(1.0)
        except Exception as e:
            print(f"Simulation loop crashed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            print("Simulation loop ended.")

    def get_latest_state(self):
        return getattr(self, 'latest_state', {})

sim_manager = SimulationManager()

# Background task to broadcast
import asyncio
from app.core.socket_manager import broadcast_traffic_update

async def broadcast_loop():
    print("Broadcast loop started")
    while True:
        if sim_manager.running:
            state = sim_manager.get_latest_state()
            if state:
                print(f"Broadcasting state with {len(state.get('intersections', []))} intersections")
                await broadcast_traffic_update(state)
            else:
                print("Simulation running but no state to broadcast")
        await asyncio.sleep(2)

# @router.on_event("startup")
# async def startup_event():
#     asyncio.create_task(broadcast_loop())

@router.post("/start")
async def start_simulation(background_tasks: BackgroundTasks):
    if sim_manager.running:
        return {"status": "already running"}
    
    # We can't really block the request, so we rely on the manager
    # But start_simulation calls traci.start which might block a bit?
    # Better to run in background?
    # sim_manager.start_simulation() is nearly instant if it just spawns thread.
    try:
        sim_manager.start_simulation()
        return {"status": "started"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@router.post("/stop")
async def stop_simulation():
    sim_manager.stop_simulation()
    return {"status": "stopped"}

@router.get("/status")
async def get_simulation_status():
    return {"running": sim_manager.running}

@router.post("/test_broadcast")
async def test_broadcast():
    """Manually trigger a fake traffic update to test WebSocket"""
    import time
    fake_data = {
        "intersections": [
             {
                 "id": "TEST_INT", 
                 "current_status": {"phase": "green"},
                 "traffic_data": {"vehicle_count": 42, "average_wait_time": 10.5},
                 "location": {"x": 40.7580, "y": -73.9855}
             }
        ],
        "snapshot": {
            "timestamp": time.time() * 1000,
            "avg_queue_length": 15
        }
    }
    await broadcast_traffic_update(fake_data)
    return {"status": "broadcast_sent", "data": fake_data}
