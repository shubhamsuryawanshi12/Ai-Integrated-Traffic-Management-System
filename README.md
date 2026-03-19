# 🚦 UrbanFlow: AI-Integrated Traffic Management system

> **Smart Cities, Smoother Journeys.**  
> An end-to-end, AI-powered traffic optimization suite that leverages Computer Vision, Reinforcement Learning, and Real-time Analytics to solve urban congestion.

---

## 🌟 Key Features

### 🚥 Intelligent Traffic Control
*   **Dynamic Signal Optimization**: Uses Deep Reinforcement Learning (A2C/PPO) to adjust signal timings based on real-time vehicle demand.
*   **Computer Vision Perception**: Real-time vehicle counting and queue detection via standard cameras (including mobile integration).
*   **Multi-Intersection Coordination**: Scalable architecture for managing cross-road networks.

### 🅿️ Smart Parking Ecosystem
*   **Predictive Occupancy**: AI models that forecast parking availability based on historical trends.
*   **Citizen PWA**: Mobile-first application for finding, booking, and navigating to available parking spots.
*   **Owner/Admin Dashboards**: Revenue tracking, permit management, and real-time lot monitoring.

### 🚔 Enforcement & Monitoring
*   **Illegal Parking Detection**: Vision-based detection of vehicles in no-parking zones.
*   **Emergency Vehicle Prioritization**: Automatic detection and green-wave signaling for ambulances and fire trucks.
*   **Analytics Engine**: High-level data visualization for city planners.

---

## 🏗️ Technology Stack

| Layer | Tools & Technologies |
| :--- | :--- |
| **Frontend** | React, Vite, Socket.io-client, TailwindCSS, Chart.js |
| **Backend** | FastAPI (Simulation), Flask (Camera), Python 3.11+ |
| **AI/ML** | PyTorch, YOLOv11 (via Ultralytics), Scikit-Learn |
| **Simulation** | SUMO (Simulation of Urban MObility), TraCI |
| **Infrastructure** | Docker, Nginx, PostgreSQL (Planned) |

---

## 🚀 Getting Started

### 📦 Prerequisites
- **Node.js** (v18+)
- **Python** (v3.11+)
- **Docker Desktop** (Recommended)
- **SUMO** (If running simulation locally without Docker)

### 🛠️ Local Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/shubhamsuryawanshi12/Ai-Integrated-Traffic-Management-System.git
   cd Ai-Integrated-Traffic-Management-System
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### 🏃 Running the Project

Run each in a separate terminal:

*   **API & Simulation**:
    ```bash
    cd backend
    uvicorn app.main:app --reload --port 8000
    ```
*   **Dashboard**:
    ```bash
    cd frontend
    npm run dev
    ```
*   **Mobile Camera Link**:
    ```bash
    cd backend
    python app/services/mobile_camera/mobile_camera_server.py
    ```

---

## 📖 Documentation Index

| Document | Description |
| :--- | :--- |
| [📂 Architecture](03_Architecture.md) | System design, components, and data flow. |
| [🔄 Workflow](SYSTEM_WORKFLOW.md) | Step-by-step logic from camera to signal. |
| [📋 SRS](04_SRS.md) | Software Requirements and Features. |
| [📊 Status](PROJECT_STATUS.md) | Current build status and roadmap. |
| [📱 Mobile Setup](docs/MOBILE_CAMERA_SETUP.md) | Guide for using your phone as a sensor. |

---

## 🌐 Community & Support

*   **Repository**: [shubhamsuryawanshi12/Ai-Integrated-Traffic-Management-System](https://github.com/shubhamsuryawanshi12/Ai-Integrated-Traffic-Management-System)
*   **Project Lead**: Shubham Suryawanshi

*Generated for the 2026 AI Smart City Hackathon*
