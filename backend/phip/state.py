"""
Protheon Core State & Event System
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Callable, List
import logging

logger = logging.getLogger("protheon.state")

@dataclass
class ProtheonState:
    connection: str = "DISCONNECTED"  # CONNECTED, DISCONNECTED, ERROR
    mode: str = "SIMULATION"          # HARDWARE, SIMULATION, REPLAY
    safety_state: str = "DISARMED"    # DISARMED, ARMED, E-STOP
    
    timestamp: int = 0
    raw_sensors: Dict[str, int] = field(default_factory=lambda: {f: 0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']})
    filtered_sensors: Dict[str, float] = field(default_factory=lambda: {f: 0.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']})
    normalized_sensors: Dict[str, float] = field(default_factory=lambda: {f: 0.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']})
    
    gesture: str = "UNKNOWN"
    gesture_confidence: float = 0.0
    
    servo_commanded: Dict[str, int] = field(default_factory=lambda: {f: 0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']})
    
    session_id: str = "DEFAULT"
    hardware_status: int = 0
    sensor_faults: int = 0


class EventBus:
    """Lightweight event system to decouple subsystems."""
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, callback: Callable):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        if callback not in self._listeners[event_name]:
            self._listeners[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable):
        if event_name in self._listeners and callback in self._listeners[event_name]:
            self._listeners[event_name].remove(callback)

    def publish(self, event_name: str, **kwargs):
        if event_name in self._listeners:
            for cb in self._listeners[event_name]:
                try:
                    cb(**kwargs)
                except Exception as e:
                    logger.error(f"Error in event {event_name} handler {cb}: {e}")

global_bus = EventBus()
global_state = ProtheonState()
