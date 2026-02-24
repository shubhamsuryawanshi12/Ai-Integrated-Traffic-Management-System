import os
import sys
# Add backend directory to sys.path to ensure modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.sumo.environment import SumoEnvironment
from app.services.ai_engine.rl_agent import RLAgent

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    print("WARNING: 'torch' not found. Running in MOCK TRAINING mode (saving dummy weights).")
    TORCH_AVAILABLE = False

def train():
    # Correctly resolve paths relative to THIS file
    base_dir = os.path.dirname(os.path.abspath(__file__)) # D:\Hackathon\backend
    project_root = os.path.dirname(base_dir) # D:\Hackathon
    
    net_file = os.path.join(project_root, "sumo_files", "networks", "simple_grid.net.xml")
    rou_file = os.path.join(project_root, "sumo_files", "routes", "traffic_routes.rou.xml")
    
    if not os.path.exists(net_file):
         print(f"⚠️ Network file not found at {net_file}")
         # Attempt relative path fallback just in case
         net_file = "../sumo_files/networks/simple_grid.net.xml"
         rou_file = "../sumo_files/routes/traffic_routes.rou.xml"

    print(f"Starting Training with Network: {net_file}")
    
    # GUI false for faster training
    env = SumoEnvironment(net_file, rou_file, use_gui=False) 
    
    state_dim = 32 # Must match simulation.py configuration
    action_dim = 4 # Example: 4 phases
    agent = RLAgent(state_dim, action_dim)
    
    episodes = 2
    steps_per_ep = 100 # Very fast
    
    try:
        env.start()
        for episode in range(episodes):
            print(f"🎬 Starting Episode {episode}")
            total_reward = 0
            
            for step in range(steps_per_ep):
                states = env.get_state()
                actions = {}
                step_reward = env.get_reward()
                
                for ts_id, state in states.items():
                    # Pad state to match input dimension (32)
                    padded_state = state + [0.0] * (state_dim - len(state))
                    
                    action, log_prob, value = agent.get_action(padded_state)
                    actions[ts_id] = action
                    agent.store_outcome(log_prob, value, step_reward, False)
                
                env.apply_actions(actions)
                env.step()
                total_reward += step_reward
                
                # Mock training delay to make logs readable
                if not TORCH_AVAILABLE:
                    import time
                    time.sleep(0.01) 
                
                if step % 20 == 0:
                     loss = agent.update()
                     print(f"  Step {step}, Loss: {loss:.4f}, Reward: {step_reward:.2f}")

            print(f"✅ Episode {episode} finished. Total Reward: {total_reward:.2f}")
            
            # Save Model
            save_path = os.path.join(base_dir, "app", "services", "ai_engine", f"model_ep{episode}.pth")
            agent.save(save_path)
            print(f"💾 Saved Model to: {save_path}")
            
    finally:
        env.close()

if __name__ == "__main__":
    train()
