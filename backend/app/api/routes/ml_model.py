"""
API routes for PCU-MARL++ ML Model.

Provides endpoints for:
- Getting model status
- Running inference
- Training (simple version)
- Getting environment state
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import numpy as np

# Import PCU-MARL++ components
try:
    from app.services.ai_engine.pcu_marl import (
        TrafficEnvironment,
        create_environment,
        CentralizedMAPPO,
        create_mappo,
        PCUReward,
        CATCModule,
        IDSSCoordinator,
        PHASE_NAMES,
        get_default_config,
    )
    PCU_MARL_AVAILABLE = True
except ImportError as e:
    PCU_MARL_AVAILABLE = False
    print(f"WARNING: PCU-MARL++ not available: {e}")

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])

# Global state
_model: Optional[CentralizedMAPPO] = None
_environment: Optional[TrafficEnvironment] = None
_is_running = False


class ActionRequest(BaseModel):
    """Request model for actions."""
    actions: Dict[int, int]


class ResetRequest(BaseModel):
    """Request model for environment reset."""
    seed: Optional[int] = None
    n_junctions: Optional[int] = 12


class ModelStatusResponse(BaseModel):
    """Response model for model status."""
    available: bool
    is_running: bool
    n_junctions: Optional[int] = None
    obs_dim: Optional[int] = None
    action_dim: Optional[int] = None
    weather: Optional[Dict[str, Any]] = None
    phases: Optional[Dict[str, str]] = None
    queues: Optional[Dict[str, Dict[str, float]]] = None
    throughput: Optional[List[float]] = None
    catc_stats: Optional[Dict[str, Any]] = None
    idss_stats: Optional[Dict[str, Any]] = None


class InferenceRequest(BaseModel):
    """Request model for inference."""
    observations: Dict[str, List[float]]


class InferenceResponse(BaseModel):
    """Response model for inference."""
    actions: Dict[str, int]
    phases: Dict[str, str]
    rewards: Dict[str, float]


@router.get("/status", response_model=ModelStatusResponse)
async def get_status():
    """
    Get the current status of the ML model.
    
    Returns:
        ModelStatusResponse with current state
    """
    global _model, _environment, _is_running
    
    if not PCU_MARL_AVAILABLE:
        return ModelStatusResponse(
            available=False,
            is_running=False,
        )
    
    if _environment is None:
        return ModelStatusResponse(
            available=True,
            is_running=False,
        )
    
    state = _environment.get_state()
    
    return ModelStatusResponse(
        available=True,
        is_running=_is_running,
        n_junctions=_environment.n_junctions,
        obs_dim=_environment.obs_dim,
        action_dim=4,
        weather={
            "rain_intensity": state.get("rain_intensity", 0.0),
            "capacity_factor": state.get("capacity_factor", 1.0),
        },
        phases=state.get("phases", {}),
        queues=state.get("queues", {}),
        throughput=state.get("total_throughput", []),
        catc_stats=state.get("catc_stats", {}),
        idss_stats=state.get("idss_stats", {}),
    )


@router.post("/reset")
async def reset_environment(request: ResetRequest):
    """
    Reset the traffic environment.
    
    Args:
        request: ResetRequest with optional seed and n_junctions
        
    Returns:
        Current environment state
    """
    global _model, _environment, _is_running
    
    if not PCU_MARL_AVAILABLE:
        raise HTTPException(status_code=503, detail="PCU-MARL++ not available")
    
    try:
        n_junctions = request.n_junctions or 12
        seed = request.seed
        
        # Create environment
        _environment = create_environment(n_junctions=n_junctions, seed=seed)
        
        # Create model
        _model = create_mappo(n_agents=n_junctions)
        
        # Reset environment
        observations = _environment.reset(seed=seed)
        
        # Get initial state
        state = _environment.get_state()
        _is_running = True
        
        return {
            "status": "success",
            "message": f"Environment reset with {n_junctions} junctions",
            "state": state,
            "observations": {str(k): v.tolist() if isinstance(v, np.ndarray) else v 
                          for k, v in observations.items()},
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step")
async def step_environment(request: ActionRequest):
    """
    Execute one step in the environment.
    
    Args:
        request: ActionRequest with actions for each junction
        
    Returns:
        Environment state after step
    """
    global _model, _environment, _is_running
    
    if not PCU_MARL_AVAILABLE:
        raise HTTPException(status_code=503, detail="PCU-MARL++ not available")
    
    if _environment is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        # Convert actions to dict with int keys
        actions = {int(k): v for k, v in request.actions.items()}
        
        # Execute step
        observations, rewards, dones, info = _environment.step(actions)
        
        # Format response
        return {
            "status": "success",
            "step": info.get("step", 0),
            "phases": info.get("phases", {}),
            "queues": info.get("queues", {}),
            "rewards": {str(k): v for k, v in rewards.items()},
            "throughput": info.get("throughput", []),
            "rain_intensity": info.get("rain_intensity", 0.0),
            "capacity_factor": info.get("capacity_factor", 1.0),
            "catc_stats": info.get("catc_stats", {}),
            "idss_stats": info.get("idss_stats", {}),
            "done": all(dones.values()),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inference")
async def run_inference(request: InferenceRequest):
    """
    Run inference with the ML model.
    
    Args:
        request: InferenceRequest with observations
        
    Returns:
        Actions chosen by the model
    """
    global _model, _environment
    
    if not PCU_MARL_AVAILABLE:
        raise HTTPException(status_code=503, detail="PCU-MARL++ not available")
    
    if _model is None or _environment is None:
        raise HTTPException(status_code=400, detail="Model not initialized. Call /reset first.")
    
    try:
        # Convert observations to dict with int keys
        observations = {int(k): np.array(v) for k, v in request.observations.items()}
        
        # Get actions from model
        results = _model.select_actions(observations, deterministic=True)
        
        # Format response
        actions = {str(k): v[0] for k, v in results.items()}
        rewards = {str(k): 0.0 for k in results.keys()}  # Placeholder
        
        phases = {}
        for jid, action in actions.items():
            phases[jid] = PHASE_NAMES.get(action, "UNKNOWN")
        
        return InferenceResponse(
            actions=actions,
            phases=phases,
            rewards=rewards,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/env_state")
async def get_env_state():
    """
    Get current environment state.
    
    Returns:
        Full environment state
    """
    global _environment
    
    if not PCU_MARL_AVAILABLE:
        raise HTTPException(status_code=503, detail="PCU-MARL++ not available")
    
    if _environment is None:
        raise HTTPException(status_code=400, detail="Environment not initialized")
    
    try:
        state = _environment.get_state()
        return {
            "status": "success",
            "state": state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_model():
    """
    Stop the ML model execution.
    
    Returns:
        Success message
    """
    global _is_running
    
    _is_running = False
    
    return {
        "status": "success",
        "message": "ML model stopped",
    }


@router.get("/config")
async def get_config():
    """
    Get the default PCU-MARL++ configuration.
    
    Returns:
        Configuration dictionary
    """
    if not PCU_MARL_AVAILABLE:
        raise HTTPException(status_code=503, detail="PCU-MARL++ not available")
    
    config = get_default_config()
    
    return {
        "status": "success",
        "config": config.to_dict(),
    }
