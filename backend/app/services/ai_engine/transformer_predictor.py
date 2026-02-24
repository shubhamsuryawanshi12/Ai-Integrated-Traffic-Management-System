"""
Transformer-Based Traffic Flow Predictor

Implements a Transformer encoder for spatio-temporal traffic prediction.
Uses multi-head attention to capture long-range dependencies in traffic flow.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import math

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for transformer."""
    
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # Create positional encoding
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encoding to input."""
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TrafficTransformerEncoder(nn.Module):
    """Transformer Encoder for traffic flow prediction."""
    
    def __init__(
        self,
        input_dim: int = 12,        # Features per intersection
        d_model: int = 128,          # Model dimension
        nhead: int = 8,              # Number of attention heads
        num_layers: int = 4,         # Number of transformer layers
        dim_feedforward: int = 512,  # Feedforward dimension
        dropout: int = 0.1,
        num_intersections: int = 9  # Number of intersections
    ):
        super().__init__()
        
        self.d_model = d_model
        self.num_intersections = num_intersections
        
        # Input embedding - project input features to model dimension
        self.input_projection = nn.Linear(input_dim, d_model)
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output heads for different prediction horizons
        self.output_heads = nn.ModuleDict({
            'short': nn.Linear(d_model, num_intersections),   # 5 min
            'medium': nn.Linear(d_model, num_intersections),  # 15 min
            'long': nn.Linear(d_model, num_intersections),    # 30 min
        })
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(
        self, 
        x: torch.Tensor, 
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Input tensor [batch, seq_len, num_intersections, input_dim]
               or [seq_len, num_intersections, input_dim]
            mask: Optional attention mask
            
        Returns:
            Tuple of (short_pred, medium_pred, long_pred)
            Each: [batch, num_intersections] or [num_intersections]
        """
        batch_mode = x.dim() == 4
        
        if not batch_mode:
            x = x.unsqueeze(0)  # Add batch dimension
        
        batch_size, seq_len, num_intersections, _ = x.shape
        
        # Reshape: combine sequence and intersection dimensions for transformer
        # [batch, seq_len, num_intersections, input_dim] -> [batch, seq_len*num_intersections, d_model]
        x = x.view(batch_size, seq_len * num_intersections, -1)
        
        # Project to model dimension
        x = self.input_projection(x)
        
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Apply transformer encoder
        x = self.transformer_encoder(x, mask=mask)
        
        # Take the last time step representation
        # [batch, seq_len*num_intersections, d_model] -> [batch, num_intersections, d_model]
        x = x[:, -num_intersections:, :]
        
        # Get predictions for different horizons
        short_pred = self.output_heads['short'](x).squeeze(-1)   # [batch, num_intersections]
        medium_pred = self.output_heads['medium'](x).squeeze(-1)
        long_pred = self.output_heads['long'](x).squeeze(-1)
        
        if not batch_mode:
            short_pred = short_pred.squeeze(0)
            medium_pred = medium_pred.squeeze(0)
            long_pred = long_pred.squeeze(0)
        
        return short_pred, medium_pred, long_pred


class TrafficFlowPredictor:
    """
    High-level traffic flow predictor using Transformer.
    Handles data preparation, training, and inference.
    """
    
    def __init__(
        self,
        input_dim: int = 12,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        num_intersections: int = 9,
        learning_rate: float = 1e-4,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.device = device
        self.num_intersections = num_intersections
        
        # Initialize model
        self.model = TrafficTransformerEncoder(
            input_dim=input_dim,
            d_model=d_model,
            nhead=nhead,
            num_layers=num_layers,
            num_intersections=num_intersections
        ).to(device)
        
        # Optimizer and loss
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'short_mae': [],
            'medium_mae': [],
            'long_mae': []
        }
    
    def prepare_sequence(
        self, 
        history: list, 
        seq_length: int = 12
    ) -> torch.Tensor:
        """
        Prepare input sequence from historical data.
        
        Args:
            history: List of historical observations
                     Each observation: dict with 'intersections': [{'id': int, 'vehicles': int, ...}, ...]
            seq_length: Length of input sequence
                    
        Returns:
            Tensor of shape [seq_length, num_intersections, input_dim]
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("numpy is required for sequence preparation")
        
        # Get last seq_length observations
        history = history[-seq_length:]
        
        # Build feature matrix
        features = []
        for timestep in history:
            intersection_features = []
            # Create feature vector for each intersection
            for i in range(self.num_intersections):
                # Find intersection data (use default if not found)
                int_data = None
                for i_data in timestep.get('intersections', []):
                    if i_data.get('id') == i:
                        int_data = i_data
                        break
                
                if int_data is None:
                    int_data = {'vehicles': 0, 'throughput': 0, 'queue': 0, 'wait_time': 0}
                
                # Feature vector: [vehicles, throughput, queue, wait_time, 
                #                hour_sin, hour_cos, day_sin, day_cos,
                #                is_peak, is_night, prev_1, prev_2]
                hour = timestep.get('hour', 12)
                day_of_week = timestep.get('day_of_week', 0)
                
                # Time features (cyclical encoding)
                hour_sin = math.sin(2 * math.pi * hour / 24)
                hour_cos = math.cos(2 * math.pi * hour / 24)
                day_sin = math.sin(2 * math.pi * day_of_week / 7)
                day_cos = math.cos(2 * math.pi * day_of_week / 7)
                
                # Peak indicators
                is_peak = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0
                is_night = 1 if (22 <= hour or hour <= 5) else 0
                
                # Previous values (simplified - would use actual history in production)
                prev_1 = int_data.get('vehicles', 0) / 100.0
                prev_2 = int_data.get('throughput', 0) / 100.0
                
                feat = [
                    int_data.get('vehicles', 0) / 100.0,      # Normalized vehicle count
                    int_data.get('throughput', 0) / 100.0,      # Normalized throughput
                    int_data.get('queue', 0) / 50.0,            # Normalized queue
                    int_data.get('wait_time', 0) / 60.0,        # Normalized wait time
                    hour_sin, hour_cos,
                    day_sin, day_cos,
                    is_peak, is_night,
                    prev_1, prev_2
                ]
                intersection_features.append(feat)
            
            features.append(intersection_features)
        
        # Convert to tensor
        tensor = torch.FloatTensor(features)
        return tensor.to(self.device)
    
    def predict(
        self, 
        history: list, 
        seq_length: int = 12
    ) -> dict:
        """
        Make predictions for multiple time horizons.
        
        Args:
            history: Historical traffic data
            seq_length: Input sequence length
            
        Returns:
            Dictionary with predictions for different horizons
        """
        self.model.eval()
        
        with torch.no_grad():
            x = self.prepare_sequence(history, seq_length)
            short_pred, medium_pred, long_pred = self.model(x)
            
            # Denormalize predictions
            predictions = {
                'short_5min': (short_pred.cpu().numpy() * 100).astype(int).tolist(),
                'medium_15min': (medium_pred.cpu().numpy() * 100).astype(int).tolist(),
                'long_30min': (long_pred.cpu().numpy() * 100).astype(int).tolist()
            }
        
        return predictions
    
    def train_step(
        self, 
        history_batch: list, 
        future_values: torch.Tensor
    ) -> float:
        """
        Single training step.
        
        Args:
            history_batch: List of history sequences
            future_values: Ground truth future values [batch, num_intersections, 3]
                          (3 = short, medium, long horizons)
        """
        self.model.train()
        
        # Prepare input
        batch_x = torch.stack([self.prepare_sequence(h) for h in history_batch])
        
        # Forward pass
        self.optimizer.zero_grad()
        short_pred, medium_pred, long_pred = self.model(batch_x)
        
        # Compute losses
        loss_short = self.criterion(short_pred, future_values[:, :, 0])
        loss_medium = self.criterion(medium_pred, future_values[:, :, 1])
        loss_long = self.criterion(long_pred, future_values[:, :, 2])
        
        # Total loss (weight short-term more heavily)
        loss = loss_short * 2.0 + loss_medium * 1.5 + loss_long * 1.0
        
        # Backward pass
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        return loss.item()
    
    def save(self, path: str):
        """Save model weights."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'history': self.history
        }, path)
    
    def load(self, path: str):
        """Load model weights."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint.get('history', self.history)


class TransformerForecaster:
    """
    Simplified wrapper for quick predictions.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.predictor = TrafficFlowPredictor()
        if model_path:
            try:
                self.predictor.load(model_path)
            except Exception as e:
                print(f"Could not load model from {model_path}: {e}")
    
    def forecast(
        self, 
        current_state: dict,
        horizon: str = 'short'
    ) -> dict:
        """
        Quick forecast method.
        
        Args:
            current_state: Current traffic state
            horizon: 'short' (5min), 'medium' (15min), or 'long' (30min)
            
        Returns:
            Predicted values per intersection
        """
        # Build simple history from current state
        import time
        current_time = time.localtime()
        hour = current_time.tm_hour
        
        # Create synthetic history for demonstration
        history = []
        for i in range(12):
            history.append({
                'hour': (hour - 12 + i) % 24,
                'day_of_week': current_time.tm_wday,
                'intersections': [
                    {
                        'id': j,
                        'vehicles': current_state.get('intersections', [{}])[j].get('vehicles', 10) + (i * 2),
                        'throughput': current_state.get('intersections', [{}])[j].get('throughput', 8),
                        'queue': current_state.get('intersections', [{}])[j].get('queue', 3),
                        'wait_time': current_state.get('intersections', [{}])[j].get('wait_time', 15)
                    }
                    for j in range(9)
                ]
            })
        
        predictions = self.predictor.predict(history)
        
        horizon_map = {
            'short': 'short_5min',
            'medium': 'medium_15min', 
            'long': 'long_30min'
        }
        
        return {
            'horizon': horizon,
            'predictions': predictions.get(horizon_map.get(horizon, 'short_5min'), []),
            'timestamp': time.time()
        }
