# Technology Stack Documentation

## Project Information
| Field | Details |
|-------|---------|
| Project Name | AI-Powered Traffic Management System |
| Tech Stack Version | 1.0 |
| Last Updated | February 2026 |
| Architecture Type | Full-Stack Web Application with AI/ML |

---

## Table of Contents
1. [Technology Stack Overview](#1-technology-stack-overview)
2. [Frontend Technologies](#2-frontend-technologies)
3. [Backend Technologies](#3-backend-technologies)
4. [AI/ML Engine](#4-aiml-engine)
5. [Database & Storage](#5-database--storage)
6. [Traffic Simulation](#6-traffic-simulation)
7. [DevOps & Deployment](#7-devops--deployment)
8. [Development Tools](#8-development-tools)
9. [Technology Justification](#9-technology-justification)
10. [System Integration](#10-system-integration)
11. [Performance Optimization](#11-performance-optimization)

---

## 1. Technology Stack Overview

### 1.1 Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                    │
│         React.js + Firebase Authentication                   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/REST API
┌────────────────────▼────────────────────────────────────────┐
│                   Application Layer                          │
│              Python + FastAPI Backend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ API Routes   │  │ Business     │  │ Authentication│      │
│  │              │  │ Logic        │  │ Middleware    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬───────────┬────────────────────────────┘
                     │           │
        ┌────────────▼───┐   ┌───▼──────────────┐
        │ AI/ML Engine   │   │ Traffic          │
        │ PyTorch + RL   │   │ Simulation       │
        │                │   │ SUMO             │
        └────────────────┘   └──────────────────┘
                     │
        ┌────────────▼────────────────┐
        │   Database Layer            │
        │   Firebase Firestore        │
        │   (NoSQL Database)          │
        └─────────────────────────────┘
                     │
        ┌────────────▼────────────────┐
        │   Containerization          │
        │   Docker + GitHub Actions   │
        └─────────────────────────────┘
```

### 1.2 Technology Summary Table

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | React.js | 18.x | User Interface |
| | Firebase SDK | 10.x | Authentication & Real-time sync |
| | React Router | 6.x | Client-side routing |
| | Material-UI / Tailwind CSS | Latest | UI Components |
| **Backend** | Python | 3.11+ | Primary programming language |
| | FastAPI | 0.109+ | REST API framework |
| | Uvicorn | 0.27+ | ASGI server |
| | Pydantic | 2.x | Data validation |
| **AI/ML** | PyTorch | 2.1+ | Deep learning framework |
| | NumPy | 1.26+ | Numerical computing |
| | Stable-Baselines3 | 2.2+ | RL algorithms (optional) |
| **Database** | Firebase Firestore | Latest | NoSQL database |
| | Firebase Storage | Latest | File storage |
| **Simulation** | SUMO | 1.19+ | Traffic simulation |
| | TraCI | Built-in | SUMO Python interface |
| **DevOps** | Docker | 24+ | Containerization |
| | Docker Compose | 2.x | Multi-container orchestration |
| | GitHub | - | Version control |
| | GitHub Actions | - | CI/CD pipeline |

---

## 2. Frontend Technologies

### 2.1 React.js (v18.x)
**Purpose**: Primary frontend framework for building user interface

**Key Features Used:**
- **Component-Based Architecture**: Modular, reusable UI components
- **Virtual DOM**: Efficient rendering and updates
- **Hooks**: useState, useEffect, useContext, custom hooks
- **React Context API**: Global state management
- **React Suspense & Lazy Loading**: Code splitting and lazy loading

**Project Structure:**
```
src/
├── components/
│   ├── Dashboard/
│   │   ├── TrafficMap.jsx
│   │   ├── RealTimeStats.jsx
│   │   └── AlertPanel.jsx
│   ├── Simulation/
│   │   ├── SimulationControl.jsx
│   │   └── SimulationVisualizer.jsx
│   ├── Analytics/
│   │   ├── TrafficCharts.jsx
│   │   └── PerformanceMetrics.jsx
│   └── Common/
│       ├── Navbar.jsx
│       ├── Sidebar.jsx
│       └── Footer.jsx
├── pages/
│   ├── Home.jsx
│   ├── Dashboard.jsx
│   ├── Simulation.jsx
│   ├── Analytics.jsx
│   └── Settings.jsx
├── services/
│   ├── api.js
│   ├── firebase.js
│   └── auth.js
├── hooks/
│   ├── useAuth.js
│   ├── useTrafficData.js
│   └── useSimulation.js
├── utils/
│   ├── helpers.js
│   └── constants.js
├── context/
│   ├── AuthContext.jsx
│   └── TrafficContext.jsx
└── App.jsx
```

**Key Dependencies:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "firebase": "^10.7.0",
    "axios": "^1.6.0",
    "@mui/material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "recharts": "^2.10.0",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1"
  }
}
```

### 2.2 Firebase SDK (v10.x)
**Purpose**: Authentication, real-time database sync, and hosting

**Firebase Services Used:**

#### 2.2.1 Firebase Authentication
```javascript
// services/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
```

**Authentication Methods:**
- Email/Password authentication
- Google OAuth
- Session management
- Token-based authentication

#### 2.2.2 Firebase Firestore
- Real-time data synchronization
- Offline data persistence
- Real-time listeners for traffic updates

### 2.3 UI Framework & Styling

#### 2.3.1 Material-UI (MUI) v5
**Purpose**: Pre-built React components

**Key Components Used:**
- `Button`, `TextField`, `Card`, `Grid`
- `AppBar`, `Drawer`, `Menu`
- `Table`, `DataGrid`
- `Snackbar`, `Alert`, `Dialog`
- `CircularProgress`, `LinearProgress`

**Theme Customization:**
```javascript
import { createTheme, ThemeProvider } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
});
```

#### 2.3.2 Alternative: Tailwind CSS
**Purpose**: Utility-first CSS framework (if not using MUI)

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#1976d2',
        secondary: '#dc004e',
      },
    },
  },
  plugins: [],
};
```

### 2.4 Data Visualization

#### 2.4.1 Recharts
**Purpose**: Traffic data visualization and charts

**Charts Used:**
- Line Chart: Traffic flow over time
- Bar Chart: Vehicle count per intersection
- Pie Chart: Traffic distribution
- Area Chart: Congestion levels

```javascript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

<LineChart width={600} height={300} data={trafficData}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="time" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Line type="monotone" dataKey="vehicles" stroke="#8884d8" />
</LineChart>
```

#### 2.4.2 React-Leaflet
**Purpose**: Interactive traffic map visualization

**Features:**
- Real-time traffic marker updates
- Heatmap for congestion zones
- Route visualization
- Custom markers for traffic lights

```javascript
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';

<MapContainer center={[51.505, -0.09]} zoom={13}>
  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
  <Marker position={[51.505, -0.09]}>
    <Popup>Traffic Light Status: Green</Popup>
  </Marker>
</MapContainer>
```

### 2.5 State Management

**Approach**: React Context API + Hooks

```javascript
// context/TrafficContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';

const TrafficContext = createContext();

export const TrafficProvider = ({ children }) => {
  const [trafficData, setTrafficData] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);
  
  // Fetch traffic data from backend
  useEffect(() => {
    fetchTrafficData();
  }, []);
  
  return (
    <TrafficContext.Provider value={{ trafficData, isSimulating, setIsSimulating }}>
      {children}
    </TrafficContext.Provider>
  );
};

export const useTraffic = () => useContext(TrafficContext);
```

### 2.6 HTTP Client

#### Axios
**Purpose**: API calls to FastAPI backend

```javascript
// services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default apiClient;
```

**API Endpoints:**
```javascript
export const trafficAPI = {
  getTrafficData: () => apiClient.get('/traffic/current'),
  startSimulation: (params) => apiClient.post('/simulation/start', params),
  stopSimulation: () => apiClient.post('/simulation/stop'),
  getAnalytics: () => apiClient.get('/analytics'),
  optimizeSignals: () => apiClient.post('/ai/optimize'),
};
```

---

## 3. Backend Technologies

### 3.1 Python (v3.11+)
**Purpose**: Primary backend programming language

**Why Python?**
- Extensive AI/ML libraries (PyTorch, NumPy, scikit-learn)
- Native integration with SUMO via TraCI
- Fast development with FastAPI
- Strong data processing capabilities
- Large community and ecosystem

**Key Python Libraries:**
```python
# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
firebase-admin==6.3.0
torch==2.1.0
numpy==1.26.0
pandas==2.1.0
traci==1.19.0
python-dotenv==1.0.0
```

### 3.2 FastAPI (v0.109+)
**Purpose**: Modern, high-performance web framework for building APIs

**Key Features:**
- **Automatic API Documentation**: Swagger UI and ReDoc
- **Type Hints**: Built-in request/response validation with Pydantic
- **Async Support**: Asynchronous request handling
- **Dependency Injection**: Clean, testable code
- **WebSocket Support**: Real-time communication
- **High Performance**: Comparable to Node.js and Go

**Project Structure:**
```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── traffic.py      # Traffic data endpoints
│   │   │   ├── simulation.py   # Simulation control
│   │   │   └── ai.py           # AI optimization endpoints
│   │   └── dependencies.py     # Shared dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── traffic.py
│   │   └── simulation.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # Pydantic schemas
│   │   ├── traffic.py
│   │   └── simulation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── firebase_service.py
│   │   ├── traffic_service.py
│   │   ├── simulation_service.py
│   │   └── ai_service.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── rl_agent.py         # Reinforcement learning agent
│   │   ├── trainer.py          # Model training
│   │   ├── environment.py      # RL environment
│   │   └── models/             # Trained models
│   ├── sumo/
│   │   ├── __init__.py
│   │   ├── sumo_controller.py  # SUMO integration
│   │   ├── traci_client.py     # TraCI API wrapper
│   │   └── network_files/      # SUMO network configurations
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
├── tests/
├── requirements.txt
├── Dockerfile
└── .env
```

**Main Application (main.py):**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, traffic, simulation, ai
from app.config import settings

app = FastAPI(
    title="AI Traffic Management System API",
    description="Backend API for intelligent traffic management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(traffic.router, prefix="/api/traffic", tags=["Traffic"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Optimization"])

@app.get("/")
async def root():
    return {"message": "AI Traffic Management System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Sample API Route (traffic.py):**
```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.traffic import TrafficDataResponse, TrafficQuery
from app.services.traffic_service import TrafficService
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/current", response_model=TrafficDataResponse)
async def get_current_traffic(
    current_user = Depends(get_current_user),
    traffic_service: TrafficService = Depends()
):
    """Get current traffic data from all intersections"""
    try:
        traffic_data = await traffic_service.get_current_traffic()
        return traffic_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict")
async def predict_traffic(
    query: TrafficQuery,
    current_user = Depends(get_current_user)
):
    """Predict future traffic patterns using AI model"""
    # Implementation
    pass
```

**Pydantic Schemas (schemas/traffic.py):**
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class IntersectionData(BaseModel):
    intersection_id: str
    vehicle_count: int
    avg_speed: float
    congestion_level: str
    timestamp: datetime

class TrafficDataResponse(BaseModel):
    intersections: List[IntersectionData]
    total_vehicles: int
    avg_congestion: float
    
class TrafficQuery(BaseModel):
    intersection_id: Optional[str] = None
    time_range: int = Field(default=60, ge=1, le=1440)  # minutes
```

### 3.3 Uvicorn (v0.27+)
**Purpose**: ASGI server for running FastAPI

**Configuration:**
```python
# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development only
        workers=4     # Production
    )
```

### 3.4 Authentication & Security

#### 3.4.1 Firebase Admin SDK
**Purpose**: Server-side Firebase authentication verification

```python
# services/firebase_service.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config import settings

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

db = firestore.client()

def verify_firebase_token(token: str):
    """Verify Firebase ID token"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")
```

#### 3.4.2 JWT & OAuth2
**Purpose**: Additional token-based authentication

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

---

## 4. AI/ML Engine

### 4.1 PyTorch (v2.1+)
**Purpose**: Deep learning framework for reinforcement learning

**Why PyTorch?**
- Dynamic computational graphs
- Pythonic and intuitive API
- Strong community and ecosystem
- Excellent for research and production
- Native support for GPU acceleration

**Key Modules Used:**
```python
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Categorical
```

### 4.2 Reinforcement Learning Agent

#### 4.2.1 Neural Network Architecture
```python
# ai/rl_agent.py
import torch.nn as nn

class TrafficSignalNetwork(nn.Module):
    """Neural network for traffic signal optimization"""
    
    def __init__(self, state_size, action_size, hidden_size=128):
        super(TrafficSignalNetwork, self).__init__()
        
        # State: [vehicle_counts, waiting_times, queue_lengths, current_phase]
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        
        # Actor (policy) head
        self.actor = nn.Linear(hidden_size, action_size)
        
        # Critic (value) head
        self.critic = nn.Linear(hidden_size, 1)
        
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, state):
        x = F.relu(self.fc1(state))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        
        # Policy distribution
        action_probs = F.softmax(self.actor(x), dim=-1)
        
        # State value
        state_value = self.critic(x)
        
        return action_probs, state_value
```

#### 4.2.2 RL Algorithm: Proximal Policy Optimization (PPO)
```python
# ai/trainer.py
class PPOAgent:
    """Proximal Policy Optimization agent for traffic control"""
    
    def __init__(self, state_size, action_size, lr=3e-4):
        self.policy = TrafficSignalNetwork(state_size, action_size)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        
        self.gamma = 0.99  # Discount factor
        self.epsilon = 0.2  # PPO clip parameter
        self.epochs = 10
        
    def select_action(self, state):
        """Select action using current policy"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        with torch.no_grad():
            action_probs, _ = self.policy(state_tensor)
        
        dist = Categorical(action_probs)
        action = dist.sample()
        
        return action.item(), dist.log_prob(action)
    
    def compute_advantages(self, rewards, values, dones):
        """Compute Generalized Advantage Estimation (GAE)"""
        advantages = []
        advantage = 0
        
        for i in reversed(range(len(rewards))):
            delta = rewards[i] + self.gamma * values[i + 1] * (1 - dones[i]) - values[i]
            advantage = delta + self.gamma * 0.95 * (1 - dones[i]) * advantage
            advantages.insert(0, advantage)
        
        return advantages
    
    def update(self, states, actions, old_log_probs, returns, advantages):
        """Update policy using PPO"""
        for _ in range(self.epochs):
            # Get current policy predictions
            action_probs, values = self.policy(torch.FloatTensor(states))
            dist = Categorical(action_probs)
            
            new_log_probs = dist.log_prob(torch.LongTensor(actions))
            entropy = dist.entropy().mean()
            
            # Calculate ratios
            ratios = torch.exp(new_log_probs - old_log_probs)
            
            # PPO clipped objective
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.epsilon, 1 + self.epsilon) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()
            
            # Value loss
            critic_loss = nn.MSELoss()(values.squeeze(), returns)
            
            # Total loss
            loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy
            
            # Optimize
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
    
    def save(self, path):
        """Save model"""
        torch.save(self.policy.state_dict(), path)
    
    def load(self, path):
        """Load model"""
        self.policy.load_state_dict(torch.load(path))
```

#### 4.2.3 Environment Wrapper
```python
# ai/environment.py
class TrafficEnvironment:
    """Custom environment for traffic signal optimization"""
    
    def __init__(self, sumo_controller):
        self.sumo = sumo_controller
        self.state_size = self._get_state_size()
        self.action_size = 4  # 4 possible signal phases
        
    def _get_state_size(self):
        """Calculate state vector size"""
        # State includes: vehicle counts (4 directions) + waiting times (4) 
        # + queue lengths (4) + current phase (1)
        return 4 + 4 + 4 + 1  # = 13
    
    def get_state(self):
        """Get current state from SUMO"""
        # Vehicle counts per lane
        vehicle_counts = self.sumo.get_vehicle_counts()
        
        # Waiting times per lane
        waiting_times = self.sumo.get_waiting_times()
        
        # Queue lengths
        queue_lengths = self.sumo.get_queue_lengths()
        
        # Current signal phase
        current_phase = self.sumo.get_current_phase()
        
        state = vehicle_counts + waiting_times + queue_lengths + [current_phase]
        return np.array(state, dtype=np.float32)
    
    def step(self, action):
        """Execute action and return next state, reward, done"""
        # Set traffic signal phase
        self.sumo.set_signal_phase(action)
        
        # Run simulation step
        self.sumo.simulation_step()
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Get next state
        next_state = self.get_state()
        
        # Check if episode is done
        done = self.sumo.is_simulation_done()
        
        return next_state, reward, done
    
    def _calculate_reward(self):
        """Calculate reward based on traffic metrics"""
        # Negative reward for waiting time (minimize)
        total_waiting_time = sum(self.sumo.get_waiting_times())
        
        # Negative reward for queue length
        total_queue_length = sum(self.sumo.get_queue_lengths())
        
        # Reward for throughput (vehicles that passed)
        throughput = self.sumo.get_throughput()
        
        # Combined reward
        reward = throughput - 0.1 * total_waiting_time - 0.05 * total_queue_length
        
        return reward
    
    def reset(self):
        """Reset environment"""
        self.sumo.reset_simulation()
        return self.get_state()
```

### 4.3 Training Pipeline
```python
# ai/train.py
def train_rl_agent(num_episodes=1000):
    """Training loop for RL agent"""
    
    # Initialize
    sumo_controller = SUMOController(config_file="network.sumocfg")
    env = TrafficEnvironment(sumo_controller)
    agent = PPOAgent(env.state_size, env.action_size)
    
    for episode in range(num_episodes):
        state = env.reset()
        episode_reward = 0
        
        states, actions, rewards, log_probs, values, dones = [], [], [], [], [], []
        
        while True:
            # Select action
            action, log_prob = agent.select_action(state)
            
            # Take action
            next_state, reward, done = env.step(action)
            
            # Store experience
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            log_probs.append(log_prob)
            
            episode_reward += reward
            state = next_state
            
            if done:
                break
        
        # Update agent
        returns = compute_returns(rewards, agent.gamma)
        advantages = compute_advantages(rewards, values, dones)
        agent.update(states, actions, log_probs, returns, advantages)
        
        # Log progress
        if episode % 10 == 0:
            print(f"Episode {episode}, Reward: {episode_reward:.2f}")
            agent.save(f"models/agent_episode_{episode}.pth")
```

### 4.4 Additional ML Libraries

#### 4.4.1 NumPy
```python
import numpy as np

# Used for:
# - Array operations
# - State representation
# - Numerical computations
```

#### 4.4.2 Pandas (for data analysis)
```python
import pandas as pd

# Used for:
# - Traffic data analysis
# - Performance metrics calculation
# - Historical data processing
```

#### 4.4.3 Stable-Baselines3 (Optional)
**Purpose**: Pre-implemented RL algorithms

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

# Alternative to custom PPO implementation
env = make_vec_env(lambda: TrafficEnvironment(sumo_controller), n_envs=4)
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100000)
```

---

## 5. Database & Storage

### 5.1 Firebase Firestore
**Purpose**: NoSQL cloud database for real-time data storage

**Why Firestore?**
- Real-time synchronization
- Offline support
- Scalable and serverless
- Easy integration with Firebase Auth
- Automatic indexing
- Strong security rules

### 5.2 Data Model

#### 5.2.1 Collections Structure
```
firestore/
├── users/
│   └── {userId}/
│       ├── email: string
│       ├── displayName: string
│       ├── role: string
│       ├── createdAt: timestamp
│       └── lastLogin: timestamp
│
├── traffic_data/
│   └── {dataId}/
│       ├── timestamp: timestamp
│       ├── intersectionId: string
│       ├── vehicleCount: number
│       ├── avgSpeed: number
│       ├── congestionLevel: string
│       └── metadata: map
│
├── simulations/
│   └── {simulationId}/
│       ├── startTime: timestamp
│       ├── endTime: timestamp
│       ├── status: string
│       ├── parameters: map
│       ├── results: map
│       └── userId: string
│
├── ai_models/
│   └── {modelId}/
│       ├── version: string
│       ├── accuracy: number
│       ├── trainingDate: timestamp
│       ├── parameters: map
│       └── downloadUrl: string
│
├── intersections/
│   └── {intersectionId}/
│       ├── name: string
│       ├── location: geopoint
│       ├── lanes: array
│       ├── signalPhases: array
│       └── connectedIntersections: array
│
└── analytics/
    └── {analyticsId}/
        ├── date: timestamp
        ├── totalVehicles: number
        ├── avgWaitTime: number
        ├── peakHours: array
        └── metrics: map
```

#### 5.2.2 Firestore Operations (Python)
```python
# services/firebase_service.py
from firebase_admin import firestore
from datetime import datetime

class FirestoreService:
    def __init__(self):
        self.db = firestore.client()
    
    async def save_traffic_data(self, data: dict):
        """Save traffic data to Firestore"""
        doc_ref = self.db.collection('traffic_data').document()
        data['timestamp'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(data)
        return doc_ref.id
    
    async def get_traffic_history(self, intersection_id: str, limit: int = 100):
        """Retrieve traffic history"""
        docs = (
            self.db.collection('traffic_data')
            .where('intersectionId', '==', intersection_id)
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        
        return [doc.to_dict() for doc in docs]
    
    async def save_simulation_result(self, simulation_data: dict):
        """Save simulation results"""
        doc_ref = self.db.collection('simulations').document()
        simulation_data['endTime'] = datetime.now()
        simulation_data['status'] = 'completed'
        doc_ref.set(simulation_data)
        return doc_ref.id
    
    async def get_user_simulations(self, user_id: str):
        """Get user's simulation history"""
        docs = (
            self.db.collection('simulations')
            .where('userId', '==', user_id)
            .order_by('startTime', direction=firestore.Query.DESCENDING)
            .stream()
        )
        return [doc.to_dict() for doc in docs]
```

#### 5.2.3 Firestore Operations (Frontend - React)
```javascript
// services/firestore.js
import { collection, addDoc, query, where, getDocs, orderBy, limit } from 'firebase/firestore';
import { db } from './firebase';

export const saveTrafficData = async (data) => {
  try {
    const docRef = await addDoc(collection(db, 'traffic_data'), {
      ...data,
      timestamp: new Date(),
    });
    return docRef.id;
  } catch (error) {
    console.error('Error saving traffic data:', error);
    throw error;
  }
};

export const getTrafficHistory = async (intersectionId, limitCount = 100) => {
  const q = query(
    collection(db, 'traffic_data'),
    where('intersectionId', '==', intersectionId),
    orderBy('timestamp', 'desc'),
    limit(limitCount)
  );
  
  const querySnapshot = await getDocs(q);
  return querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
};
```

### 5.3 Firebase Storage
**Purpose**: Store large files (trained models, simulation files)

```python
# Upload trained model
from firebase_admin import storage

bucket = storage.bucket()
blob = bucket.blob('models/traffic_agent_v1.pth')
blob.upload_from_filename('path/to/model.pth')

# Get download URL
download_url = blob.generate_signed_url(expiration=datetime.timedelta(days=7))
```

### 5.4 Real-time Data Sync

#### Frontend Real-time Listener
```javascript
import { onSnapshot, collection, query, where } from 'firebase/firestore';

useEffect(() => {
  const q = query(
    collection(db, 'traffic_data'),
    where('intersectionId', '==', selectedIntersection)
  );
  
  const unsubscribe = onSnapshot(q, (snapshot) => {
    const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    setTrafficData(data);
  });
  
  return () => unsubscribe();
}, [selectedIntersection]);
```

---

## 6. Traffic Simulation

### 6.1 SUMO (Simulation of Urban MObility) v1.19+
**Purpose**: Microscopic traffic simulation

**Why SUMO?**
- Open-source and free
- Highly detailed traffic modeling
- Python API (TraCI) for control
- Supports large-scale networks
- Realistic vehicle behavior
- Multi-modal traffic support

**Installation:**
```bash
# Ubuntu/Debian
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc

# macOS
brew install sumo

# Verify installation
sumo --version
```

### 6.2 SUMO Network Files

#### 6.2.1 Network Definition (.net.xml)
```xml
<!-- network.net.xml -->
<net version="1.16" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <location netOffset="0.00,0.00" convBoundary="0.00,0.00,1000.00,1000.00"/>
    
    <edge id="E0" from="J0" to="J1" priority="1">
        <lane id="E0_0" index="0" speed="13.89" length="500.00" shape="0.00,0.00 500.00,0.00"/>
        <lane id="E0_1" index="1" speed="13.89" length="500.00" shape="0.00,3.20 500.00,3.20"/>
    </edge>
    
    <junction id="J1" type="traffic_light" x="500.00" y="0.00" incLanes="E0_0 E0_1" intLanes=":J1_0 :J1_1">
        <request index="0" response="00" foes="00" cont="0"/>
        <request index="1" response="00" foes="00" cont="0"/>
    </junction>
    
    <tlLogic id="J1" type="static" programID="0" offset="0">
        <phase duration="30" state="GG"/>
        <phase duration="5" state="yy"/>
        <phase duration="30" state="rr"/>
        <phase duration="5" state="yy"/>
    </tlLogic>
</net>
```

#### 6.2.2 Route Definition (.rou.xml)
```xml
<!-- routes.rou.xml -->
<routes>
    <!-- Vehicle types -->
    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5" maxSpeed="50"/>
    <vType id="truck" accel="1.3" decel="4.0" sigma="0.5" length="12" maxSpeed="40"/>
    
    <!-- Routes -->
    <route id="route0" edges="E0 E1 E2"/>
    <route id="route1" edges="E3 E4 E5"/>
    
    <!-- Vehicle flows -->
    <flow id="flow_north" type="car" route="route0" begin="0" end="3600" vehsPerHour="600"/>
    <flow id="flow_south" type="car" route="route1" begin="0" end="3600" vehsPerHour="800"/>
    <flow id="flow_truck" type="truck" route="route0" begin="0" end="3600" probability="0.1"/>
</routes>
```

#### 6.2.3 Configuration File (.sumocfg)
```xml
<!-- simulation.sumocfg -->
<configuration>
    <input>
        <net-file value="network.net.xml"/>
        <route-files value="routes.rou.xml"/>
    </input>
    
    <time>
        <begin value="0"/>
        <end value="3600"/>
        <step-length value="1.0"/>
    </time>
    
    <processing>
        <time-to-teleport value="-1"/>
    </processing>
    
    <report>
        <verbose value="true"/>
        <no-step-log value="true"/>
    </report>
</configuration>
```

### 6.3 TraCI (Traffic Control Interface)

#### 6.3.1 SUMO Controller (Python)
```python
# sumo/sumo_controller.py
import traci
import sumolib
import os

class SUMOController:
    """Controller for SUMO simulation with TraCI"""
    
    def __init__(self, config_file, gui=False):
        self.config_file = config_file
        self.gui = gui
        self.simulation_running = False
        
        # SUMO binary
        if gui:
            self.sumo_binary = sumolib.checkBinary('sumo-gui')
        else:
            self.sumo_binary = sumolib.checkBinary('sumo')
    
    def start_simulation(self):
        """Start SUMO simulation"""
        sumo_cmd = [self.sumo_binary, "-c", self.config_file]
        traci.start(sumo_cmd)
        self.simulation_running = True
        print("SUMO simulation started")
    
    def simulation_step(self, num_steps=1):
        """Advance simulation by specified steps"""
        for _ in range(num_steps):
            traci.simulationStep()
    
    def get_vehicle_counts(self):
        """Get vehicle count for each lane"""
        traffic_lights = traci.trafficlight.getIDList()
        
        counts = {}
        for tl_id in traffic_lights:
            controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)
            for lane in controlled_lanes:
                counts[lane] = traci.lane.getLastStepVehicleNumber(lane)
        
        return counts
    
    def get_waiting_times(self):
        """Get waiting times for vehicles"""
        vehicles = traci.vehicle.getIDList()
        waiting_times = []
        
        for vehicle_id in vehicles:
            waiting_time = traci.vehicle.getWaitingTime(vehicle_id)
            waiting_times.append(waiting_time)
        
        return waiting_times
    
    def get_queue_lengths(self):
        """Get queue lengths at intersections"""
        lanes = traci.lane.getIDList()
        queue_lengths = {}
        
        for lane_id in lanes:
            queue_length = traci.lane.getLastStepHaltingNumber(lane_id)
            queue_lengths[lane_id] = queue_length
        
        return queue_lengths
    
    def get_current_phase(self, tl_id):
        """Get current traffic light phase"""
        return traci.trafficlight.getPhase(tl_id)
    
    def set_signal_phase(self, tl_id, phase_index):
        """Set traffic light phase"""
        traci.trafficlight.setPhase(tl_id, phase_index)
    
    def get_throughput(self):
        """Get number of vehicles that completed their route"""
        return traci.simulation.getArrivedNumber()
    
    def is_simulation_done(self):
        """Check if simulation is finished"""
        return traci.simulation.getMinExpectedNumber() <= 0
    
    def reset_simulation(self):
        """Reset simulation to initial state"""
        if self.simulation_running:
            traci.close()
        self.start_simulation()
    
    def close(self):
        """Close SUMO simulation"""
        if self.simulation_running:
            traci.close()
            self.simulation_running = False
            print("SUMO simulation closed")
```

#### 6.3.2 Integration with FastAPI
```python
# api/routes/simulation.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.sumo.sumo_controller import SUMOController
from app.ai.rl_agent import PPOAgent
from app.schemas.simulation import SimulationConfig, SimulationStatus

router = APIRouter()

# Global simulation controller
sumo_controller = None
simulation_task = None

@router.post("/start")
async def start_simulation(
    config: SimulationConfig,
    background_tasks: BackgroundTasks
):
    """Start SUMO simulation"""
    global sumo_controller
    
    try:
        sumo_controller = SUMOController(
            config_file="sumo/network_files/simulation.sumocfg",
            gui=config.use_gui
        )
        
        # Start simulation in background
        background_tasks.add_task(run_simulation, sumo_controller, config)
        
        return {
            "status": "started",
            "message": "Simulation started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_simulation():
    """Stop running simulation"""
    global sumo_controller
    
    if sumo_controller:
        sumo_controller.close()
        return {"status": "stopped"}
    else:
        raise HTTPException(status_code=404, detail="No active simulation")

@router.get("/status")
async def get_simulation_status():
    """Get current simulation status"""
    if sumo_controller and sumo_controller.simulation_running:
        return {
            "status": "running",
            "current_time": traci.simulation.getTime(),
            "vehicle_count": len(traci.vehicle.getIDList())
        }
    return {"status": "stopped"}

async def run_simulation(controller, config):
    """Run simulation with AI agent"""
    controller.start_simulation()
    
    # Load AI agent if enabled
    if config.use_ai:
        agent = PPOAgent(state_size=13, action_size=4)
        agent.load("models/trained_agent.pth")
    
    while not controller.is_simulation_done():
        if config.use_ai:
            # Get state
            state = get_state_from_sumo(controller)
            
            # Get action from agent
            action, _ = agent.select_action(state)
            
            # Apply action
            controller.set_signal_phase("J1", action)
        
        # Step simulation
        controller.simulation_step()
    
    controller.close()
```

### 6.4 Network Generation Tools

**netedit**: GUI tool for creating SUMO networks
```bash
netedit network.net.xml
```

**netconvert**: Convert OpenStreetMap to SUMO network
```bash
# Download OSM data
wget "https://api.openstreetmap.org/api/0.6/map?bbox=..."

# Convert to SUMO
netconvert --osm-files map.osm -o network.net.xml
```

---

## 7. DevOps & Deployment

### 7.1 Docker
**Purpose**: Containerization for consistent deployment

#### 7.1.1 Backend Dockerfile
```dockerfile
# Dockerfile (Backend)
FROM python:3.11-slim

# Install SUMO
RUN apt-get update && apt-get install -y \
    sumo \
    sumo-tools \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV SUMO_HOME=/usr/share/sumo
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 7.1.2 Frontend Dockerfile
```dockerfile
# Dockerfile (Frontend)
# Build stage
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 7.1.3 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
      - SUMO_HOME=/usr/share/sumo
    volumes:
      - ./backend:/app
      - ./firebase-credentials.json:/app/firebase-credentials.json:ro
    networks:
      - traffic-network
    depends_on:
      - sumo-simulator
  
  sumo-simulator:
    build:
      context: ./sumo
      dockerfile: Dockerfile
    networks:
      - traffic-network
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
      - REACT_APP_FIREBASE_API_KEY=${FIREBASE_API_KEY}
    networks:
      - traffic-network
    depends_on:
      - backend

networks:
  traffic-network:
    driver: bridge
```

### 7.2 GitHub
**Purpose**: Version control and collaboration

#### 7.2.1 Repository Structure
```
traffic-management-system/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── sumo/
│   ├── network_files/
│   └── Dockerfile
├── docs/
├── docker-compose.yml
├── .gitignore
└── README.md
```

#### 7.2.2 .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
env/
.env

# Node
node_modules/
build/
.env.local

# IDE
.vscode/
.idea/

# Firebase
firebase-credentials.json

# SUMO
*.log
*.xml.gz

# Models
*.pth
*.pkl

# Docker
docker-compose.override.yml
```

### 7.3 GitHub Actions (CI/CD)

#### 7.3.1 Continuous Integration
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v
      
      - name: Run linter
        run: |
          cd backend
          flake8 app/ --max-line-length=100
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
      
      - name: Build
        run: |
          cd frontend
          npm run build
```

#### 7.3.2 Continuous Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push Backend
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: username/traffic-backend:latest
      
      - name: Build and push Frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: username/traffic-frontend:latest
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /app/traffic-management
            docker-compose pull
            docker-compose up -d
```

### 7.4 Environment Variables

#### 7.4.1 Backend (.env)
```env
# FastAPI
APP_NAME=Traffic Management System
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Firebase
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id

# SUMO
SUMO_HOME=/usr/share/sumo
SUMO_CONFIG_FILE=sumo/network_files/simulation.sumocfg

# AI Model
MODEL_PATH=app/ai/models/
USE_GPU=False

# Database
DATABASE_URL=firestore

# Logging
LOG_LEVEL=INFO
```

#### 7.4.2 Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_FIREBASE_API_KEY=your-api-key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=123456789
REACT_APP_FIREBASE_APP_ID=1:123456789:web:abcdef
```

### 7.5 Deployment Options

#### Option 1: Cloud Platforms
- **Frontend**: Firebase Hosting, Vercel, Netlify
- **Backend**: Google Cloud Run, AWS ECS, Heroku
- **Database**: Firebase Firestore (managed)

#### Option 2: VPS (Virtual Private Server)
- **Provider**: DigitalOcean, Linode, AWS EC2
- **Server**: Ubuntu 22.04 LTS
- **Web Server**: Nginx as reverse proxy
- **Process Manager**: PM2 or systemd

#### Option 3: Kubernetes (for large scale)
- Container orchestration
- Auto-scaling
- Load balancing
- High availability

---

## 8. Development Tools

### 8.1 Code Editors / IDEs
- **VS Code**: Recommended for full-stack development
- **PyCharm**: For Python/FastAPI backend
- **WebStorm**: For React frontend

### 8.2 Essential VS Code Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "dsznajder.es7-react-js-snippets",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens",
    "ms-vscode-remote.remote-containers"
  ]
}
```

### 8.3 Testing Frameworks

#### Backend Testing
```python
# tests/test_traffic_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_traffic_data():
    response = client.get("/api/traffic/current")
    assert response.status_code == 200
    assert "intersections" in response.json()
```

**Testing Tools:**
- pytest
- pytest-asyncio
- pytest-cov (coverage)

#### Frontend Testing
```javascript
// src/components/__tests__/Dashboard.test.js
import { render, screen } from '@testing-library/react';
import Dashboard from '../Dashboard';

test('renders dashboard title', () => {
  render(<Dashboard />);
  const titleElement = screen.getByText(/Traffic Dashboard/i);
  expect(titleElement).toBeInTheDocument();
});
```

**Testing Tools:**
- Jest
- React Testing Library
- Cypress (E2E testing)

### 8.4 API Documentation

#### Swagger UI (Auto-generated by FastAPI)
Access at: `http://localhost:8000/api/docs`

#### Postman Collection
Export API collection for team sharing

### 8.5 Code Quality Tools

#### Python
- **Black**: Code formatting
- **Flake8**: Linting
- **mypy**: Type checking
- **isort**: Import sorting

```bash
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100
```

#### JavaScript/React
- **ESLint**: Linting
- **Prettier**: Code formatting
- **Husky**: Git hooks

```json
// .eslintrc.json
{
  "extends": ["react-app", "react-app/jest"],
  "rules": {
    "no-console": "warn",
    "no-unused-vars": "warn"
  }
}
```

### 8.6 Monitoring & Logging

#### Application Monitoring
- **Sentry**: Error tracking
- **LogRocket**: Session replay
- **Google Analytics**: User analytics

#### Backend Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Application started")
```

---

## 9. Technology Justification

### 9.1 Why This Stack?

| Technology | Justification |
|------------|---------------|
| **React** | Industry-standard frontend framework, large ecosystem, excellent for SPAs |
| **Firebase** | Managed authentication & database, real-time sync, reduces backend complexity |
| **Python** | Best language for AI/ML, easy integration with SUMO, readable and maintainable |
| **FastAPI** | Modern, fast, auto-documentation, async support, type safety with Pydantic |
| **PyTorch** | Flexible for RL research, dynamic graphs, strong community, production-ready |
| **Firestore** | Serverless, real-time, scalable, tight Firebase integration |
| **SUMO** | Industry-standard traffic simulator, free, Python API, realistic modeling |
| **Docker** | Consistent environments, easy deployment, microservices-ready |

### 9.2 Alternatives Considered

| Our Choice | Alternatives | Why We Chose Ours |
|------------|--------------|-------------------|
| React | Vue, Angular, Svelte | Largest ecosystem, most job-relevant |
| FastAPI | Flask, Django | Better performance, auto-docs, modern async |
| PyTorch | TensorFlow, JAX | More intuitive for research, flexible |
| Firestore | MongoDB, PostgreSQL | Managed service, real-time, easier scaling |
| SUMO | VISSIM, Aimsun | Free, open-source, Python integration |
| Docker | Podman, manual deployment | Industry standard, excellent tooling |

---

## 10. System Integration

### 10.1 Data Flow

```
User (React) 
    ↓ HTTP Request
FastAPI Backend
    ↓ Query
Firebase Firestore ← Store Results
    ↑ Data
FastAPI Backend
    ↓ Control
SUMO Simulation (TraCI)
    ↓ State
RL Agent (PyTorch)
    ↓ Action
SUMO Simulation
    ↓ Results
FastAPI Backend
    ↓ Update
Firebase Firestore
    ↓ Real-time Sync
User (React)
```

### 10.2 API Integration Points

**Frontend ↔ Backend:**
- REST API (HTTP/JSON)
- WebSocket (real-time updates)

**Backend ↔ SUMO:**
- TraCI Python API

**Backend ↔ AI Model:**
- Direct function calls
- Model loading/inference

**Backend ↔ Firebase:**
- Firebase Admin SDK
- Firestore queries

**Frontend ↔ Firebase:**
- Firebase SDK
- Real-time listeners

---

## 11. Performance Optimization

### 11.1 Frontend Optimization
- Code splitting with React.lazy()
- Image optimization
- Caching with service workers
- Debouncing API calls
- Memoization (React.memo, useMemo)

### 11.2 Backend Optimization
- Async/await for I/O operations
- Connection pooling
- Caching frequent queries
- Background tasks for long operations
- Database indexing

### 11.3 AI Model Optimization
- Model quantization
- Batch inference
- GPU acceleration (if available)
- Model pruning
- Caching predictions

### 11.4 Database Optimization
- Proper indexing
- Query optimization
- Data denormalization where appropriate
- Pagination for large datasets
- Connection caching

---

## 12. Security Considerations

### 12.1 Authentication & Authorization
- Firebase Authentication
- JWT tokens
- Role-based access control (RBAC)
- API key authentication

### 12.2 Data Security
- HTTPS/TLS for all communications
- Environment variables for secrets
- Firebase security rules
- Input validation (Pydantic)
- SQL injection prevention (not applicable with Firestore)
- XSS prevention

### 12.3 API Security
- CORS configuration
- Rate limiting
- Request validation
- Error handling (no sensitive data in errors)

---

## 13. Scalability

### 13.1 Horizontal Scaling
- Stateless backend (easy to replicate)
- Load balancing with Docker Swarm/Kubernetes
- Firestore auto-scaling

### 13.2 Vertical Scaling
- Increase server resources
- GPU for AI model inference
- Database read replicas

---

## 14. Development Workflow

### 14.1 Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start

# SUMO (if testing locally)
sumo-gui -c sumo/network_files/simulation.sumocfg
```

### 14.2 Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### 14.3 Docker Development
```bash
# Build and run all services
docker-compose up --build

# Run specific service
docker-compose up backend

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

---

## 15. Conclusion

This technology stack provides:
- **Modern**: Latest versions of proven technologies
- **Scalable**: Cloud-ready, containerized architecture
- **Maintainable**: Clean separation of concerns
- **Performant**: Async operations, efficient frameworks
- **Developer-Friendly**: Excellent tooling and documentation
- **Production-Ready**: Battle-tested technologies

The combination of React, Firebase, Python, FastAPI, PyTorch, SUMO, and Docker creates a robust, scalable, and maintainable system for AI-powered traffic management.

---

## Appendices

### Appendix A: Quick Reference Commands

```bash
# Docker
docker-compose up -d
docker-compose down
docker-compose logs -f [service]

# Backend
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
black app/
flake8 app/

# Frontend
npm start
npm test
npm run build

# SUMO
sumo-gui -c simulation.sumocfg
sumo -c simulation.sumocfg --no-step-log

# Git
git add .
git commit -m "message"
git push origin main
```

### Appendix B: Useful Links

- React: https://react.dev
- FastAPI: https://fastapi.tiangolo.com
- PyTorch: https://pytorch.org
- Firebase: https://firebase.google.com/docs
- SUMO: https://sumo.dlr.de/docs/
- Docker: https://docs.docker.com

### Appendix C: Version Compatibility Matrix

| Component | Minimum Version | Recommended Version |
|-----------|----------------|---------------------|
| Python | 3.10 | 3.11+ |
| Node.js | 16 | 18 LTS |
| React | 17 | 18.2+ |
| FastAPI | 0.100 | 0.109+ |
| PyTorch | 2.0 | 2.1+ |
| SUMO | 1.15 | 1.19+ |
| Docker | 20.10 | 24+ |
