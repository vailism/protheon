"""
Protheon Sensor Health Engine
"""
import time
import numpy as np
import logging

logger = logging.getLogger("protheon.health")

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']

class HealthMonitor:
    def __init__(self, history_len=50):
        self.history_len = history_len
        self.history = {f: [] for f in FINGERS}
        self.last_update = {f: time.time() for f in FINGERS}
        
    def analyze(self, raw_data, timestamp_ms):
        """Analyze a frame of raw data and return a status dict."""
        status = {}
        now = time.time()
        
        for f in FINGERS:
            val = raw_data.get(f, 0)
            self.history[f].append(val)
            if len(self.history[f]) > self.history_len:
                self.history[f].pop(0)
                
            hist = self.history[f]
            
            # Default
            f_status = "OK"
            
            if len(hist) > 10:
                variance = np.var(hist)
                std_dev = np.std(hist)
                recent_diff = abs(hist[-1] - hist[-2])
                
                # Check for completely stuck sensor
                if variance < 0.1:
                    f_status = "STUCK_SENSOR"
                    
                # Check for extreme sudden jumps (physically impossible finger speeds)
                elif recent_diff > 150:
                    f_status = "SUDDEN_JUMP"
                    
                # Check for disconnected sensor (floating around 0 or 1023 repeatedly)
                elif np.mean(hist) < 5 or np.mean(hist) > 1018:
                    f_status = "DISCONNECTED"
                    
                # Check for excessive noise
                elif std_dev > 30:
                    f_status = "NOISY"
            
            status[f] = f_status
            
        return status
