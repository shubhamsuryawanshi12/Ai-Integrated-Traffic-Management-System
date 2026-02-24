# How to Run UrbanFlow

## Prerequisites
- **Python 3.12+**
- **Node.js & npm**
- **PowerShell** (Windows)

## One-Time Setup

### Backend (Python virtual environment)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-windows.txt
```

### Frontend (Node modules)
```powershell
cd frontend
npm install
```

## 1. Start the Backend Server (Terminal 1)
This runs the main Traffic Management System (API + Simulation + AI).

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*Access:* [http://localhost:8000](http://localhost:8000)

## 2. Start the Frontend Dashboard (Terminal 2)
This runs the React-based User Interface.

```powershell
cd frontend
npm start
```
*Access:* [http://localhost:3000](http://localhost:3000)

## 3. (Optional) Start Mobile Camera Server (Terminal 3)
This runs the separate service for handling mobile camera streams.

```powershell
cd backend
.venv\Scripts\python.exe app/services/mobile_camera/mobile_camera_server.py
```
*Access:* [http://localhost:5000](http://localhost:5000)

## Usage
1. Open **Frontend** ([localhost:3000](http://localhost:3000)).
2. Click **"Enter Dashboard"**.
3. Click **"START SIMULATION"** to begin the traffic simulation.
4. To test camera integration, open [localhost:5000](http://localhost:5000) on your mobile device (connected to same Wi-Fi) and start streaming. The dashboard will show the "Live Traffic Camera".
