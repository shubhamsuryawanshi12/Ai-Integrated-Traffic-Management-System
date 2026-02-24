# UrbanFlow — Complete System Data Documentation

> **Project**: UrbanFlow - AI-Powered Adaptive Traffic Signal Control  
> **Generated**: 2026-02-20  
> **Version**: 1.0

---

## 1. System Architecture Overview

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Mobile Phone   │────▶│  Camera Server (5000) │────▶│  React Dashboard │
│  (Camera Feed)   │◀────│  Flask + SocketIO     │     │  (Port 3001)     │
└─────────────────┘     └──────────────────────┘     └────────┬────────┘
                                                              │
                        ┌──────────────────────┐              │
                        │  Simulation API (8000)│◀─────────────┘
                        │  FastAPI + SocketIO   │
                        │  + SUMO Environment   │
                        │  + RL Agent (A2C)     │
                        └──────────────────────┘
```

### Three Running Services:
| Service | Port | Technology | Purpose |
|---------|------|------------|---------|
| Camera Server | 5000 | Flask + SocketIO + OpenCV | Real-time video processing |
| Simulation API | 8000 | FastAPI + SocketIO | Traffic simulation + AI control |
| Frontend | 3001 | React.js | Dashboard visualization |

---

## 2. Data Sources

### 2.1 Mobile Camera Feed (Real-Time)
- **Input**: Base64-encoded JPEG frames from phone camera
- **Transport**: Socket.IO (`frame` event)
- **Frame Rate**: ~1-5 FPS (depends on phone/network)
- **Resolution**: Variable (phone camera native)
- **Format**:
```json
{
  "image": "<base64-encoded-jpeg-string>",
  "timestamp": 1708456789000
}
```

### 2.2 SUMO Traffic Simulation (Mock Mode)
- **Source**: `app/services/sumo/environment.py`
- **Mode**: Currently running in **MOCK MODE** (SUMO not installed)
- **Intersections**: 4 (INT_1, INT_2, INT_3, INT_4)
- **Mock Data Ranges**:

| Parameter | Min | Max | Unit |
|-----------|-----|-----|------|
| Queue Length | 0 | 20 | vehicles |
| Vehicle Count | 5 | 50 | vehicles |
| Avg Speed | 5 | 15 | m/s |
| Phase | 0 | 2 | enum (0=Green, 1=Yellow, 2=Red) |

### 2.3 SUMO Network Files (For Full Simulation)
```
sumo_files/
├── config/
│   └── simulation.sumocfg        # SUMO configuration
├── networks/
│   └── simple_grid.net.xml       # Road network (4-intersection grid)
└── routes/
    └── traffic_routes.rou.xml    # Vehicle routes & demand
```

---

## 3. Detection Data (Computer Vision)

### 3.1 Vehicle Detection Output
- **Detector**: Motion-based (BackgroundSubtractorMOG2) — fallback for missing YOLO
- **Source**: `app/services/vision/vehicle_detector.py`
- **Output Format**:
```json
{
  "timestamp": "2026-02-20T22:30:00.123456",
  "frame_number": 42,
  "total_vehicles": 5,
  "lanes": {
    "north": {
      "vehicle_count": 2,
      "queue_length": 0,
      "avg_speed": 8.5,
      "vehicles": [
        {
          "id": 0,
          "class_id": 2,
          "class_name": "car",
          "confidence": 1.0,
          "bbox": [120, 80, 220, 160],
          "center": [170, 120]
        }
      ]
    },
    "south": { "vehicle_count": 1, "queue_length": 0, "avg_speed": 12.3, "vehicles": [...] },
    "east":  { "vehicle_count": 1, "queue_length": 0, "avg_speed": 7.1, "vehicles": [...] },
    "west":  { "vehicle_count": 1, "queue_length": 0, "avg_speed": 9.8, "vehicles": [...] }
  },
  "vehicle_types": { "car": 5 },
  "all_detections": [...],
  "processing_fps": 1.5
}
```

### 3.2 Lane Assignment
- Frame is divided into **4 quadrants** (North/South/East/West)
- Each detected vehicle is assigned to a lane based on its center point:
```
┌───────────┬───────────┐
│           │           │
│   NORTH   │   EAST    │
│  (top-L)  │  (top-R)  │
│           │           │
├───────────┼───────────┤
│           │           │
│   WEST    │   SOUTH   │
│  (bot-L)  │  (bot-R)  │
│           │           │
└───────────┴───────────┘
```

### 3.3 Signal Detection Output
- **Detector**: HSV Color Detection + Hough Circle Transform
- **Source**: `app/services/vision/signal_detector.py`
- **Output Format**:
```json
{
  "timestamp": "2026-02-20T22:30:00.123456",
  "signal_state": "red",
  "phase_duration": 12.5,
  "cycle_time": 45.0,
  "confidence": 0.85,
  "detections": {
    "red":    { "detected": true,  "confidence": 0.85, "circles": [[150, 50, 15]] },
    "yellow": { "detected": false, "confidence": 0.0,  "circles": [] },
    "green":  { "detected": false, "confidence": 0.0,  "circles": [] }
  },
  "state_history": [
    { "state": "green",  "timestamp": "..." },
    { "state": "yellow", "timestamp": "..." },
    { "state": "red",    "timestamp": "..." }
  ]
}
```

### 3.4 HSV Color Ranges for Signal Detection
| Color | H Low | H High | S Low | S High | V Low | V High |
|-------|-------|--------|-------|--------|-------|--------|
| Red (range 1) | 0 | 10 | 100 | 255 | 100 | 255 |
| Red (range 2) | 160 | 180 | 100 | 255 | 100 | 255 |
| Yellow | 15 | 35 | 100 | 255 | 100 | 255 |
| Green | 40 | 90 | 50 | 255 | 50 | 255 |

---

## 4. RL Agent Data (Reinforcement Learning)

### 4.1 State Vector (Input to AI)
- **Dimension**: 32 features (padded with zeros)
- **Per Intersection**: 4 features × 4 intersections = 16 core features
- **Format**:
```
State = [
  # INT_1
  queue_length_1, vehicle_count_1, avg_speed_1, phase_1,
  # INT_2
  queue_length_2, vehicle_count_2, avg_speed_2, phase_2,
  # INT_3
  queue_length_3, vehicle_count_3, avg_speed_3, phase_3,
  # INT_4
  queue_length_4, vehicle_count_4, avg_speed_4, phase_4,
  # Padding
  0.0, 0.0, ..., 0.0  (16 zeros)
]
```

### 4.2 Action Space
| Action | Meaning |
|--------|---------|
| 0 | 🟢 Green Phase |
| 1 | 🟡 Yellow Phase |
| 2 | 🔴 Red Phase |
| 3 | 🟢 Extended Green |

### 4.3 Reward Function
```python
reward = -(total_waiting_time + 10 * total_stopped_vehicles)
```
- **Goal**: Minimize waiting time and stopped vehicles
- **Range**: Typically -100 to -10 per step

### 4.4 Neural Network Architecture (Actor-Critic A2C)
```
Input (32) → Linear(128) → ReLU
                ├── Actor Head  → Linear(4) → Softmax → Action Probabilities
                └── Critic Head → Linear(1) → State Value
```
- **Optimizer**: Adam (lr=0.001)
- **Discount Factor (γ)**: 0.99
- **Current Mode**: Dummy (random actions) — PyTorch not installed

---

## 5. API Endpoints & Response Data

### 5.1 Camera Server APIs (Port 5000)

#### `GET /api/status`
```json
{
  "status": "running",
  "cv_available": true,
  "frame_count": 42,
  "connected_clients": 1
}
```

#### `GET /api/debug`
```json
{
  "cv_available": true,
  "frame_count": 42,
  "total_vehicles": 5,
  "signal_state": "red",
  "lane_keys": ["north", "south", "east", "west"],
  "status": "ok"
}
```

#### `GET /api/latest`
```json
{
  "timestamp": "2026-02-20T22:30:00",
  "frame": 42,
  "signal": { "state": "red", "confidence": 0.85, "duration": 12.5 },
  "vehicles": {
    "total": 5,
    "by_lane": { "north": 2, "south": 1, "east": 1, "west": 1 },
    "queue_length": 0,
    "avg_speed": 8.5
  },
  "metrics": { "fps": 1.5 }
}
```

#### `GET /api/rl_state`
```json
{
  "state": [0.0, 0.0, 0.0, ...],
  "reward": 0.0,
  "timestamp": "2026-02-20T22:30:00"
}
```

### 5.2 Simulation APIs (Port 8000)

#### `POST /api/v1/simulation/start`
```json
// Request: mode = "simulation" | "real_world" | "green_wave"
// Response:
{ "status": "started", "mode": "simulation" }
```

#### `POST /api/v1/simulation/stop`
```json
{ "status": "stopped" }
```

#### `GET /api/v1/simulation/status`
```json
{ "running": true }
```

### 5.3 WebSocket Events (Socket.IO)

#### Camera Server (Port 5000)
| Event | Direction | Data |
|-------|-----------|------|
| `connect` | Client→Server | — |
| `frame` | Client→Server | `{ "image": "<base64>" }` |
| `detection_result` | Server→Client | Full detection JSON |
| `status` | Server→Client | `{ "connected": true }` |

#### Simulation API (Port 8000)
| Event | Direction | Data |
|-------|-----------|------|
| `traffic_update` | Server→Client | Intersection states + snapshot |

---

## 6. Simulation Broadcast Data (WebSocket)

The simulation broadcasts this data every **2 seconds** to all connected dashboard clients:

```json
{
  "intersections": [
    {
      "id": "INT_1",
      "name": "Signal INT_1",
      "current_status": { "phase": "green" },
      "traffic_data": {
        "vehicle_count": 25,
        "average_wait_time": 8.5,
        "avg_speed": 12.3
      },
      "location": { "x": 0, "y": 0 }
    },
    {
      "id": "INT_2",
      "name": "Signal INT_2",
      "current_status": { "phase": "red" },
      "traffic_data": {
        "vehicle_count": 40,
        "average_wait_time": 15.2,
        "avg_speed": 6.1
      },
      "location": { "x": 150, "y": 0 }
    },
    {
      "id": "INT_3",
      "name": "Signal INT_3",
      "current_status": { "phase": "yellow" },
      "traffic_data": {
        "vehicle_count": 12,
        "average_wait_time": 3.8,
        "avg_speed": 14.0
      },
      "location": { "x": 0, "y": 150 }
    },
    {
      "id": "INT_4",
      "name": "Signal INT_4",
      "current_status": { "phase": "green" },
      "traffic_data": {
        "vehicle_count": 30,
        "average_wait_time": 10.1,
        "avg_speed": 9.5
      },
      "location": { "x": 150, "y": 150 }
    }
  ],
  "snapshot": {
    "timestamp": 1708456789000,
    "avg_queue_length": 9.4
  }
}
```

---

## 7. Vehicle Detection Parameters

### 7.1 Motion Detector (Current Fallback)
| Parameter | Value | Description |
|-----------|-------|-------------|
| `history` | 200 | Background model memory (frames) |
| `varThreshold` | 25 | Sensitivity (lower = more sensitive) |
| `detectShadows` | false | Ignore shadow artifacts |
| `min_area` | 500 px² | Min contour area to count as vehicle |
| `max_area` | 50% of frame | Max contour (filters full-frame noise) |
| `aspect_ratio` | 0.2 – 4.0 | Vehicle shape filter |

### 7.2 YOLO Model (When Available)
| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | yolov8n.pt | YOLOv8 Nano (6.5MB, fast) |
| `confidence` | 0.5 | Min detection confidence |
| `iou_threshold` | 0.45 | Non-max suppression overlap |
| `img_size` | 640 | Input image size |

### 7.3 COCO Vehicle Class IDs (YOLO)
| Class ID | Vehicle Type |
|----------|-------------|
| 1 | Bicycle |
| 2 | Car |
| 3 | Motorcycle |
| 5 | Bus |
| 7 | Truck |

---

## 8. Configuration Parameters

### 8.1 Server Configuration
| Parameter | Value | File |
|-----------|-------|------|
| Camera Server Port | 5000 | `mobile_camera_server.py` |
| Simulation API Port | 8000 | `app/main.py` |
| Frontend Port | 3001 | `package.json` |
| Max Frame Size | 10 MB | `mobile_camera_server.py` |
| Ping Timeout | 60s | `mobile_camera_server.py` |
| Async Mode | eventlet | `mobile_camera_server.py` |
| CORS | `*` (all origins) | Both servers |

### 8.2 Simulation Configuration
| Parameter | Value |
|-----------|-------|
| Intersections | 4 (INT_1 to INT_4) |
| Grid Layout | 2×2 (150px spacing) |
| Step Interval | 1.0 second |
| Broadcast Interval | 2.0 seconds |
| Simulation Weight | 0.7 |
| Real-World Weight | 0.3 |

### 8.3 Speed Estimation
| Parameter | Value |
|-----------|-------|
| `pixels_per_meter` | 10 |
| `stopped_threshold` | 2.0 m/s |
| Motion fallback speed | 5.0 – 15.0 m/s (random) |

---

## 9. Data Flow Diagram

```
PHONE CAMERA
     │
     │ Socket.IO: "frame" event
     │ { image: base64 }
     ▼
CAMERA SERVER (Port 5000)
     │
     ├──▶ VehicleDetector.detect(frame)
     │         │
     │         ├── YOLO model (if available)
     │         └── Motion Detector (fallback)
     │                │
     │                ▼
     │    { total_vehicles, lanes, queue_length, avg_speed }
     │
     ├──▶ SignalDetector.detect(frame)
     │         │
     │         ├── HSV mask → Red/Yellow/Green
     │         └── Hough Circle Transform
     │                │
     │                ▼
     │    { signal_state, phase_duration, cycle_time }
     │
     ├──▶ Socket.IO emit: "detection_result"
     │         └──▶ Phone receives result
     │
     └──▶ REST API: /api/latest, /api/debug, /api/rl_state
               └──▶ Dashboard polls data


SIMULATION ENGINE (Port 8000)
     │
     ├──▶ SumoEnvironment.get_state()
     │         │
     │         └── Mock: random traffic data
     │             OR SUMO TraCI: real simulation
     │
     ├──▶ RLAgent.get_action(state)
     │         │
     │         └── Dummy: random action (0-3)
     │             OR A2C Neural Network → optimal action
     │
     ├──▶ SumoEnvironment.apply_actions(actions)
     │
     └──▶ WebSocket broadcast: "traffic_update"
               └──▶ Dashboard receives intersection data


REACT DASHBOARD (Port 3001)
     │
     ├── Receives WebSocket "traffic_update" from Port 8000
     ├── Polls REST APIs from Port 5000
     └── Renders: Signal status, Vehicle counts, Lane stats,
                  Activity log, Vehicle count history chart
```

---

## 10. File Structure

```
d:\Hackathon\
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI server entry point
│   │   ├── api/routes/
│   │   │   ├── simulation.py                # Simulation start/stop/status APIs
│   │   │   └── traffic.py                   # Traffic data APIs
│   │   ├── core/
│   │   │   └── socket_manager.py            # WebSocket broadcast manager
│   │   └── services/
│   │       ├── ai_engine/
│   │       │   └── rl_agent.py              # A2C Reinforcement Learning Agent
│   │       ├── mobile_camera/
│   │       │   └── mobile_camera_server.py  # Flask Camera Server (Port 5000)
│   │       ├── sumo/
│   │       │   └── environment.py           # SUMO simulation environment
│   │       └── vision/
│   │           ├── vehicle_detector.py      # Vehicle detection (YOLO/Motion)
│   │           ├── signal_detector.py       # Traffic signal color detection
│   │           ├── camera_stream.py         # Mobile camera stream handler
│   │           ├── data_processor.py        # Data processing utilities
│   │           └── hybrid_environment.py    # Hybrid sim+real environment
│   ├── sumo_files/
│   │   ├── config/simulation.sumocfg
│   │   ├── networks/simple_grid.net.xml
│   │   └── routes/traffic_routes.rou.xml
│   ├── train_agent.py                       # RL training script
│   ├── yolov8n.pt                           # YOLOv8 Nano model weights (6.5MB)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/Dashboard.jsx              # Main dashboard page
│   │   ├── services/api.js                  # API service layer
│   │   └── context/AuthContext.jsx
│   └── package.json
└── SYSTEM_DATA_DOCUMENTATION.md             # This file
```

---

## 11. Current System Status

| Component | Status | Mode |
|-----------|--------|------|
| Camera Server | ✅ Running | OpenCV Motion Detection |
| Simulation API | ✅ Running | Mock Mode (no SUMO) |
| RL Agent | ✅ Running | Dummy Mode (no PyTorch) |
| Frontend | ✅ Running | Connected |
| YOLO Model | ⚠️ File exists (`yolov8n.pt`) but `ultralytics` not installed |
| SUMO | ❌ Not installed | Mock data generated |
| PyTorch | ❌ Not installed | Random actions |

---

*End of Documentation*
