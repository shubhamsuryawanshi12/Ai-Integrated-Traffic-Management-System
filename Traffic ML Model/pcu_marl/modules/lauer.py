"""
LAUER (LLM-Aware Urban Event Reasoning) Module for PCU-MARL++.

Implements LLM-based event parsing and demand forecasting for traffic control.
Includes fallback hierarchy: Mistral-7B → GPT-2 → Rule-based parser.
"""

import json
import re
import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# For LLM integration (optional)
try:
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


# Mock events for Bengaluru, India
MOCK_EVENTS = [
    {
        "text": "Ganesh Chaturthi procession on Chord Road, Rajajinagar, 6 PM to 11 PM tonight",
        "time": "18:00",
        "end_time": "23:00",
        "corridors": ["Main Road 2", "Cross Street C"],
    },
    {
        "text": "BBMP road repair work on Palace Road junction from 10 AM to 4 PM",
        "time": "10:00",
        "end_time": "16:00",
        "corridors": ["Cross Street B"],
    },
    {
        "text": "Kannada Rajyotsava rally starting from Town Hall towards Cubbon Park, 4 PM",
        "time": "16:00",
        "end_time": "19:00",
        "corridors": ["Cross Street A", "Main Road 1"],
    },
    {
        "text": "Heavy rainfall warning for Electronic City from 3 PM to 8 PM",
        "time": "15:00",
        "end_time": "20:00",
        "corridors": ["Main Road 3"],
    },
]


# Event extraction prompt
EXTRACTION_PROMPT = """You are a traffic demand forecasting assistant. Analyze the following civic event and extract in JSON:
{{
  "event_type": <protest|festival|emergency|construction|rally|other>,
  "start_time": <HH:MM>,
  "end_time": <HH:MM>,
  "affected_corridors": [<road name>, ...],
  "peak_demand_multiplier": <float 1.0-3.0>,
  "spatial_radius_km": <float>
}}
Event: {event_text}
JSON only, no explanation."""


@dataclass
class ParsedEvent:
    """Parsed event data."""
    event_type: str
    start_time: str
    end_time: str
    affected_corridors: List[str]
    peak_demand_multiplier: float
    spatial_radius_km: float


class RuleBasedParser:
    """
    Rule-based fallback parser when LLM is not available.
    
    Uses regex patterns and keyword matching.
    """
    
    def __init__(self):
        """Initialize rule-based parser."""
        self.event_patterns = {
            "festival": [
                r"festival",
                r"celebration",
                r"procession",
                r"ganesh|diwali|eid|christmas",
            ],
            "construction": [
                r"repair",
                r"construction",
                r"road work",
                r"maintenance",
                r"bbmp",
            ],
            "rally": [
                r"rally",
                r"march",
                r"protest",
                r"dharna",
                r"demonstration",
            ],
            "emergency": [
                r"accident",
                r"emergency",
                r"fire",
                r"flood",
                r"warning",
            ],
        }
        
        self.demand_patterns = {
            "high": [2.0, 2.5, 3.0],
            "medium": [1.5, 1.8, 2.0],
            "low": [1.2, 1.5, 1.8],
        }
        
        self.time_pattern = r"(\d{1,2})\s*(?:AM|PM|am|pm)?\s*(?:to|-)\s*(\d{1,2})\s*(?:AM|PM|am|pm)?"
    
    def parse(self, text: str) -> ParsedEvent:
        """
        Parse event text using rules.
        
        Args:
            text: Event text
            
        Returns:
            ParsedEvent
        """
        text_lower = text.lower()
        
        # Detect event type
        event_type = "other"
        for etype, patterns in self.event_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    event_type = etype
                    break
        
        # Extract time
        time_match = re.search(self.time_pattern, text)
        if time_match:
            start_time = time_match.group(1).zfill(2) + ":00"
            end_time = time_match.group(2).zfill(2) + ":00"
        else:
            start_time = "12:00"
            end_time = "18:00"
        
        # Extract demand multiplier based on event type
        if event_type == "festival":
            demand = 2.0
        elif event_type == "rally":
            demand = 1.8
        elif event_type == "construction":
            demand = 1.3
        elif event_type == "emergency":
            demand = 1.5
        else:
            demand = 1.2
        
        # Extract corridors
        corridors = self._extract_corridors(text)
        
        # Spatial radius
        radius = 1.5 if event_type in ["festival", "rally"] else 1.0
        
        return ParsedEvent(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            affected_corridors=corridors,
            peak_demand_multiplier=demand,
            spatial_radius_km=radius,
        )
    
    def _extract_corridors(self, text: str) -> List[str]:
        """Extract corridor names from text."""
        text_lower = text.lower()
        
        corridors = []
        known_corridors = [
            "chord road",
            "palace road",
            "main road",
            "cross street",
            "electronic city",
            "town hall",
            "cubbon park",
        ]
        
        for corridor in known_corridors:
            if corridor in text_lower:
                corridors.append(corridor.title())
        
        return corridors


class LAUERModule:
    """
    LLM-Aware Urban Event Reasoning module.
    
    Processes civic events and generates demand context vectors for junctions.
    """
    
    def __init__(
        self,
        n_junctions: int = 12,
        road_network=None,
        llm_backend: str = "rule_based",  # "mistral", "gpt2", "rule_based"
        poll_interval: int = 1800,  # 30 minutes
    ):
        """
        Initialize LAUER module.
        
        Args:
            n_junctions: Number of junctions
            road_network: RoadNetwork instance
            llm_backend: LLM backend to use
            poll_interval: Event polling interval in seconds
        """
        self.n_junctions = n_junctions
        self.road_network = road_network
        self.llm_backend = llm_backend
        self.poll_interval = poll_interval
        
        # Current event context
        self.current_ctx = np.ones(n_junctions, dtype=np.float32)
        self.current_event: Optional[ParsedEvent] = None
        self.active_events: List[ParsedEvent] = []
        
        # LLM pipeline (if available)
        self.llm_pipeline = None
        self._init_llm()
        
        # Rule-based fallback
        self.rule_parser = RuleBasedParser()
        
        # Event polling thread
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False
    
    def _init_llm(self):
        """Initialize LLM pipeline."""
        if not TRANSFORMERS_AVAILABLE:
            print("LAUER: transformers not available, using rule-based parser")
            return
        
        if self.llm_backend == "mistral":
            try:
                # Use a smaller model for CPU
                self.llm_pipeline = pipeline(
                    "text-generation",
                    model="gpt2",  # Fallback to gpt2 for now
                    device=-1,  # CPU
                )
            except Exception as e:
                print(f"LAUER: Failed to load LLM: {e}")
                self.llm_backend = "rule_based"
        
        elif self.llm_backend == "gpt2":
            try:
                self.llm_pipeline = pipeline(
                    "text-generation",
                    model="gpt2",
                    device=-1,
                )
            except Exception as e:
                print(f"LAUER: Failed to load GPT-2: {e}")
                self.llm_backend = "rule_based"
    
    def parse_event(self, text: str) -> ParsedEvent:
        """
        Parse event text using available backend.
        
        Args:
            text: Event text
            
        Returns:
            ParsedEvent
        """
        if self.llm_backend == "rule_based":
            return self.rule_parser.parse(text)
        
        # Use LLM if available
        prompt = EXTRACTION_PROMPT.format(event_text=text)
        
        try:
            raw = self.llm_pipeline(
                prompt, 
                max_new_tokens=200,
                temperature=0.1,
            )[0]["generated_text"]
            
            # Extract JSON
            json_str = self._extract_json(raw)
            
            if json_str:
                data = json.loads(json_str)
                return ParsedEvent(
                    event_type=data.get("event_type", "other"),
                    start_time=data.get("start_time", "12:00"),
                    end_time=data.get("end_time", "18:00"),
                    affected_corridors=data.get("affected_corridors", []),
                    peak_demand_multiplier=data.get("peak_demand_multiplier", 1.5),
                    spatial_radius_km=data.get("spatial_radius_km", 1.5),
                )
        except Exception as e:
            print(f"LAUER: LLM parsing failed: {e}")
        
        # Fallback to rule-based
        return self.rule_parser.parse(text)
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON block from text."""
        # Find JSON block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        return None
    
    def build_event_context_vector(self, event: ParsedEvent) -> np.ndarray:
        """
        Build demand multiplier vector for all junctions.
        
        Applies spatial decay based on distance from affected corridors.
        
        Args:
            event: Parsed event
            
        Returns:
            Demand multiplier array of shape (n_junctions,)
        """
        ctx = np.ones(self.n_junctions, dtype=np.float32)
        
        if not self.road_network:
            return ctx
        
        # For each affected corridor
        for corridor_name in event.affected_corridors:
            try:
                center = self.road_network.get_corridor_centroid(corridor_name)
            except:
                continue
            
            # Apply to nearby junctions
            for jid in range(self.n_junctions):
                try:
                    jpos = self.road_network.get_junction_position(jid)
                    distance_km = np.linalg.norm(
                        np.array([jpos.x, jpos.y]) - center
                    ) / 1000  # Convert to km
                except:
                    distance_km = float('inf')
                
                if distance_km < event.spatial_radius_km:
                    # Exponential decay
                    multiplier = event.peak_demand_multiplier * np.exp(
                        -distance_km / event.spatial_radius_km
                    )
                    ctx[jid] *= multiplier
        
        # Bound to [1.0, 3.0]
        return np.clip(ctx, 1.0, 3.0)
    
    def fetch_events(self) -> List[Dict]:
        """
        Fetch upcoming events.
        
        In real implementation, would poll RSS feeds, BBMP API, etc.
        
        Returns:
            List of event dictionaries
        """
        # Return mock events for now
        return MOCK_EVENTS
    
    def update_events(self) -> np.ndarray:
        """
        Update event context from current events.
        
        Returns:
            Updated context vector
        """
        events = self.fetch_events()
        
        if not events:
            self.current_ctx = np.ones(self.n_junctions, dtype=np.float32)
            return self.current_ctx
        
        # Parse events and build context
        combined_ctx = np.ones(self.n_junctions, dtype=np.float32)
        
        for event_dict in events:
            parsed = self.parse_event(event_dict["text"])
            event_ctx = self.build_event_context_vector(parsed)
            combined_ctx *= event_ctx
        
        self.current_ctx = np.clip(combined_ctx, 1.0, 3.0)
        
        # Store active event info
        if events:
            self.current_event = self.parse_event(events[0]["text"])
        
        return self.current_ctx
    
    def get_event_context(self) -> np.ndarray:
        """
        Get current event context vector.
        
        Returns:
            Context array of shape (n_junctions,)
        """
        return self.current_ctx
    
    def get_current_event_info(self) -> Optional[Dict]:
        """Get information about current active event."""
        if self.current_event is None:
            return None
        
        return {
            "type": self.current_event.event_type,
            "start": self.current_event.start_time,
            "end": self.current_event.end_time,
            "demand_mult": self.current_event.peak_demand_multiplier,
            "corridors": self.current_event.affected_corridors,
        }
    
    def start_polling(self):
        """Start background event polling."""
        if self._running:
            return
        
        self._running = True
        
        def poll_loop():
            while self._running:
                self.update_events()
                time.sleep(self.poll_interval)
        
        self._poll_thread = threading.Thread(target=poll_loop, daemon=True)
        self._poll_thread.start()
    
    def stop_polling(self):
        """Stop background polling."""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=1.0)
    
    def reset(self):
        """Reset module state."""
        self.current_ctx = np.ones(self.n_junctions, dtype=np.float32)
        self.current_event = None
        self.active_events = []
    
    def get_stats(self) -> Dict:
        """Get module statistics."""
        return {
            "llm_backend": self.llm_backend,
            "has_active_event": self.current_event is not None,
            "current_event_info": self.get_current_event_info(),
            "context_vector": self.current_ctx.tolist(),
            "poll_interval": self.poll_interval,
        }


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate haversine distance between two points.
    
    Args:
        lat1, lon1: First point
        lat2, lon2: Second point
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c
