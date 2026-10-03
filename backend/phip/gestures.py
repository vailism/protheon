"""
PHIP Gesture Recognition Engine

Classifies the current hand posture based on finger bend percentages.
Uses deterministic rules with hysteresis to prevent flickering between
gestures due to sensor noise.
"""

import time
import logging

logger = logging.getLogger("phip.gestures")

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']


class GestureRecognizer:
    def __init__(self, threshold_closed=65.0, threshold_open=35.0, 
                 hold_time_ms=150):
        """
        Args:
            threshold_closed: % above which a finger is considered closed/bent
            threshold_open: % below which a finger is considered open/straight
            hold_time_ms: minimum time (ms) a gesture must be stable before
                          it replaces the current gesture (prevents flickering)
        """
        self.threshold_closed = threshold_closed
        self.threshold_open = threshold_open
        self.hold_time_ms = hold_time_ms

        self.current_gesture = "UNKNOWN"
        self._candidate_gesture = "UNKNOWN"
        self._candidate_since = 0  # timestamp in ms when candidate first seen
        
        # Format: {'GESTURE_NAME': {'thumb': 'CLOSED', 'index': 'OPEN', ...}}
        self.rules = {
            'CLOSED_FIST': {f: 'CLOSED' for f in FINGERS},
            'OPEN_HAND': {f: 'OPEN' for f in FINGERS},
            'PINCH': {'thumb': 'CLOSED', 'index': 'CLOSED', 'middle': 'OPEN', 'ring': 'OPEN', 'pinky': 'OPEN'},
            'POINT': {'thumb': 'CLOSED', 'index': 'OPEN', 'middle': 'CLOSED', 'ring': 'CLOSED', 'pinky': 'CLOSED'},
            'PEACE': {'thumb': 'CLOSED', 'index': 'OPEN', 'middle': 'OPEN', 'ring': 'CLOSED', 'pinky': 'CLOSED'},
            'THUMBS_UP': {'thumb': 'OPEN', 'index': 'CLOSED', 'middle': 'CLOSED', 'ring': 'CLOSED', 'pinky': 'CLOSED'}
        }

    def add_rule(self, name, rule_dict):
        self.rules[name] = rule_dict
        logger.info(f"Added custom gesture rule: {name}")

    def recognize(self, percentages):
        """
        Classify gesture from finger bend percentages.
        Returns the stable gesture name (with hysteresis debouncing).
        """
        closed = {}
        opened = {}
        for f in FINGERS:
            val = percentages.get(f, 0.0)
            closed[f] = val > self.threshold_closed
            opened[f] = val < self.threshold_open

        raw_gesture = self._classify(closed, opened)

        # Hysteresis: only change gesture if the new one is stable for hold_time_ms
        now_ms = int(time.monotonic() * 1000)

        if raw_gesture != self._candidate_gesture:
            # New candidate — start timing
            self._candidate_gesture = raw_gesture
            self._candidate_since = now_ms

        # Check if candidate has been stable long enough to promote
        if (self._candidate_gesture != self.current_gesture and 
                now_ms - self._candidate_since >= self.hold_time_ms):
            logger.info(f"Gesture: {self.current_gesture} → {self._candidate_gesture}")
            self.current_gesture = self._candidate_gesture

        return self.current_gesture

    def _classify(self, closed, opened):
        """Rule-based classification evaluated dynamically against self.rules."""
        
        for name, rule in self.rules.items():
            match = True
            for f, required_state in rule.items():
                if required_state == 'CLOSED' and not closed[f]:
                    match = False
                    break
                elif required_state == 'OPEN' and not opened[f]:
                    match = False
                    break
            
            if match:
                return name
                
        return "TRANSITIONING"
