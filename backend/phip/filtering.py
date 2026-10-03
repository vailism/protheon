"""
PHIP Signal Processing — Exponential Moving Average with Deadzone

Smooths the calibrated percentage values to prevent servo jitter caused
by analog sensor noise, while maintaining low latency for responsive control.
"""

import logging

logger = logging.getLogger("phip.filtering")

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']


class EMAFilter:
    """
    Exponential Moving Average filter with configurable deadzone.
    
    EMA formula: output = α * input + (1-α) * previous_output
    
    α (alpha) controls responsiveness:
        - Higher α (0.5-0.8) = faster response, less smoothing
        - Lower α (0.1-0.3) = smoother, more latency
        
    Deadzone prevents micro-changes from propagating to servos:
        - If the change is smaller than deadzone %, the output doesn't update.
        - This eliminates servo jitter from ADC noise.
    """
    
    def __init__(self, alpha=0.3, deadzone=2.0):
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"Alpha must be in (0, 1], got {alpha}")
        if deadzone < 0:
            raise ValueError(f"Deadzone must be >= 0, got {deadzone}")
            
        self.alpha = alpha
        self.deadzone = deadzone
        self._prev = {f: 0.0 for f in FINGERS}
        self._initialized = False

    def process(self, percentages):
        """
        Apply EMA + deadzone to a dict of finger percentages.
        
        Args:
            percentages: dict with keys 'thumb','index','middle','ring','pinky'
                         and float values 0.0-100.0
        Returns:
            dict with same keys and smoothed float values
        """
        if not self._initialized:
            # First sample — seed the filter with actual values
            for f in FINGERS:
                self._prev[f] = percentages.get(f, 0.0)
            self._initialized = True
            return self._prev.copy()

        output = {}
        for f in FINGERS:
            val = percentages.get(f, self._prev[f])
            
            # EMA
            smoothed = (self.alpha * val) + ((1.0 - self.alpha) * self._prev[f])
            
            # Deadzone — only update if change exceeds threshold
            if abs(smoothed - self._prev[f]) > self.deadzone:
                self._prev[f] = smoothed
                
            output[f] = self._prev[f]

        return output

    def reset(self):
        """Reset filter state (e.g., after recalibration)."""
        self._prev = {f: 0.0 for f in FINGERS}
        self._initialized = False
