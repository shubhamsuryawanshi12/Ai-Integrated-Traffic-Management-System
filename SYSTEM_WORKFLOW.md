# UrbanFlow — Complete System Workflow

> **AI-Powered Adaptive Traffic Signal Control System**  
> End-to-end workflow from camera input to intelligent signal optimization

---

## 🎯 What Does UrbanFlow Do?

UrbanFlow is a **smart traffic management system** that:
1. **SEES** traffic using a mobile phone camera (Computer Vision)
2. **THINKS** about the best signal timing using AI (Reinforcement Learning)
3. **ACTS** by optimizing traffic signal phases to reduce congestion
4. **SHOWS** everything on a real-time dashboard

---

## 🔄 Complete System Workflow

### PHASE 1: DATA COLLECTION (The Eyes)

```
📱 Your Phone Camera
        │
        │  Step 1: Phone opens http://<PC-IP>:5000
        │  Step 2: Browser requests camera access
        │  Step 3: Camera starts capturing frames
        │
        ▼
┌─────────────────────────────┐
│  JavaScript on Phone        │
│                             │
│  Every ~200ms:              │
│  1. Capture video frame     │
│  2. Convert to Base64 JPEG  │
│  3. Send via Socket.IO      │
│     Event: "frame"          │
│     Data: { image: "..." }  │
└─────────────┬───────────────┘
              │
              │ WiFi (Same Network)
              ▼
┌─────────────────────────────┐
│  Camera Server (Port 5000)  │
│  Flask + Socket.IO          │
│  + eventlet async           │
│                             │
│  Receives "frame" event     │
│  Decodes Base64 → OpenCV    │
│  numpy image array          │
└─────────────┬───────────────┘
              │
              ▼
        PHASE 2: PERCEPTION
```

---

### PHASE 2: PERCEPTION (The Brain's Eyes)

The server processes each frame through **TWO parallel detectors**:

```
                    ┌─── Frame (OpenCV Image) ───┐
                    │                             │
                    ▼                             ▼
        ┌───────────────────┐         ┌───────────────────┐
        │ VEHICLE DETECTOR  │         │ SIGNAL DETECTOR   │
        │                   │         │                   │
        │ Method: Motion    │         │ Method: HSV Color │
        │ Detection (MOG2)  │         │ + Circle Detection│
        │                   │         │                   │
        │ How it works:     │         │ How it works:     │
        │ 1. Background     │         │ 1. Convert frame  │
        │    subtraction    │         │    to HSV color   │
        │ 2. Find moving    │         │ 2. Apply masks:   │
        │    blobs          │         │    Red/Yellow/     │
        │ 3. Filter by size │         │    Green ranges   │
        │    & shape        │         │ 3. Find circles   │
        │ 4. Count as       │         │    (Hough Trans.) │
        │    vehicles       │         │ 4. Determine      │
        │                   │         │    signal state   │
        └───────┬───────────┘         └───────┬───────────┘
                │                             │
                ▼                             ▼
        ┌───────────────┐             ┌───────────────┐
        │ Output:       │             │ Output:       │
        │ • 5 cars      │             │ • State: RED  │
        │ • North: 2    │             │ • Duration:   │
        │ • South: 1    │             │   12.5 sec    │
        │ • East: 1     │             │ • Confidence: │
        │ • West: 1     │             │   0.85        │
        │ • Speed: 8m/s │             │ • Cycle: 45s  │
        │ • Queue: 0    │             │               │
        └───────┬───────┘             └───────┬───────┘
                │                             │
                └──────────┬──────────────────┘
                           │
                           ▼
                  COMBINED RESULT
```

#### Vehicle Detection — Step by Step:
```
Frame 1: ████████████████  ← Background model learns "empty road"
Frame 2: ████████████████
Frame 3: ████🚗██████████  ← New pixels detected! (car entered)
                │
                ▼
         Background Subtraction (MOG2)
                │
                ▼
         Binary Mask: ░░░░████░░░░░░░░  ← White = "new/moving"
                │
                ▼
         Morphology Cleanup (remove noise)
                │
                ▼
         Find Contours
                │
                ▼
         Filter: area > 500px² AND aspect_ratio 0.2-4.0
                │
                ▼
         Result: 1 vehicle detected at [x, y, w, h]
```

#### Signal Detection — Step by Step:
```
Frame: ┌────────────────┐
       │    🔴          │  ← Red traffic light visible
       │    ⚫          │
       │    ⚫          │
       │                │
       │  🚗  🚗  🚗   │
       └────────────────┘
                │
                ▼
         Convert BGR → HSV colorspace
                │
                ▼
         Apply RED mask (H: 0-10 & 160-180, S: 100-255, V: 100-255)
                │
                ▼
         Detect circles using HoughCircles
                │
                ▼
         Found red circle at (150, 50, radius=15)
                │
                ▼
         Result: signal_state = "RED", confidence = 0.85
```

---

### PHASE 3: LANE ASSIGNMENT & METRICS

```
┌─────────────── Camera Frame ───────────────────┐
│                                                  │
│           ┌─────────┬─────────┐                  │
│           │         │         │                  │
│           │  NORTH  │  EAST   │    ← Top half    │
│           │  🚗🚗   │  🚗     │                  │
│           │         │         │                  │
│           ├─────────┼─────────┤ ← y = height/2  │
│           │         │         │                  │
│           │  WEST   │  SOUTH  │    ← Bottom half │
│           │  🚗     │  🚗     │                  │
│           │         │         │                  │
│           └─────────┴─────────┘                  │
│                                                  │
│           x = width/2                            │
└──────────────────────────────────────────────────┘

Rules:
  • center_x < width/2  AND center_y < height/2  →  NORTH
  • center_x >= width/2 AND center_y < height/2  →  EAST
  • center_x < width/2  AND center_y >= height/2 →  WEST
  • center_x >= width/2 AND center_y >= height/2 →  SOUTH

After lane assignment:
  ┌──────────────────────────────────────────┐
  │ Per Lane Metrics:                         │
  │   • vehicle_count: How many cars          │
  │   • queue_length:  How many are stopped   │
  │   • avg_speed:     Average speed (m/s)    │
  │     (Motion detector → speed ~5-15 m/s)   │
  └──────────────────────────────────────────┘
```

---

### PHASE 4: AI DECISION MAKING (The Brain)

```
┌────────────────────────────────────────────────────────────┐
│                  REINFORCEMENT LEARNING ENGINE              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ STATE VECTOR (What the AI "sees"):                   │   │
│  │                                                      │   │
│  │ [queue₁, vehicles₁, speed₁, phase₁,  ← INT_1       │   │
│  │  queue₂, vehicles₂, speed₂, phase₂,  ← INT_2       │   │
│  │  queue₃, vehicles₃, speed₃, phase₃,  ← INT_3       │   │
│  │  queue₄, vehicles₄, speed₄, phase₄,  ← INT_4       │   │
│  │  0, 0, 0, 0, 0, 0, 0, 0,             ← padding     │   │
│  │  0, 0, 0, 0, 0, 0, 0, 0]             ← padding     │   │
│  │                                                      │   │
│  │ Total: 32 features                                   │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           ACTOR-CRITIC NEURAL NETWORK (A2C)          │  │
│  │                                                      │  │
│  │  Input Layer (32 neurons)                            │  │
│  │       │                                              │  │
│  │       ▼                                              │  │
│  │  Hidden Layer (128 neurons + ReLU activation)        │  │
│  │       │                                              │  │
│  │       ├──────────────┐                               │  │
│  │       │              │                               │  │
│  │       ▼              ▼                               │  │
│  │  ┌─────────┐  ┌──────────┐                           │  │
│  │  │ ACTOR   │  │ CRITIC   │                           │  │
│  │  │ (4 out) │  │ (1 out)  │                           │  │
│  │  │ Softmax │  │ Value    │                           │  │
│  │  └────┬────┘  └────┬─────┘                           │  │
│  │       │             │                                │  │
│  │       ▼             ▼                                │  │
│  │  Probabilities    State                              │  │
│  │  [0.4, 0.1,      Value                              │  │
│  │   0.3, 0.2]      = -25.3                            │  │
│  │       │                                              │  │
│  │       ▼                                              │  │
│  │  Sample Action                                       │  │
│  │  → Action = 0                                        │  │
│  │  → 🟢 GREEN                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ REWARD CALCULATION:                                  │  │
│  │                                                      │  │
│  │ reward = -(waiting_time + 10 × stopped_vehicles)     │  │
│  │                                                      │  │
│  │ Example:                                             │  │
│  │   waiting_time = 45 sec, stopped = 3 cars            │  │
│  │   reward = -(45 + 10×3) = -75                        │  │
│  │                                                      │  │
│  │ Goal: MAXIMIZE reward (minimize waiting/stopped)     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

#### How the AI Learns (Training Loop):
```
┌──────────────────────────────────────────────────────┐
│                 TRAINING CYCLE                        │
│                                                      │
│  Step 1: OBSERVE  → Get traffic state                │
│  Step 2: DECIDE   → Neural network picks action      │
│  Step 3: ACT      → Change traffic signal            │
│  Step 4: MEASURE  → Calculate reward                 │
│  Step 5: LEARN    → Update neural network weights    │
│                                                      │
│  Repeat 1000× per episode, 100+ episodes             │
│                                                      │
│  Over time:                                          │
│    Episode 1:   reward = -95  (random, bad)          │
│    Episode 10:  reward = -72  (learning patterns)    │
│    Episode 50:  reward = -45  (getting smarter)      │
│    Episode 100: reward = -28  (optimized!)           │
└──────────────────────────────────────────────────────┘
```

---

### PHASE 5: SIGNAL CONTROL (The Action)

```
AI Decision: Action = 0 (GREEN for INT_1)
     │
     ▼
┌──────────────────────────────────────────────┐
│ Signal Controller                             │
│                                               │
│ SUMO Mode:                                    │
│   traci.trafficlight.setPhase("INT_1", 0)     │
│   → Changes actual simulation signal          │
│                                               │
│ Mock Mode (Current):                          │
│   Phase stored in memory                      │
│   → Broadcast to dashboard                    │
│                                               │
│ Real-World Mode (Future):                     │
│   → Could send to IoT traffic controller      │
│   → Via MQTT, HTTP, or serial port             │
└──────────────────────────────────────────────┘

Signal Phases:
  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
  │ 🟢  │→│ 🟡  │→│ 🔴  │→│ 🟢+ │
  │Green│  │Yell.│  │ Red │  │Ext. │
  │  0  │  │  1  │  │  2  │  │  3  │
  └─────┘  └─────┘  └─────┘  └─────┘
```

---

### PHASE 6: DASHBOARD VISUALIZATION (The Display)

```
┌─────────────────────────────────────────────────────────────┐
│  React Dashboard (http://localhost:3001)                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ TRAFFIC       │  │ VEHICLE      │  │ LANE          │      │
│  │ SIGNAL        │  │ DETECTION    │  │ STATISTICS    │      │
│  │               │  │              │  │               │      │
│  │  🔴 🟡 🟢    │  │ Total: 5     │  │ N: 2  S: 1   │      │
│  │               │  │ Queue: 0     │  │ E: 1  W: 1   │      │
│  │ Phase: RED    │  │ Speed: 8m/s  │  │               │      │
│  │ Duration: 12s │  │ FPS: 1.5     │  │ Queue: 0 each │      │
│  │ Cycle: 45s    │  │              │  │               │      │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────────────┐  ┌────────────────────────┐       │
│  │ VEHICLE COUNT HISTORY │  │ ACTIVITY LOG           │       │
│  │                       │  │                        │       │
│  │  5│    ╱╲             │  │ 10:30 PM Signal: RED   │       │
│  │  4│   ╱  ╲   ╱╲      │  │ 10:30 PM Vehicles: 5   │       │
│  │  3│  ╱    ╲ ╱  ╲     │  │ 10:29 PM Signal: GREEN │       │
│  │  2│ ╱      ╳    ╲    │  │ 10:29 PM Vehicles: 3   │       │
│  │  1│╱              ╲   │  │ 10:28 PM Data started  │       │
│  │  0└──────────────── │  │ 10:28 PM Dashboard init │       │
│  │   Vehicles ■ Queue ■ │  │                        │       │
│  └──────────────────────┘  └────────────────────────┘       │
│                                                              │
│  Data Sources:                                               │
│  ├── WebSocket from Port 8000 → Intersection states          │
│  ├── REST API from Port 5000  → Camera detection results     │
│  └── Updates every 2 seconds                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔁 Complete Loop (One Cycle)

```
TIME ──────────────────────────────────────────────────────────▶

t=0.0s   📱 Phone captures frame
         │
t=0.1s   │──▶ Socket.IO sends to server
         │
t=0.2s   │──▶ Server decodes frame
         │
t=0.3s   │──▶ VehicleDetector: "5 cars detected"
         │    SignalDetector:  "RED signal"
         │
t=0.4s   │──▶ Lane assignment: N=2, S=1, E=1, W=1
         │    Speed estimation: 8.5 m/s avg
         │    Queue calculation: 0 stopped
         │
t=0.5s   │──▶ Emit "detection_result" → Phone
         │    Update /api/latest endpoint
         │
t=1.0s   🤖 Simulation step
         │──▶ RLAgent reads state [queue, vehicles, speed, phase]×4
         │──▶ Neural Network → Action = 0 (GREEN)
         │──▶ Apply action to intersection
         │──▶ Calculate reward = -45
         │
t=2.0s   📡 WebSocket broadcast
         │──▶ Send intersection data to Dashboard
         │
t=2.0s   📊 Dashboard updates
         │──▶ Signal indicator changes
         │──▶ Vehicle count updates
         │──▶ Chart adds new data point
         │──▶ Activity log entry added
         │
t=2.0s   📱 Next frame arrives...
         └──▶ Cycle repeats ♻️
```

---

## 🧩 Three Operating Modes

### Mode 1: SIMULATION (Current)
```
┌─────────────────────────────────────────┐
│  SUMO Simulator (or Mock)               │
│  Generates fake traffic data            │
│  AI optimizes signal timing             │
│  Dashboard shows simulated results      │
│                                          │
│  Use: Testing & Training the AI          │
└─────────────────────────────────────────┘
```

### Mode 2: REAL-WORLD
```
┌─────────────────────────────────────────┐
│  Phone Camera → Real traffic video      │
│  OpenCV detects real vehicles           │
│  AI suggests optimal signal timing      │
│  Dashboard shows live detection         │
│                                          │
│  Use: Live deployment at intersection   │
└─────────────────────────────────────────┘
```

### Mode 3: HYBRID (Best of Both)
```
┌─────────────────────────────────────────┐
│  SUMO simulation (70% weight)           │
│  + Phone camera (30% weight)            │
│  AI uses both data sources              │
│  More robust than either alone          │
│                                          │
│  Use: Calibrating simulation with       │
│       real-world data                    │
└─────────────────────────────────────────┘
```

---

## 🏗️ Technology Stack

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│  React.js │ Socket.IO Client │ Chart.js │ CSS       │
├─────────────────────────────────────────────────────┤
│                 BACKEND SERVER 1                     │
│  Flask │ Socket.IO │ eventlet │ OpenCV │ NumPy       │
├─────────────────────────────────────────────────────┤
│                 BACKEND SERVER 2                     │
│  FastAPI │ Socket.IO │ uvicorn │ asyncio             │
├─────────────────────────────────────────────────────┤
│                    AI ENGINE                         │
│  PyTorch (A2C) │ Actor-Critic │ Policy Gradient      │
├─────────────────────────────────────────────────────┤
│              COMPUTER VISION                         │
│  OpenCV │ MOG2 Background Subtraction │ HSV Detection│
│  YOLOv8 (when available) │ Hough Circle Transform    │
├─────────────────────────────────────────────────────┤
│              SIMULATION                              │
│  SUMO (when available) │ TraCI API │ Mock Environment │
└─────────────────────────────────────────────────────┘
```

---

## 📌 Key Innovation

```
Traditional Traffic Lights:          UrbanFlow:
┌──────────────────────┐             ┌──────────────────────┐
│ Fixed Timer           │             │ AI-Adaptive           │
│                       │             │                       │
│ Green: 30s always     │             │ Green: 15-60s         │
│ Red:   30s always     │             │ (based on demand)     │
│                       │             │                       │
│ No awareness of       │      vs     │ Sees actual traffic   │
│ actual traffic        │             │ via camera            │
│                       │             │                       │
│ Same timing at        │             │ Adapts in real-time   │
│ 3 AM and 5 PM         │             │ Less wait at 3 AM     │
│                       │             │ More green at 5 PM    │
│                       │             │                       │
│ Result: Wasted time   │             │ Result: 30-40% less   │
│ and fuel              │             │ waiting time          │
└──────────────────────┘             └──────────────────────┘
```

---

*Generated for UrbanFlow Traffic Management System — Hackathon 2026*
