# 📱 UrbanFlow Mobile Camera Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install opencv-python ultralytics flask flask-cors flask-socketio
```

### 2. Start the Camera Server
```bash
cd backend
python -m app.services.mobile_camera.mobile_camera_server
```

### 3. Open on Your Phone
The server will display a URL like:
```
📱 Open this URL on your phone:
   http://192.168.1.100:5000
```

Open this URL in your phone's browser (Chrome recommended).

### 4. Grant Camera Permission
- Click "Start Camera" button
- Allow camera access when prompted
- Point your phone at traffic

---

## Features

### 📷 Camera Interface (`/`)
- Live camera preview
- Start/Stop controls
- Real-time detection results
- FPS counter

### 📊 Dashboard (`/dashboard`)
- Traffic signal display
- Vehicle count charts
- Lane statistics
- Data collection controls

### 🤖 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | Server status and statistics |
| `GET /api/latest` | Latest detection results |
| `GET /api/rl_state` | Current state in RL format |
| `POST /api/collect/start` | Start data collection |
| `POST /api/collect/stop` | Stop data collection |
| `GET /api/collect/export` | Export collected data |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Mobile Phone                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Browser (Camera Interface)                      │    │
│  │  - Camera access via getUserMedia()              │    │
│  │  - Captures frames at 5 FPS                      │    │
│  │  - Sends base64 images via WebSocket             │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           │ WebSocket
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Mobile Camera Server (Flask)                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Frame Receiver                                  │    │
│  │  - Decodes base64 images                         │    │
│  │  - Queues for processing                         │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                                │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Vision Processing Pipeline                      │    │
│  │  ├─ SignalDetector (OpenCV)                      │    │
│  │  │   - Traffic light detection                   │    │
│  │  │   - Color classification                      │    │
│  │  │   - Phase timing                              │    │
│  │  │                                               │    │
│  │  └─ VehicleDetector (YOLOv8)                     │    │
│  │      - Vehicle detection                         │    │
│  │      - Lane-wise counting                        │    │
│  │      - Queue calculation                         │    │
│  │      - Speed estimation                          │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                                │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  DataProcessor                                   │    │
│  │  - Converts to RL state format                   │    │
│  │  - Calculates reward signal                      │    │
│  │  - Exports training data                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              RL Training Integration                     │
│  - HybridEnvironment                                     │
│  - Combines SUMO + Camera data                           │
│  - Trains A3C/DQN agents                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Camera not working on phone?
1. **Use HTTPS**: Some browsers require HTTPS for camera access
   - For local testing, use Chrome and enable `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
   - Add your server URL (e.g., `http://192.168.1.100:5000`)
   
2. **Same WiFi network**: Phone and server must be on same network

3. **Firewall**: Allow port 5000 through firewall
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="Camera Server" dir=in action=allow protocol=tcp localport=5000
   ```

### Detection not accurate?
1. **Calibrate HSV colors** for your lighting conditions
2. **Adjust confidence threshold** in config
3. **Use YOLOv8m or YOLOv8l** for better accuracy (slower)

### Slow processing?
1. Reduce processing FPS (currently 5)
2. Use YOLOv8n (nano) model
3. Reduce image resolution

---

## Integration with RL Training

### Using Camera Data for Training

```python
from app.services.vision.hybrid_environment import HybridEnvironment

# Create hybrid environment
env = HybridEnvironment(
    mode='hybrid',  # or 'real_world' for camera-only
    config={
        'sim_weight': 0.7,
        'real_weight': 0.3,
        'camera': {
            'server_url': 'http://localhost:5000'
        }
    }
)

# Start environment
env.start()

# Training loop
for episode in range(100):
    state = env.get_state()
    
    for step in range(1000):
        action = agent.get_action(state)
        next_state, reward, done, info = env.step(action)
        
        agent.store_experience(state, action, reward, next_state, done)
        agent.update()
        
        state = next_state
        
        if done:
            break

env.stop()
```

### Collecting Training Data

```python
import requests

# Start collection
requests.post('http://localhost:5000/api/collect/start')

# ... point camera at traffic for desired duration ...

# Stop collection
requests.post('http://localhost:5000/api/collect/stop')

# Export data
data = requests.get('http://localhost:5000/api/collect/export').json()
print(f"Collected {data['num_samples']} samples")

# Save to file
import json
with open('training_data.json', 'w') as f:
    json.dump(data, f)
```

---

## Files Structure

```
backend/app/services/
├── vision/
│   ├── __init__.py
│   ├── signal_detector.py      # Traffic light detection
│   ├── vehicle_detector.py     # YOLOv8 vehicle detection
│   ├── camera_stream.py        # Camera input handling
│   ├── data_processor.py       # Vision → RL data conversion
│   └── hybrid_environment.py   # Combined SUMO + Camera env
│
└── mobile_camera/
    ├── mobile_camera_server.py # Flask WebSocket server
    └── templates/
        └── dashboard.html      # Monitoring dashboard
```

---

## Success Criteria

✅ Mobile camera streams to server  
✅ Traffic signals detected and timed  
✅ Vehicles counted per lane  
✅ Queue length calculated  
✅ Data converts to RL state format  
✅ Can train RL agent on real data  
✅ Dashboard shows live statistics  

---

## Next Steps

1. **Calibrate for your location** - Adjust HSV ranges for local lighting
2. **Collect baseline data** - Record 30 mins of normal traffic
3. **Train on real data** - Use collected data to validate RL model
4. **Compare performance** - Simulation vs real-world metrics
5. **Deploy hybrid system** - Use both data sources for robust training
