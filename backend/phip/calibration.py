"""
PHIP Calibration Engine

Maps raw ADC values (0-1023) to normalized percentages (0.0-100.0%)
independently for each finger. Each flex sensor has different resistance
curves, so per-finger min/max calibration is essential.
"""

import json
import os
import logging

logger = logging.getLogger("phip.calibration")

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']


class CalibrationProfile:
    def __init__(self, filepath=None):
        self.filepath = filepath
        # Safe defaults — deliberately conservative range that will produce
        # approximate results before real calibration. User MUST calibrate.
        self.min_vals = {f: 300 for f in FINGERS}
        self.max_vals = {f: 700 for f in FINGERS}
        self.is_calibrated = False
        
        if filepath:
            self.load()

    def update_min(self, raw_data):
        """Set OPEN HAND calibration point."""
        for f in FINGERS:
            if f in raw_data:
                self.min_vals[f] = raw_data[f]
        logger.info(f"Min (open) calibrated: {self.min_vals}")

    def update_max(self, raw_data):
        """Set CLOSED HAND calibration point."""
        for f in FINGERS:
            if f in raw_data:
                self.max_vals[f] = raw_data[f]
        self.is_calibrated = True
        logger.info(f"Max (closed) calibrated: {self.max_vals}")

    def get_percentage(self, raw_data):
        """Convert raw ADC dict to 0-100% dict, clamped."""
        pct = {}
        for f in FINGERS:
            raw = raw_data.get(f, 0)
            lo = self.min_vals[f]
            hi = self.max_vals[f]
            span = hi - lo

            if span == 0:
                # Uncalibrated or broken sensor — return 0%, don't divide by zero
                pct[f] = 0.0
                continue

            if span < 0:
                # Inverted sensor polarity — swap and compute
                # Some flex sensors decrease ADC on bend instead of increasing
                p = ((raw - hi) / (-span)) * 100.0
            else:
                p = ((raw - lo) / span) * 100.0

            pct[f] = max(0.0, min(100.0, p))

        return pct

    def validate(self):
        """Check if calibration is sane. Returns list of warnings."""
        warnings = []
        for f in FINGERS:
            span = abs(self.max_vals[f] - self.min_vals[f])
            if span < 20:
                warnings.append(f"{f}: Very small calibration range ({span}). "
                                f"Sensor may not be connected or glove may not be on.")
            if self.min_vals[f] < 5 or self.max_vals[f] > 1020:
                warnings.append(f"{f}: Calibration values near ADC rails. "
                                f"Check wiring/voltage divider.")
        return warnings

    def save(self):
        """Persist calibration to JSON file."""
        if not self.filepath:
            logger.warning("No filepath set, cannot save calibration.")
            return

        dirpath = os.path.dirname(self.filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
            
        data = {
            'min': self.min_vals,
            'max': self.max_vals,
            'calibrated': self.is_calibrated,
        }
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Calibration saved to {self.filepath}")

    def load(self):
        """Load calibration from JSON file if it exists."""
        if not self.filepath or not os.path.exists(self.filepath):
            return

        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            self.min_vals = data.get('min', self.min_vals)
            self.max_vals = data.get('max', self.max_vals)
            self.is_calibrated = data.get('calibrated', False)
            logger.info(f"Calibration loaded from {self.filepath}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load calibration: {e}")
