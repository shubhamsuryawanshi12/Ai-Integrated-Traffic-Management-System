"""
Flask Dashboard for PCU-MARL++ Real-time Monitoring.

Provides WebSocket interface for live traffic simulation visualization.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pcu_marl.env import TrafficEnv
from pcu_marl.agents import CentralizedMAPPO
import torch
import numpy as np


# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pcu_marl_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
simulator_thread = None
is_running = False
current_state = None
env = None
agents = None
step_count = 0
episode_count = 0


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """Get simulation status."""
    return jsonify({
        'running': is_running,
        'step': step_count,
        'episode': episode_count,
    })


@app.route('/api/start', methods=['POST'])
def start_simulation():
    """Start the simulation."""
    global simulator_thread, is_running, env, agents, step_count, episode_count
    
    if is_running:
        return jsonify({'status': 'already_running'})
    
    # Create environment and agents
    env = TrafficEnv(n_junctions=12, seed=42)
    agents = CentralizedMAPPO(n_agents=12, device='cpu')
    
    step_count = 0
    episode_count = 0
    is_running = True
    
    # Start simulation thread
    simulator_thread = threading.Thread(target=simulation_loop, daemon=True)
    simulator_thread.start()
    
    return jsonify({'status': 'started'})


@app.route('/api/stop', methods=['POST'])
def stop_simulation():
    """Stop the simulation."""
    global is_running
    
    is_running = False
    
    return jsonify({'status': 'stopped'})


@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    """Reset the simulation."""
    global env, agents, step_count, episode_count, is_running
    
    is_running = False
    time.sleep(0.5)
    
    env = TrafficEnv(n_junctions=12, seed=42)
    agents = CentralizedMAPPO(n_agents=12, device='cpu')
    step_count = 0
    episode_count = 0
    
    return jsonify({'status': 'reset'})


def simulation_loop():
    """Main simulation loop running in background thread."""
    global env, agents, step_count, episode_count, is_running, current_state
    
    print("Starting simulation loop...")
    
    # Reset environment
    obs, _ = env.reset()
    max_steps = 400
    
    while is_running:
        try:
            # Select actions
            actions_dict = {}
            for jid in range(12):
                action, _, _ = agents.agents[jid].select_action(obs[jid], deterministic=True)
                actions_dict[jid] = action
            
            # Step environment
            obs, rewards, dones, infos = env.step(actions_dict)
            step_count += 1
            
            # Check episode end
            if step_count >= max_steps:
                obs, _ = env.reset()
                episode_count += 1
                step_count = 0
            
            # Get state for dashboard
            state = env.get_state_dict()
            
            # Add rewards
            state['rewards'] = {str(k): v for k, v in rewards.items()}
            
            # Add active CATC policy (mock)
            state['active_catc_policy'] = 'moderate' if env.weather.current_rain_intensity > 0.3 else 'clear'
            
            # Add LAUER event
            state['lauer_event'] = 'No active events'
            
            # Emit to WebSocket
            socketio.emit('state_update', state)
            
            # Sleep to control update rate
            socketio.sleep(0.5)
            
        except Exception as e:
            print(f"Simulation error: {e}")
            is_running = False
            break
    
    print("Simulation loop ended.")


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected")
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print("Client disconnected")


@socketio.on('request_state')
def handle_state_request():
    """Handle state request from client."""
    if current_state:
        emit('state_update', current_state)


def create_app():
    """Create and configure the Flask app."""
    return app


def run_dashboard(host='0.0.0.0', port=5000):
    """Run the dashboard server."""
    socketio.run(app, host=host, port=port, debug=False)


if __name__ == '__main__':
    run_dashboard()
