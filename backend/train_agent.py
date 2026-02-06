import os
import sys
from app.services.sumo.environment import SumoEnvironment
from app.services.ai_engine.rl_agent import RLAgent
import torch

def train():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjust paths if running from backend root
    
    # We assume this script is run as 'python -m app.train' or similar, 
    # but let's assume it is run from backend/ dir.
    
    net_file = os.path.join(base_dir, "../sumo_files/networks/simple_grid.net.xml")
    rou_file = os.path.join(base_dir, "../sumo_files/routes/traffic_routes.rou.xml")
    
    if not os.path.exists(net_file):
         print(f"Network file not found at {net_file}")
         # Attempt fallback
         net_file = "sumo_files/networks/simple_grid.net.xml"
         rou_file = "sumo_files/routes/traffic_routes.rou.xml"

    env = SumoEnvironment(net_file, rou_file, use_gui=False) # GUI false for faster training
    state_dim = 4
    action_dim = 4 # Example: 4 phases
    agent = RLAgent(state_dim, action_dim)
    
    episodes = 50
    
    try:
        env.start()
        for episode in range(episodes):
            print(f"Starting Episode {episode}")
            # Reset environment? SUMO is tricky with reset. 
            # Usually better to reload simulation or use loadState.
            # Simplified: just run steps until done? 
            # SumoEnvironment currently doesn't implement reset fully (needs traci.load).
            
            # For this MVP, we will just run a set number of steps as one 'episode' or run continuously.
            steps = 1000
            total_reward = 0
            
            for step in range(steps):
                # We need to get state for ALL intersections
                states = env.get_state()
                actions = {}
                
                # Global update or per-agent? 
                # Here we treat all intersections as sharing one brain (parameter sharing)
                
                step_reward = env.get_reward() # Global reward
                
                for ts_id, state in states.items():
                    action, log_prob, value = agent.get_action(state)
                    actions[ts_id] = action
                    
                    # Store experience
                    # Warning: Reward is global, might be noisy for individual agents
                    agent.store_outcome(log_prob, value, step_reward, False)
                
                env.apply_actions(actions)
                env.step()
                
                total_reward += step_reward
                
                # Update every N steps or end of episode?
                if step % 100 == 0 and step > 0:
                     loss = agent.update()
                     print(f"Step {step}, Loss: {loss}, Reward: {step_reward}")

            print(f"Episode {episode} finished. Total Reward: {total_reward}")
            agent.save(f"app/services/ai_engine/model_ep{episode}.pth")
            
    finally:
        env.close()

if __name__ == "__main__":
    train()
