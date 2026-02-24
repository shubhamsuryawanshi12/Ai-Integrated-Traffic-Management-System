# PCU-MARL++

**PCU-Aware Multi-Agent Reinforcement Learning for Urban Traffic Control**

A comprehensive traffic signal control system using multi-agent RL with:
- **PCU-weighted reward functions** based on IRC:106-1990 standards
- **Graph attention communication (IDSS)** for inter-junction coordination
- **Climate-adaptive policy mixing (CATC)** for weather-aware control
- **LLM-based event reasoning (LAUER)** for civic event awareness
- **MAPPO training** with federated aggregation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Traffic Environment                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Junc 0  │  │ Junc 1  │  │ Junc 2  │  │   ...   │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────────┘       │
│       │            │            │                           │
│       ▼            ▼            ▼                           │
│  ┌─────────────────────────────────────────────────┐       │
│  │         Road Network (12 junctions)              │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Innovation Modules                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PCUReward│  │  IDSS    │  │  CATC    │  │  LAUER   │   │
│  │         │  │ (GAT)    │  │          │  │  (LLM)   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       MAPPO Agents                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Agent 0  │  │ Agent 1  │  │ Agent 2  │  │   ...   │   │
│  │ Actor    │  │ Actor    │  │ Actor    │  │          │   │
│  │ Critic   │  │ Critic   │  │ Critic   │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                           │                                  │
│                    ┌──────┴──────┐                           │
│                    │ FedAvg      │                           │
│                    │ Aggregation │                           │
│                    └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/pcu_marl.git
cd pcu_marl

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Quick Start

### Training

```bash
# Train for 100 episodes
python train.py --episodes 100 --junctions 12 --weather random

# Resume training from checkpoint
python train.py --episodes 500 --checkpoint checkpoints/latest.pt
```

### Evaluation

```bash
# Evaluate trained agents
python simulate.py --checkpoint checkpoints/best.pt --episodes 10
```

### Dashboard

```bash
# Start dashboard
python -m flask --app dashboard.app run --port 5000

# Or run with simulation feed
python simulate.py --checkpoint checkpoints/best.pt --dashboard
```

## Project Structure

```
pcu_marl/
├── env/                    # Environment module
│   ├── traffic_env.py     # Main Gym environment
│   ├── junction.py        # Intersection model
│   ├── vehicle.py         # PCU vehicle model
│   ├── weather.py         # Monsoon capacity model
│   └── road_network.py   # 12-junction graph
│
├── modules/               # Innovation modules
│   ├── pcu_reward.py      # PCU-aware reward
│   ├── idss.py           # Graph attention
│   ├── catc.py           # Climate mixing
│   └── lauer.py          # LLM events
│
├── agents/                # Agent implementations
│   ├── actor_critic.py    # Neural networks
│   ├── mappo_agent.py    # MAPPO agent
│   └── rollout_buffer.py # GAE buffer
│
├── training/              # Training pipeline
│   ├── trainer.py        # Main orchestrator
│   ├── federated.py      # FedAvg
│   └── logger.py         # TensorBoard logging
│
├── utils/                # Utilities
│   ├── config.py         # Hyperparameters
│   └── graph_utils.py   # Graph helpers
│
└── dashboard/            # Real-time dashboard
    ├── app.py            # Flask + Socket.IO
    ├── templates/        # HTML template
    └── static/           # CSS + JS
```

## Key Features

### 1. PCU-Weighted Queuing
Vehicles are weighted by PCU (Passenger Car Unit) based on IRC:106-1990:
- Motorcycle: 0.5 PCU
- Car/Auto: 1.0 PCU  
- Bus: 3.0 PCU
- Truck: 3.5 PCU

### 2. Weather Adaptation
Monsoon conditions reduce capacity:
- Clear weather: 100% capacity
- Moderate rain: 80% capacity
- Heavy rain: 60% capacity

### 3. Graph Attention Communication
Junctions within 800m communicate via learned attention, enabling coordinated green waves.

### 4. Event-Aware Control
LAUER processes civic events (festivals, rallies, construction) to predict demand spikes.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_env.py -v
```

## Configuration

See `pcu_marl/utils/config.py` for all hyperparameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| n_junctions | 12 | Number of intersections |
| n_episodes | 1000 | Training episodes |
| rollout_steps | 400 | Steps per episode |
| lr_actor | 3e-4 | Actor learning rate |
| lr_critic | 1e-3 | Critic learning rate |
| gamma | 0.99 | Discount factor |
| gae_lambda | 0.95 | GAE lambda |

## Dashboard Features

- **12-junction grid visualization** with phase indicators
- **Real-time metrics** (delay, throughput, overflow)
- **Module status panels** (IDSS, CATC, LAUER)
- **Reward curves** over time
- **Weather gauge** showing rain intensity

## License

MIT License

## Citation

If you use this code, please cite:

```bibtex
@article{pcu_marl2024,
  title={PCU-MARL++: PCU-Aware Multi-Agent Reinforcement Learning for Urban Traffic Control},
  author={},
  journal={},
  year={2024}
}
```
