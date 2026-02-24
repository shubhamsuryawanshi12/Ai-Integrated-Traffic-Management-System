"""
Logger module for PCU-MARL++.

Provides TensorBoard and CSV logging for training metrics.
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, Optional, List
import numpy as np


class TrainingLogger:
    """
    Logger for training metrics.
    
    Supports both TensorBoard and CSV logging.
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        experiment_name: Optional[str] = None,
        use_tensorboard: bool = True,
    ):
        """
        Initialize logger.
        
        Args:
            log_dir: Base directory for logs
            experiment_name: Name for this experiment
            use_tensorboard: Whether to use TensorBoard
        """
        self.log_dir = log_dir
        
        # Create experiment name with timestamp
        if experiment_name is None:
            experiment_name = f"pcu_marl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.experiment_name = experiment_name
        self.run_dir = os.path.join(log_dir, experiment_name)
        
        # Create directories
        os.makedirs(self.run_dir, exist_ok=True)
        
        # CSV logging
        self.csv_file = os.path.join(self.run_dir, "metrics.csv")
        self.csv_writer = None
        self.csv_handle = None
        
        # TensorBoard
        self.use_tensorboard = use_tensorboard
        self.writer = None
        
        if use_tensorboard:
            try:
                from torch.utils.tensorboard import SummaryWriter
                self.writer = SummaryWriter(self.run_dir)
            except ImportError:
                print("TensorBoard not available, disabling")
                self.use_tensorboard = False
        
        # Metrics storage
        self.episode_metrics: List[Dict] = []
        self.step_metrics: List[Dict] = []
        
        # Current episode
        self.current_episode = 0
    
    def _init_csv(self):
        """Initialize CSV writer."""
        if self.csv_handle is None:
            self.csv_handle = open(self.csv_file, 'w', newline='')
            fieldnames = ['episode', 'step', 'metric', 'value']
            self.csv_writer = csv.DictWriter(self.csv_handle, fieldnames=fieldnames)
            self.csv_writer.writeheader()
    
    def log_scalar(self, tag: str, value: float, step: int):
        """
        Log a scalar value.
        
        Args:
            tag: Metric name
            value: Value
            step: Step number
        """
        # TensorBoard
        if self.use_tensorboard and self.writer:
            self.writer.add_scalar(tag, value, step)
        
        # CSV
        self._init_csv()
        self.csv_writer.writerow({
            'episode': self.current_episode,
            'step': step,
            'metric': tag,
            'value': value,
        })
    
    def log_episode_metrics(
        self,
        episode: int,
        metrics: Dict[str, float],
    ):
        """
        Log metrics for an episode.
        
        Args:
            episode: Episode number
            metrics: Dictionary of metrics
        """
        self.current_episode = episode
        self.episode_metrics.append({
            'episode': episode,
            **metrics,
        })
        
        for key, value in metrics.items():
            self.log_scalar(f"episode/{key}", value, episode)
    
    def log_step_metrics(
        self,
        step: int,
        metrics: Dict[str, float],
    ):
        """
        Log metrics for a step.
        
        Args:
            step: Step number
            metrics: Dictionary of metrics
        """
        self.step_metrics.append({
            'step': step,
            **metrics,
        })
        
        for key, value in metrics.items():
            self.log_scalar(f"step/{key}", value, step)
    
    def log_loss(
        self,
        episode: int,
        loss_dict: Dict[str, float],
    ):
        """
        Log loss values.
        
        Args:
            episode: Episode number
            loss_dict: Dictionary of loss values
        """
        for key, value in loss_dict.items():
            self.log_scalar(f"loss/{key}", value, episode)
    
    def log_module_stats(
        self,
        episode: int,
        module_name: str,
        stats: Dict[str, float],
    ):
        """
        Log module-specific statistics.
        
        Args:
            episode: Episode number
            module_name: Name of module
            stats: Statistics dictionary
        """
        for key, value in stats.items():
            self.log_scalar(f"{module_name}/{key}", value, episode)
    
    def save_config(self, config: Dict):
        """
        Save training configuration.
        
        Args:
            config: Configuration dictionary
        """
        config_file = os.path.join(self.run_dir, "config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def close(self):
        """Close logger and flush files."""
        if self.use_tensorboard and self.writer:
            self.writer.close()
        
        if self.csv_handle:
            self.csv_handle.close()
    
    def get_log_dir(self) -> str:
        """Get log directory path."""
        return self.run_dir
    
    def get_latest_metrics(self) -> Dict:
        """Get latest episode metrics."""
        if self.episode_metrics:
            return self.episode_metrics[-1]
        return {}
    
    def get_metric_history(self, metric_name: str) -> List[float]:
        """Get history of a specific metric."""
        values = []
        for m in self.episode_metrics:
            if metric_name in m:
                values.append(m[metric_name])
        return values


class MetricsTracker:
    """
    Tracks metrics during training for smoothing.
    """
    
    def __init__(
        self,
        window_size: int = 100,
    ):
        """
        Initialize metrics tracker.
        
        Args:
            window_size: Window for moving average
        """
        self.window_size = window_size
        self.metrics: Dict[str, List[float]] = {}
    
    def add(self, metric_name: str, value: float):
        """Add a metric value."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(value)
        
        # Keep only window
        if len(self.metrics[metric_name]) > self.window_size:
            self.metrics[metric_name] = self.metrics[metric_name][-self.window_size:]
    
    def get_mean(self, metric_name: str) -> float:
        """Get mean of metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return 0.0
        return np.mean(self.metrics[metric_name])
    
    def get_std(self, metric_name: str) -> float:
        """Get std of metric."""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < 2:
            return 0.0
        return np.std(self.metrics[metric_name])
    
    def get_latest(self, metric_name: str) -> float:
        """Get latest value."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return 0.0
        return self.metrics[metric_name][-1]
    
    def get_all_means(self) -> Dict[str, float]:
        """Get means of all metrics."""
        return {name: self.get_mean(name) for name in self.metrics.keys()}
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = {}


def create_logger(
    log_dir: str = "logs",
    experiment_name: Optional[str] = None,
    use_tensorboard: bool = True,
) -> TrainingLogger:
    """
    Factory function to create logger.
    
    Args:
        log_dir: Log directory
        experiment_name: Experiment name
        use_tensorboard: Use TensorBoard
        
    Returns:
        TrainingLogger instance
    """
    return TrainingLogger(
        log_dir=log_dir,
        experiment_name=experiment_name,
        use_tensorboard=use_tensorboard,
    )
