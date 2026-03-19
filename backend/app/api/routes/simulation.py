# Fix encoding for Windows console
import sys
import io
if sys.platform == 'win32' and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import APIRouter, BackgroundTasks, HTTPException, Body
try:
    from app.services.vision.hybrid_environment import HybridEnvironment
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False
    print("WARNING: HybridEnvironment not available (missing numpy/cv2?). Using SumoEnvironment.")
    from app.services.sumo.environment import SumoEnvironment

try:
    from app.services.vision.camera_stream import MobileCamera
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

from app.services.ai_engine.a3c_agent import RLAgent
from typing import Dict, Optional, List, Any
import threading
import time
import os

router = APIRouter()

class HybridAdapter:
    """Adapter for SumoEnvironment to look like HybridEnvironment"""
    def __init__(self, mode, config):
        self.mode = mode
        self.sumo_env = SumoEnvironment(config['net_file'], config['rou_file'], config.get('gui', False))
        self.camera = None
        self.vehicle_detector = None
        
    def start(self):
        try:
            self.sumo_env.start()
        except Exception as e:
            print(f"[WARNING] HybridAdapter start failed: {e}")
            # Continue with mock mode

    def get_state(self):
        # Flatten state dict to list for RLAgent
        states = self.sumo_env.get_state()
        features = []
        for ts_id, state in states.items():
            # state is list [queue, count, speed, phase]
            features.extend(state)
        # Pad to 32
        target_size = 32
        features = features[:target_size]
        while len(features) < target_size:
            features.append(0.0)
        return features

    def step(self, action):
        # Apply action to all
        if self.sumo_env.is_running:
             # Map scalar action to dict?
             # Agent returns int.
             actions = {ts: action for ts in self.sumo_env.ts_ids}
             self.sumo_env.apply_actions(actions)
             self.sumo_env.step()
        
        return self.get_state(), 0, False, {}

    def stop(self):
        self.sumo_env.close()

# Global state for simulation
class SimulationManager:
    def __init__(self):
        self.env = None
        self.agent = None
        self.running = False
        self.thread = None
        self.emergency_active = False
        self.emergency_intersection = None
        self.weather_mode = "clear" # clear, rain, fog
        self.cumulative_co2_saved = 0.0
        self.step_count = 0
        
    def start_simulation(self, mode: str = 'simulation'):
        if self.running:
            return
        
        # Paths - use project root directory (parent of backend)
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        project_root = os.path.dirname(backend_dir)  # Go up from backend/app/api/routes to project root
        net_file = os.path.join(project_root, "sumo_files/networks/simple_grid.net.xml")
        rou_file = os.path.join(project_root, "sumo_files/routes/traffic_routes.rou.xml")
        
        config = {
            'net_file': net_file,
            'rou_file': rou_file,
            'gui': False,
            'sim_weight': 0.7,
            'real_weight': 0.3
        }

        if HYBRID_AVAILABLE:
            self.env = HybridEnvironment(mode=mode, config=config)
        else:
            self.env = HybridAdapter(mode=mode, config=config)

        try:
            self.env.start() # Starts SUMO and/or Camera
        except Exception as e:
            print(f"[WARNING] Environment start failed: {e}")
            # Continue anyway - mock mode should work
        
        self.agent = RLAgent(state_dim=32, action_dim=4) 
        
        # Auto-load latest trained model
        try:
            import glob
            model_dir = os.path.join(project_root, "backend/app/services/ai_engine")
            models = glob.glob(os.path.join(model_dir, "model_ep*.pth"))
            if models:
                latest_model = max(models, key=os.path.getctime)
                self.agent.load(latest_model)
                print(f"[OK] Loaded trained AI model: {os.path.basename(latest_model)}")
            else:
                print("[INFO] No trained model found, running with random agent.")
        except Exception as e:
            print(f"[WARN] Error loading AI model: {e}") 
        
        self.running = True
        
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()



    def stop_simulation(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            if hasattr(self.env, 'stop'):
                self.env.stop()
            elif hasattr(self.env, 'close'):
                self.env.close()

    def _simulation_loop(self):
        mode = getattr(self.env, 'mode', 'Unknown')
        print(f"Simulation loop started. Mode: {mode}")
        
        # Pre-calculate grid locations for mock mode or visualization
        print(f"Simulation loop started. Mode: {self.env.mode if self.env else 'Unknown'}")
        
        # Grid layout for visualizer
        # We need IDs. If HybridEnv is in simulation mode, we can get them from sumo_env.
        # If real_world, we might have fixed IDs or single intersection.
        # For robustness, we'll try to get IDs from sumo_env if available, else use a default.
        
        ts_ids = []
        if self.env and self.env.sumo_env:
            # Depending on if SUMO successfully started or Mock mode
            ts_ids = self.env.sumo_env.ts_ids
        else:
             # Default/Mock IDs for Real World or Fallback
             ts_ids = ["INT_1"]

        grid_size = int(len(ts_ids) ** 0.5) + 1
        node_locations = {}
        for idx, ts_id in enumerate(ts_ids):
            row = idx // grid_size
            col = idx % grid_size
            node_locations[ts_id] = {
                "x": col * 150,
                "y": row * 150
            }

        try:
            while self.running and self.env:
                # Decentralized Adaptive Control Loop
                # Each intersection observes its own state and acts independently
                
                intersections_data = []
                actions = {}
                
                # Get current mode
                current_mode = getattr(self.env, 'mode', 'simulation')
                
                if hasattr(self.env, 'sumo_env') and self.env.sumo_env:
                    # Multi-Agent Control (Simulation / Hybrid)
                    sumo_states = self.env.sumo_env.get_state() # Dict[ts_id, items]
                    
                    # Sort IDs to ensure consistent 'Wave' order
                    sorted_ids = sorted(sumo_states.keys())
                    
                    for i, ts_id in enumerate(sorted_ids):
                        state_vec = sumo_states[ts_id]
                        
                        action = 0
                        # === COORDINATION DEMO MODE (Green Wave) ===
                        if current_mode == 'green_wave':
                            # Deterministic "Green Wave" Logic
                            # Cycle: 10s. Split: 50/50. Offset: 2s per intersection.
                            cycle_time = 10.0
                            offset = i * 2.0
                            # Calculate position in cycle
                            t = (time.time() + offset) % cycle_time
                            
                            if t < (cycle_time * 0.5):
                                action = 0 # Green Phase
                            else:
                                action = 2 # Red Phase
                        else:
                            # === AI ADAPTIVE CONTROL ===
                            # state_vec: [queue, count, speed, phase] (4 dims)
                            # Pad to agent's expected input dimension (32)
                            local_state = state_vec + [0.0] * (32 - len(state_vec))
                            action, _, _ = self.agent.get_action(local_state, intersection_id=ts_id)
                            
                        actions[ts_id] = action
                        
                        # Visualization Data
                        # Map phase 0->green, 1->yellow, 2->red (simplified)
                        # If green_wave, we force action. If AI, we read existing state (which implies delay)
                        # For better UI responsiveness, show the PLANNED action status if green_wave,
                        # but real status comes from env.step().
                        # Let's show current ENV status for accuracy.
                        
                        phase_str = "green"
                        if len(state_vec) > 3:
                            p = int(state_vec[3])
                            if p == 1: phase_str = "yellow"
                            elif p == 2: phase_str = "red"
                            
                        intersections_data.append({
                             "id": ts_id, 
                             "name": f"Signal {ts_id}",
                             "current_status": {"phase": phase_str}, 
                             "traffic_data": {
                                 "vehicle_count": int(state_vec[1]), 
                                 "average_wait_time": float(state_vec[0]),
                                 "avg_speed": float(state_vec[2])
                             },
                             "location": node_locations.get(ts_id, {"x": 0, "y": 0})
                        })

                    # Apply Distributed Actions
                    self.env.sumo_env.apply_actions(actions)
                    self.env.sumo_env.step()
                    
                elif current_mode == 'real_world':
                     # Single Camera Control
                     if self.env.camera:
                         state_vec = [0]*32 
                         # TODO: Get real features from vehicle_detector
                         action, _, _ = self.agent.get_action(state_vec)
                         
                         stats = self.env.camera.get_stats()
                         intersections_data.append({
                             "id": "CAM_1",
                             "name": "Live Camera Feed",
                             "current_status": {"phase": "active"},
                             "traffic_data": {"vehicle_count": 0, "average_wait_time": 0},
                             "location": {"x": 50, "y": 50}
                         })
                         # No step() for real world usually, or it's implicitly time-based

                # === FEATURE: CO2 SAVINGS CALCULATION ===
                current_avg_wait = sum([d['traffic_data']['average_wait_time'] for d in intersections_data]) / max(1, len(intersections_data))
                savings_this_step = max(0, (15.0 - current_avg_wait) * sum([d['traffic_data']['vehicle_count'] for d in intersections_data]) * 0.05)
                self.cumulative_co2_saved += savings_this_step

                # === FEATURE: EMERGENCY PREEMPTION OVERRIDE ===
                if self.emergency_active and self.emergency_intersection:
                    for d in intersections_data:
                        if d['id'] == self.emergency_intersection:
                            d['current_status']['phase'] = 'emergency'
                            d['name'] = f"🚨 EMERGENCY: {d['id']}"

                self.latest_state = {
                    "intersections": intersections_data,
                    "snapshot": {
                        "timestamp": time.time() * 1000,
                        "avg_queue_length": current_avg_wait,
                        "weather": self.weather_mode,
                        "co2_saved_kg": round(self.cumulative_co2_saved / 1000, 2),
                        "emergency_active": self.emergency_active
                    }
                }
                
                self.step_count += 1
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
        
    def receive_camera_frame(self, base64_image: str):
        """Pass frame to hybrid env camera"""
        if self.env and self.env.camera:
            if hasattr(self.env.camera, 'receive_frame'):
                return self.env.camera.receive_frame(base64_image)
        return False

sim_manager = SimulationManager()

# Background task to broadcast
import asyncio
from app.core.socket_manager import broadcast_traffic_update, broadcast_parking_update, sio
from app.services.ai_engine.anomaly_detector import anomaly_detector

async def broadcast_loop():
    print("Broadcast loop started")
    while True:
        if sim_manager.running:
            state = sim_manager.get_latest_state()
            if state:
                await broadcast_traffic_update(state)
                
                # Check for anomalies and broadcast alerts
                anomalies = anomaly_detector.detect_anomalies(state.get('intersections', []))
                for anomaly in anomalies:
                    # Emit alert via socketio to the frontend AlertPanel
                    await sio.emit('hawker_alert', {
                        'alert_message': anomaly['message'],
                        'severity': anomaly['severity'],
                        'type': 'traffic_anomaly'
                    })
        
        # Broadcast parking updates independently mapping every 2 seconds
        # For demo, simulate updates
        # parking_manager.simulate_random_updates()
        # await broadcast_parking_update({"zones": parking_manager.get_all_zones()})
        
        await asyncio.sleep(2)

# @router.on_event("startup")
# async def startup_event():
#     asyncio.create_task(broadcast_loop())

@router.post("/start")
async def start_simulation(background_tasks: BackgroundTasks, mode: str = 'simulation'):
    if sim_manager.running:
        return {"status": "already running"}
    
    try:
        # Start in background thread (handled by manager)
        sim_manager.start_simulation(mode=mode)
        return {"status": "started", "mode": mode}
    except Exception as e:
        # Return ASCII-safe error message
        error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
        return {"status": "failed", "error": error_msg}

@router.post("/stop")
async def stop_simulation():
    sim_manager.stop_simulation()
    return {"status": "stopped"}

@router.get("/status")
async def get_simulation_status():
    return {"running": sim_manager.running}

@router.post("/camera/frame")
async def receive_camera_frame(data: Dict = Body(...)):
    """Receive base64 encoded frame from mobile/webcam"""
    image_data = data.get("image")
    if not image_data:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    # Send to simulation manager -> hybrid env -> camera
    success = sim_manager.receive_camera_frame(image_data)
    
    return {"status": "received", "processed": success}

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

@router.post("/emergency")
async def trigger_emergency(intersection_id: str = "INT_1", active: bool = True):
    """Trigger or clear emergency preemption on a specific intersection"""
    sim_manager.emergency_active = active
    sim_manager.emergency_intersection = intersection_id if active else None
    return {"status": "success", "emergency": active, "intersection": intersection_id}

@router.post("/weather")
async def set_weather(condition: str = Body(..., embed=True)):
    """Set simulation weather: clear, rain, fog"""
    if condition not in ["clear", "rain", "fog"]:
        raise HTTPException(status_code=400, detail="Invalid weather mode")
    sim_manager.weather_mode = condition
    return {"status": "success", "weather": condition}

