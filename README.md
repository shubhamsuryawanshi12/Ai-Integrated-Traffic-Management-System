# UrbanFlow - AI-Powered Traffic Management

## Prerequisites
- Node.js (v18+)
- Python (v3.11+)
- **Docker Desktop** (Recommended) OR **SUMO** (Manual install required for local run)

## Quick Start (Docker)
1. Run `docker-compose up --build`
2. Open `http://localhost:3000`

## Quick Start (Local)
1. Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
2. Frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```
3. SUMO:
   Ensure `sumo` is in your PATH.
   Run `python backend/generate_sumo_network.py` to create simulation files.
