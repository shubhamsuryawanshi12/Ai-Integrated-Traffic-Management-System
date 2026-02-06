import os
import sys
import time
import numpy as np
from typing import Dict, List, Tuple

# Try to import traci for SUMO simulation
try:
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False
    print("WARNING: SUMO/TraCI not available. Running in MOCK mode only.")

# Ensure SUMO_HOME is set
if 'SUMO_HOME' not in os.environ:
    print("WARNING: SUMO_HOME not set. Simulation features will not work.")

class SumoEnvironment:
    def __init__(self, net_file: str, route_file: str, use_gui: bool = False):
        self.net_file = net_file
        self.route_file = route_file
        self.use_gui = use_gui
        self.ts_ids = []
        self.lanes = []
        
        # Check if we should run in mock mode
        self.mock_mode = not TRACI_AVAILABLE or 'SUMO_HOME' not in os.environ
        
        if not self.mock_mode:
            self.sumo_binary = "sumo-gui" if self.use_gui else "sumo"
            self.sumo_cmd = [
                self.sumo_binary,
                "-n", self.net_file,
                "-r", self.route_file,
                "--no-step-log", "true",
                "--waiting-time-memory", "1000"
            ]
        self.is_running = False

    def start(self):
        """Start the simulation"""
        if self.mock_mode:
            print("Starting simulation in MOCK MODE")
            self.is_running = True
            # Mock Intersection IDs
            self.ts_ids = ["gneJ0", "gneJ1", "gneJ2", "gneJ3"]
            self.lanes = ["lane_1", "lane_2"]
            return

        try:
            traci.start(self.sumo_cmd)
            self.is_running = True
            self.ts_ids = traci.trafficlight.getIDList()
            self.lanes = []
            for ts in self.ts_ids:
                self.lanes.extend(traci.trafficlight.getControlledLanes(ts))
            self.lanes = list(set(self.lanes))
        except Exception as e:
            print(f"Failed to start SUMO, switching to MOCK MODE: {e}")
            self.mock_mode = True
            self.is_running = True
            self.ts_ids = ["gneJ0", "gneJ1", "gneJ2", "gneJ3"]

    def step(self):
        """Advance simulation by one step"""
        if not self.is_running:
            return
        
        if self.mock_mode:
            # Simulate processing time
            import time
            time.sleep(0.1)
            return

        traci.simulationStep()

    def get_state(self) -> Dict[str, np.ndarray]:
        """
        Get the current state of the environment.
        """
        states = {}
        
        if self.mock_mode:
            for ts_id in self.ts_ids:
                # Generate random realistic looking traffic data
                queue_length = np.random.uniform(0, 20)
                num_vehicles = np.random.uniform(5, 50)
                avg_speed = np.random.uniform(5, 15)
                phase = int(np.random.choice([0, 1, 2])) # 0: Green, 1: Yellow, 2: Red
                
                state_vec = np.array([queue_length, num_vehicles, avg_speed, phase], dtype=np.float32)
                states[ts_id] = state_vec
            return states

        for ts_id in self.ts_ids:
            try:
                lanes = traci.trafficlight.getControlledLanes(ts_id)
                queue_length = 0
                num_vehicles = 0
                avg_speed = 0.0
                
                for lane in lanes:
                    queue_length += traci.lane.getLastStepHaltingNumber(lane)
                    num_vehicles += traci.lane.getLastStepVehicleNumber(lane)
                    avg_speed += traci.lane.getLastStepMeanSpeed(lane)
                
                if len(lanes) > 0:
                    avg_speed /= len(lanes)

                phase = traci.trafficlight.getPhase(ts_id)
                state_vec = np.array([queue_length, num_vehicles, avg_speed, phase], dtype=np.float32)
                states[ts_id] = state_vec
            except Exception:
                # Fallback if traci fails during query
                states[ts_id] = np.array([0, 0, 0, 0], dtype=np.float32)
            
        return states

    def apply_actions(self, actions: Dict[str, int]):
        if self.mock_mode:
            return

        for ts_id, phase_index in actions.items():
            current_phase = traci.trafficlight.getPhase(ts_id)
            if current_phase != phase_index:
                traci.trafficlight.setPhase(ts_id, phase_index)

    def get_reward(self) -> float:
        if self.mock_mode:
            return np.random.uniform(-100, -10)

        total_waiting_time = 0
        total_stopped = 0
        for lane in self.lanes:
            total_waiting_time += traci.lane.getWaitingTime(lane)
            total_stopped += traci.lane.getLastStepHaltingNumber(lane)
            
        reward = -(total_waiting_time + 10 * total_stopped)
        return reward

    def close(self):
        self.is_running = False
        if not self.mock_mode:
            try:
                traci.close()
            except:
                pass
