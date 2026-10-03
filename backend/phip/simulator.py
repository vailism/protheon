"""
PHIP Simulator — Virtual Arduino

Generates synthetic telemetry data so the entire UI and processing
pipeline can be tested without physical hardware connected.
"""

import threading
import time
import math
import random
import logging

logger = logging.getLogger("phip.simulator")

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']


from phip.hardware import HardwareInterface

class SimulatedArduino(HardwareInterface):
    """
    Generates realistic synthetic sensor data that mimics the Arduino
    telemetry protocol's parsed output format.
    """

    # Preset gesture patterns: finger ADC values (approximate)
    GESTURES = {
        'OPEN_HAND':  {'thumb': 320, 'index': 310, 'middle': 300, 'ring': 310, 'pinky': 320},
        'CLOSED_FIST': {'thumb': 680, 'index': 690, 'middle': 700, 'ring': 685, 'pinky': 670},
        'PINCH':       {'thumb': 670, 'index': 680, 'middle': 310, 'ring': 300, 'pinky': 310},
        'POINT':       {'thumb': 660, 'index': 310, 'middle': 680, 'ring': 690, 'pinky': 680},
        'PEACE':       {'thumb': 670, 'index': 310, 'middle': 320, 'ring': 680, 'pinky': 690},
        'THUMBS_UP':   {'thumb': 310, 'index': 690, 'middle': 680, 'ring': 690, 'pinky': 680},
    }

    def __init__(self, rate_hz=50):
        self.rate_hz = rate_hz
        self._running = False
        self._thread = None
        self._callbacks = []
        self._state_callbacks = []
        self._gesture_sequence = list(self.GESTURES.keys())
        self._current_idx = 0
        self._tick = 0
        self._servo_angles = {f: 0 for f in FINGERS}
        
        # Fault injection state
        self.active_faults = {}
        self.drop_packets = False
        self.extra_delay = 0.0

    def connect(self, port=None):
        """Simulated connect — always succeeds."""
        self._running = True
        self._thread = threading.Thread(target=self._generate_loop, daemon=True, name="sim-arduino")
        self._thread.start()
        logger.info("Simulated Arduino connected.")
        for cb in self._state_callbacks:
            cb("CONNECTED")
        return True

    def disconnect(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        for cb in self._state_callbacks:
            cb("DISCONNECTED")

    @property
    def is_connected(self):
        return self._running

    @property
    def state(self):
        return "CONNECTED" if self._running else "DISCONNECTED"

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def add_state_callback(self, callback):
        self._state_callbacks.append(callback)

    def send_command(self, cmd_type, arg1=0, arg2=0):
        """Simulated command handling."""
        if cmd_type == "SET" and 0 <= arg1 <= 4:
            finger = FINGERS[arg1]
            self._servo_angles[finger] = max(0, min(180, arg2))
        elif cmd_type == "STOP":
            self._servo_angles = {f: 0 for f in FINGERS}
        return True

    def send_stop(self):
        return self.send_command("STOP")

    def send_ping(self):
        return True

    def get_stats(self):
        return {'received': self._tick, 'dropped': 0, 'state': self.state, 'port': 'SIMULATOR'}

    @staticmethod
    def list_ports():
        return ['SIMULATOR']

    def inject_fault(self, fault_type, finger=None):
        if fault_type == "CLEAR":
            self.active_faults.clear()
            self.drop_packets = False
            self.extra_delay = 0.0
            logger.info("Cleared all simulator faults.")
        elif fault_type == "DROP":
            self.drop_packets = True
        elif fault_type == "DELAY":
            self.extra_delay = 0.1 # 100ms delay per packet
        elif finger and finger in FINGERS:
            self.active_faults[finger] = fault_type
            logger.info(f"Injected {fault_type} on {finger}")

    def _generate_loop(self):
        """Generate synthetic telemetry at the configured rate."""
        interval = 1.0 / self.rate_hz
        start = time.time()

        while self._running:
            self._tick += 1
            timestamp = int((time.time() - start) * 1000)

            # Cycle through gestures every 3 seconds
            gesture_name = self._gesture_sequence[self._current_idx]
            target = self.GESTURES[gesture_name]

            if self._tick % (self.rate_hz * 3) == 0:
                self._current_idx = (self._current_idx + 1) % len(self._gesture_sequence)

            # Add realistic noise (±5 ADC counts) and slow drift
            sensors = {}
            for f in FINGERS:
                base = target[f]
                
                # Apply Faults
                fault = self.active_faults.get(f)
                if fault == "STUCK":
                    sensors[f] = base  # No noise, no drift, just stuck at base
                elif fault == "DISCONNECT":
                    sensors[f] = 0
                elif fault == "JUMP":
                    sensors[f] = min(1023, base + 400)
                elif fault == "NOISE":
                    sensors[f] = int(max(0, min(1023, base + random.gauss(0, 50))))
                else:
                    noise = random.gauss(0, 3)
                    drift = 2 * math.sin(self._tick * 0.01)
                    sensors[f] = int(max(0, min(1023, base + noise + drift)))

            # Simulate hardware fault flags matching Arduino protocol
            faults_bitmask = 0
            for i, f in enumerate(FINGERS):
                if self.active_faults.get(f) in ["STUCK", "DISCONNECT"]:
                    faults_bitmask |= (1 << i)

            data = {
                'timestamp': timestamp,
                'sensors': sensors,
                'servos': dict(self._servo_angles),
                'status': faults_bitmask,
                'estop': False,
                'sensor_faults': faults_bitmask,
            }

            if not self.drop_packets:
                for cb in self._callbacks:
                    try:
                        cb(data)
                    except Exception as e:
                        logger.error(f"Simulator callback error: {e}")

            time.sleep(interval + self.extra_delay)
