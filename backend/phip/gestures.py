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
        """Pure rule-based classification — no side effects."""
        # All fingers closed → FIST
        if all(closed[f] for f in FINGERS):
            return "CLOSED_FIST"

        # All fingers open → OPEN HAND
        if all(opened[f] for f in FINGERS):
            return "OPEN_HAND"

        # Thumb & Index closed, rest open → PINCH
        if (closed['thumb'] and closed['index'] and 
            opened['middle'] and opened['ring'] and opened['pinky']):
            return "PINCH"

        # Only index extended, rest closed (including thumb) → POINT
        if (closed['thumb'] and opened['index'] and 
            closed['middle'] and closed['ring'] and closed['pinky']):
            return "POINT"

        # Thumb closed, index & middle extended, ring & pinky closed → PEACE
        if (closed['thumb'] and opened['index'] and opened['middle'] and 
            closed['ring'] and closed['pinky']):
            return "PEACE"

        # Thumb extended, all others closed → THUMBS UP
        if (opened['thumb'] and closed['index'] and 
            closed['middle'] and closed['ring'] and closed['pinky']):
            return "THUMBS_UP"

        return "TRANSITIONING"
