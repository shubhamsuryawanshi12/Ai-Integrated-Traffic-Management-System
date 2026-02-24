"""
Federated Averaging module for PCU-MARL++.

Implements FedAvg for aggregating actor parameters across agents.
"""

from typing import List, Dict, Optional
import torch
import copy
from collections import OrderedDict


class FedAvg:
    """
    Federated Averaging for multi-agent parameter synchronization.
    
    Averages actor parameters across all junction agents.
    Critic is centralized, so no aggregation needed.
    """
    
    def __init__(
        self,
        n_agents: int = 12,
    ):
        """
        Initialize FedAvg.
        
        Args:
            n_agents: Number of agents
        """
        self.n_agents = n_agents
        self.global_model_state: Optional[OrderedDict] = None
        
        # Aggregation history
        self.aggregation_history: List[Dict] = []
    
    def aggregate(
        self,
        agents: List,
    ) -> OrderedDict:
        """
        Aggregate actor parameters from all agents.
        
        Args:
            agents: List of MAPPOAgent objects
            
        Returns:
            Averaged state dict
        """
        if not agents:
            return {}
        
        # Get all actor state dicts
        state_dicts = []
        for agent in agents:
            if hasattr(agent, 'get_actor_params'):
                state_dicts.append(agent.get_actor_params())
        
        if not state_dicts:
            return {}
        
        # Average parameters
        averaged = self._average_state_dicts(state_dicts)
        
        # Store global model
        self.global_model_state = averaged
        
        # Record history
        self.aggregation_history.append({
            'n_agents': len(agents),
            'timestamp': len(self.aggregation_history),
        })
        
        return averaged
    
    def _average_state_dicts(
        self,
        state_dicts: List[OrderedDict],
    ) -> OrderedDict:
        """
        Average multiple state dictionaries.
        
        Args:
            state_dicts: List of state dicts
            
        Returns:
            Averaged state dict
        """
        if len(state_dicts) == 1:
            return copy.deepcopy(state_dicts[0])
        
        # Get keys from first dict
        keys = state_dicts[0].keys()
        
        # Initialize averaged dict
        averaged = OrderedDict()
        
        for key in keys:
            # Sum all tensors
            summed = None
            for sd in state_dicts:
                if key in sd:
                    if summed is None:
                        summed = sd[key].float()
                    else:
                        summed = summed + sd[key].float()
            
            # Average
            if summed is not None:
                averaged[key] = summed / len(state_dicts)
            else:
                averaged[key] = state_dicts[0][key]
        
        return averaged
    
    def distribute(
        self,
        agents: List,
    ) -> None:
        """
        Distribute global model to all agents.
        
        Args:
            agents: List of MAPPOAgent objects
        """
        if self.global_model_state is None:
            return
        
        for agent in agents:
            if hasattr(agent, 'load_actor_params'):
                agent.load_actor_params(copy.deepcopy(self.global_model_state))
    
    def get_global_model(self) -> Optional[OrderedDict]:
        """Get the global model state."""
        return self.global_model_state
    
    def set_global_model(self, state_dict: OrderedDict):
        """Set the global model state."""
        self.global_model_state = copy.deepcopy(state_dict)
    
    def get_history(self) -> List[Dict]:
        """Get aggregation history."""
        return self.aggregation_history
    
    def reset(self):
        """Reset FedAvg state."""
        self.global_model_state = None
        self.aggregation_history = []


class FedAvgOptimizer:
    """
    Optimizer for federated learning with momentum.
    """
    
    def __init__(
        self,
        n_agents: int = 12,
        momentum: float = 0.9,
    ):
        """
        Initialize FedAvg optimizer.
        
        Args:
            n_agents: Number of agents
            momentum: Momentum factor
        """
        self.n_agents = n_agents
        self.momentum = momentum
        
        # Local updates
        self.local_updates: List[OrderedDict] = []
        
        # Momentum buffer
        self.velocity: Optional[OrderedDict] = None
    
    def compute_local_update(
        self,
        old_state: OrderedDict,
        new_state: OrderedDict,
    ) -> OrderedDict:
        """
        Compute local update (difference between old and new).
        
        Args:
            old_state: Previous state dict
            new_state: New state dict
            
        Returns:
            Update dict (new - old)
        """
        update = OrderedDict()
        
        for key in old_state.keys():
            if key in new_state:
                update[key] = new_state[key] - old_state[key]
        
        return update
    
    def aggregate_updates(
        self,
        updates: List[OrderedDict],
    ) -> OrderedDict:
        """
        Aggregate local updates.
        
        Args:
            updates: List of update dicts
            
        Returns:
            Averaged update
        """
        if not updates:
            return {}
        
        return self._average_state_dicts(updates)
    
    def _average_state_dicts(
        self,
        state_dicts: List[OrderedDict],
    ) -> OrderedDict:
        """Average state dicts."""
        if len(state_dicts) == 1:
            return copy.deepcopy(state_dicts[0])
        
        keys = state_dicts[0].keys()
        averaged = OrderedDict()
        
        for key in keys:
            summed = None
            for sd in state_dicts:
                if key in sd:
                    if summed is None:
                        summed = sd[key].float()
                    else:
                        summed = summed + sd[key].float()
            
            if summed is not None:
                averaged[key] = summed / len(state_dicts)
        
        return averaged
    
    def apply_momentum(
        self,
        aggregated_update: OrderedDict,
    ) -> OrderedDict:
        """
        Apply momentum to aggregated update.
        
        Args:
            aggregated_update: Averaged update
            
        Returns:
            Update with momentum
        """
        if self.velocity is None:
            self.velocity = copy.deepcopy(aggregated_update)
            return aggregated_update
        
        # Apply momentum
        for key in aggregated_update.keys():
            if key in self.velocity:
                self.velocity[key] = (
                    self.momentum * self.velocity[key] + 
                    aggregated_update[key]
                )
            else:
                self.velocity[key] = aggregated_update[key]
        
        return self.velocity
    
    def reset(self):
        """Reset optimizer state."""
        self.local_updates = []
        self.velocity = None


def federated_averaging(
    agent_params_list: List[Dict],
) -> Dict:
    """
    Simple federated averaging function.
    
    Args:
        agent_params_list: List of agent parameter dicts
        
    Returns:
        Averaged parameters
    """
    if not agent_params_list:
        return {}
    
    if len(agent_params_list) == 1:
        return copy.deepcopy(agent_params_list[0])
    
    avg = OrderedDict()
    keys = agent_params_list[0].keys()
    
    for key in keys:
        tensors = [p[key] for p in agent_params_list if key in p]
        if tensors:
            avg[key] = torch.stack(tensors).mean(dim=0)
    
    return avg
