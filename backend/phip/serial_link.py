"""
PHIP Serial Communication Layer

Handles:
- Background threaded serial reading
- Checksum validation (XOR, masked to 8 bits)
- Structured telemetry parsing
- Command transmission with checksums
- Auto-detection of Arduino on macOS
- Connection state tracking
- Heartbeat (PING) to prevent Arduino timeout
- Reconnection on disconnect
"""

import serial
import serial.tools.list_ports
import threading
import time
import logging

logger = logging.getLogger("phip.serial")


class SerialLink:
    # Connection states
    STATE_DISCONNECTED = "DISCONNECTED"
    STATE_CONNECTED = "CONNECTED"
    STATE_ERROR = "ERROR"

    def __init__(self, port=None, baudrate=115200, ping_interval=1.0):
        self.port = port
        self.baudrate = baudrate
        self.ping_interval = ping_interval  # Seconds between heartbeat PINGs
        self._serial = None
        self._running = False
        self._thread = None
        self._ping_thread = None
        self._callbacks = []
        self._state_callbacks = []
        self._state = self.STATE_DISCONNECTED
        self._lock = threading.Lock()
        self._packets_received = 0
        self._packets_dropped = 0

    @property
    def state(self):
        return self._state

    @property
    def is_connected(self):
        return self._state == self.STATE_CONNECTED

    def connect(self, port=None):
        """Connect to the Arduino. Returns True on success."""
        if port:
            self.port = port

        if not self.port:
            self.port = self.auto_detect_port()
            if not self.port:
                logger.warning("No Arduino found on any USB serial port.")
                self._set_state(self.STATE_DISCONNECTED)
                return False

        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(2.0)  # Arduino resets on serial open — wait for bootloader
            self._serial.reset_input_buffer()
            
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True, name="serial-rx")
            self._thread.start()
            self._ping_thread = threading.Thread(target=self._ping_loop, daemon=True, name="serial-ping")
            self._ping_thread.start()
            
            logger.info(f"Connected to {self.port} at {self.baudrate} baud.")
            self._set_state(self.STATE_CONNECTED)
            return True
        except serial.SerialException as e:
            logger.error(f"Connection failed: {e}")
            self._set_state(self.STATE_ERROR)
            return False

    def disconnect(self):
        """Cleanly disconnect from Arduino."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._ping_thread:
            self._ping_thread.join(timeout=2.0)
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except Exception:
                    pass
        logger.info("Disconnected.")
        self._set_state(self.STATE_DISCONNECTED)

    def auto_detect_port(self):
        """Find Arduino Uno serial port on macOS."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = (p.device + " " + (p.description or "")).lower()
            if "usbmodem" in desc or "usbserial" in desc or "tty.usb" in desc:
                logger.info(f"Auto-detected Arduino on: {p.device}")
                return p.device
        return None

    @staticmethod
    def list_ports():
        """Return list of all available serial ports."""
        return [p.device for p in serial.tools.list_ports.comports()]

    def add_callback(self, callback):
        """Register a telemetry data callback."""
        self._callbacks.append(callback)

    def add_state_callback(self, callback):
        """Register a connection state change callback."""
        self._state_callbacks.append(callback)

    # ----------------------------------------------------------
    # SENDING
    # ----------------------------------------------------------
    def send_command(self, cmd_type, arg1=0, arg2=0):
        """Send a command to the Arduino with XOR checksum."""
        with self._lock:
            if not self._serial or not self._serial.is_open:
                return False

            payload = f"CMD|{cmd_type}|{arg1}|{arg2}|"
            chk = 0
            for c in payload:
                chk ^= ord(c)
            chk &= 0xFF  # Mask to 8 bits to match Arduino uint8_t

            packet = f"{payload}{chk}\n"
            try:
                self._serial.write(packet.encode('ascii'))
                return True
            except serial.SerialException:
                self._set_state(self.STATE_ERROR)
                return False

    def send_stop(self):
        """Emergency stop — highest priority command."""
        return self.send_command("STOP")

    def send_ping(self):
        """Heartbeat ping to keep Arduino from entering timeout safe state."""
        return self.send_command("PING")

    # ----------------------------------------------------------
    # BACKGROUND THREADS
    # ----------------------------------------------------------
    def _read_loop(self):
        """Background thread: reads serial data line by line."""
        while self._running:
            try:
                with self._lock:
                    if not self._serial or not self._serial.is_open:
                        break
                    waiting = self._serial.in_waiting

                if waiting > 0:
                    with self._lock:
                        raw = self._serial.readline()
                    line = raw.decode('ascii', errors='ignore').strip()
                    if line:
                        self._parse_line(line)
                else:
                    time.sleep(0.002)

            except serial.SerialException as e:
                logger.error(f"Serial read error: {e}")
                self._set_state(self.STATE_ERROR)
                break
            except Exception as e:
                logger.error(f"Unexpected error in read loop: {e}")
                time.sleep(0.01)

    def _ping_loop(self):
        """Background thread: sends periodic PING to prevent Arduino timeout."""
        while self._running:
            time.sleep(self.ping_interval)
            if self._running and self.is_connected:
                self.send_ping()

    # ----------------------------------------------------------
    # PARSING
    # ----------------------------------------------------------
    def _parse_line(self, line):
        """Parse a telemetry or system message from the Arduino."""
        if line.startswith("SYS|") or line.startswith("ACK|"):
            logger.info(f"Arduino: {line}")
            return

        if not line.startswith("TEL|"):
            logger.debug(f"Unknown message: {line}")
            return

        parts = line.split('|')
        # Expected: TEL|ts|t|i|m|r|p|s0|s1|s2|s3|s4|status|checksum = 14 parts
        if len(parts) != 14:
            self._packets_dropped += 1
            return

        # Validate checksum
        try:
            received_chk = int(parts[13])
        except ValueError:
            self._packets_dropped += 1
            return

        # Reconstruct payload: everything up to and including the last '|' before checksum
        payload = '|'.join(parts[:13]) + '|'
        calc_chk = 0
        for c in payload:
            calc_chk ^= ord(c)
        calc_chk &= 0xFF  # Critical: mask to 8 bits to match Arduino uint8_t

        if calc_chk != received_chk:
            self._packets_dropped += 1
            logger.debug(f"Checksum mismatch: calc={calc_chk} recv={received_chk}")
            return

        # Parse validated data
        try:
            status_val = int(parts[12])
            data = {
                'timestamp': int(parts[1]),
                'sensors': {
                    'thumb':  int(parts[2]),
                    'index':  int(parts[3]),
                    'middle': int(parts[4]),
                    'ring':   int(parts[5]),
                    'pinky':  int(parts[6]),
                },
                'servos': {
                    'thumb':  int(parts[7]),
                    'index':  int(parts[8]),
                    'middle': int(parts[9]),
                    'ring':   int(parts[10]),
                    'pinky':  int(parts[11]),
                },
                'status': status_val,
                'estop': bool(status_val & 0x80),
                'sensor_faults': status_val & 0x1F,
            }
            self._packets_received += 1

            for cb in self._callbacks:
                try:
                    cb(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        except (ValueError, IndexError) as e:
            self._packets_dropped += 1

    # ----------------------------------------------------------
    # STATE MANAGEMENT
    # ----------------------------------------------------------
    def _set_state(self, new_state):
        if new_state != self._state:
            old = self._state
            self._state = new_state
            logger.info(f"Connection state: {old} → {new_state}")
            for cb in self._state_callbacks:
                try:
                    cb(new_state)
                except Exception:
                    pass

    def get_stats(self):
        """Return packet statistics for diagnostics."""
        return {
            'received': self._packets_received,
            'dropped': self._packets_dropped,
            'state': self._state,
            'port': self.port,
        }
